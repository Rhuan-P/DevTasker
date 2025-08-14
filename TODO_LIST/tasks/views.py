from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django.db.models import Count, Q, F

from .models import Task
from .forms import TaskForm
from projects.models import Project
from core.choices import TaskStatus, TaskPriority


class TaskAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        if user != task.owner and user != task.assigned_to and user != getattr(task.project, 'owner', None):
            raise PermissionDenied("Você não tem permissão para acessar esta tarefa.")
        return super().dispatch(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Retorna as tasks atribuídas ao usuário logado (assigned_to)
        return Task.objects.filter(assigned_to=self.request.user)


class TaskStatusUpdateView(TaskAccessMixin, SingleObjectMixin, View):
    model = Task
    success_url = reverse_lazy('task-list')
    template_name = ''            # Deve ser definido nas subclasses
    target_status = None          # Deve ser definido nas subclasses
    skip_if_status_is = None      # Deve ser definido nas subclasses

    
    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if task.owner != request.user:
            raise PermissionDenied("You do not have permission to update this task.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.skip_if_status_is and self.object.status == self.skip_if_status_is:
            return redirect(self.success_url)
        return render(request, self.template_name, {'object': self.object})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status != self.target_status:
            self.object.status = self.target_status
            # Atualiza o campo completed_at conforme status
            if self.target_status == TaskStatus.COMPLETED:
                self.object.completed_at = timezone.now()
            else:
                self.object.completed_at = None
            self.object.save()
        return redirect(self.success_url)


class TaskCompleteView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_complete.html'
    target_status = TaskStatus.COMPLETED
    skip_if_status_is = TaskStatus.COMPLETED


class TaskReopenView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_reopen.html'
    target_status = TaskStatus.IN_PROGRESS
    skip_if_status_is = TaskStatus.IN_PROGRESS



class TaskCancelView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_cancel.html'
    target_status = TaskStatus.CANCELED
    skip_if_status_is = TaskStatus.CANCELED


class TaskListViewbyProject(DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'projects/project_detail.html'  # Se desejar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(project=self.object)
        return context


class AssignedTasksByProjectView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_mytasks.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        user = self.request.user
        return Task.objects.filter(project_id=project_id, assigned_to=user)


class TaskDetailView(TaskAccessMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('project-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project_id = self.kwargs.get('project_id')
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            kwargs['project'] = project
        return kwargs

    def form_valid(self, form):
        project_id = self.kwargs.get('project_id')
        if project_id:
            project = get_object_or_404(Project, pk=project_id)
            form.instance.project = project
            form.instance.owner = self.request.user
        return super().form_valid(form)


class TaskUpdateView(TaskAccessMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project  # Passa o projeto para o form
        return kwargs


class TaskDeleteView(TaskAccessMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')


# =============== MÉTRICAS =================


class TaskMetricsView(LoginRequiredMixin, View):
    """
    API JSON com métricas e listas auxiliares:
      - total_tasks
      - completed_this_month
      - overdue_tasks
      - tasks_in_risk_count, tasks_in_risk (amostra)
      - status_counts [{status,label,count},...]
      - priority_counts [{priority,label,count},...]
      - avg_completion_time_days (float) ou null
      - completed_tasks_by_date (serie)
    """
    RISK_DAYS = 3  # margem em dias para considerar "em risco"

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))

        now = timezone.now()
        today = now.date()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_tasks = tasks.count()
        completed_this_month = tasks.filter(status=TaskStatus.COMPLETED, completed_at__gte=start_of_month).count()
        overdue_tasks = tasks.filter(end_date__lt=today).exclude(status=TaskStatus.COMPLETED).count()

        # status / priority counts (com labels)
        status_counts = []
        for val, label in TaskStatus.choices:
            cnt = tasks.filter(status=val).count()
            status_counts.append({'status': val, 'label': label, 'count': cnt})

        priority_counts = []
        for val, label in TaskPriority.choices:
            cnt = tasks.filter(priority=val).count()
            priority_counts.append({'priority': val, 'label': label, 'count': cnt})

        # tarefas em risco: end_date entre hoje e hoje+RISK_DAYS (inclui hoje)
        risk_cutoff = today + timezone.timedelta(days=self.RISK_DAYS)
        tasks_in_risk_qs = tasks.filter(end_date__gte=today, end_date__lte=risk_cutoff).exclude(status=TaskStatus.COMPLETED)
        tasks_in_risk_count = tasks_in_risk_qs.count()
        tasks_in_risk_sample = []
        for t in tasks_in_risk_qs.select_related('project', 'owner', 'assigned_to')[:50]:
            tasks_in_risk_sample.append({
                'id': t.id,
                'name': t.name,
                'project': {'id': t.project_id, 'name': t.project.name if t.project else None},
                'owner': {'id': t.owner_id, 'name': getattr(t.owner, 'name', str(t.owner))},
                'assigned_to': {'id': t.assigned_to_id, 'name': getattr(t.assigned_to, 'name', None) if t.assigned_to else None},
                'end_date': t.end_date.isoformat() if t.end_date else None,
                'status': t.status,
                'status_display': t.get_status_display(),
            })

        # avg completion time (dias) — só tasks completadas que tenham start_date
        completed_qs = tasks.filter(status=TaskStatus.COMPLETED, completed_at__isnull=False, start_date__isnull=False)
        total_days = 0
        count_completed = 0
        for t in completed_qs:
            # diferença em dias entre completed_at (datetime) e start_date (date)
            delta = (t.completed_at.date() - t.start_date).days
            total_days += delta
            count_completed += 1
        avg_completion_time_days = round((total_days / count_completed), 2) if count_completed else None

        # série temporal (últimos 30 dias) — completadas por dia
        days_series = 30
        start_date = today - timezone.timedelta(days=days_series - 1)
        completed_by_date_qs = (
            tasks.filter(status=TaskStatus.COMPLETED, completed_at__date__gte=start_date)
                 .values('completed_at__date')
                 .annotate(count=Count('id'))
        )
        counts_map = {entry['completed_at__date']: entry['count'] for entry in completed_by_date_qs}
        completed_tasks_by_date = []
        for i in range(days_series):
            d = start_date + timezone.timedelta(days=i)
            completed_tasks_by_date.append({'date': d.strftime('%Y-%m-%d'), 'count': counts_map.get(d, 0)})

        data = {
            'total_tasks': total_tasks,
            'completed_this_month': completed_this_month,
            'overdue_tasks': overdue_tasks,
            'tasks_in_risk_count': tasks_in_risk_count,
            'tasks_in_risk': tasks_in_risk_sample,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'avg_completion_time_days': avg_completion_time_days,
            'completed_tasks_by_date': completed_tasks_by_date,
            'risk_days': self.RISK_DAYS,
        }
        return JsonResponse(data)


class TaskListAPIView(LoginRequiredMixin, View):
    """
    Lista de tasks em JSON para popular a tabela (limite 50).
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        qs = qs.select_related('project', 'owner', 'assigned_to')[:50]

        data = []
        for t in qs:
            data.append({
                "id": t.id,
                "name": t.name,
                "project": {"id": t.project_id, "name": t.project.name if t.project else None},
                "owner": {"id": t.owner_id, "name": getattr(t.owner, 'name', str(t.owner))},
                "assigned_to": {"id": t.assigned_to_id, "name": getattr(t.assigned_to, 'name', None) if t.assigned_to else None},
                "status": t.status,
                "status_display": t.get_status_display(),
                "priority": t.priority,
                "priority_display": t.get_priority_display(),
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "end_date": t.end_date.isoformat() if t.end_date else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            })
        return JsonResponse(data, safe=False)


class TaskMetricsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Renderiza o dashboard (server-side). Contexto contém os mesmos dados
    que a API, útil se preferir render server-side.
    """
    template_name = 'tasks/task_metrics.html'
    days_series = 30
    RISK_DAYS = 3

    def _human_name(self, user_obj):
        if not user_obj:
            return None
        return getattr(user_obj, 'name', str(user_obj))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()

        if user.is_superuser:
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))

        qs = qs.select_related('project', 'owner', 'assigned_to')

        total_tasks = qs.count()

        status_counts = []
        for val, label in TaskStatus.choices:
            status_counts.append({'status': val, 'label': label, 'count': qs.filter(status=val).count()})

        priority_counts = []
        for val, label in TaskPriority.choices:
            priority_counts.append({'priority': val, 'label': label, 'count': qs.filter(priority=val).count()})

        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = qs.filter(status=TaskStatus.COMPLETED, completed_at__gte=start_of_month).count()
        overdue_tasks = qs.filter(end_date__lt=today).exclude(status=TaskStatus.COMPLETED).count()

        # tasks in risk
        risk_cutoff = today + timezone.timedelta(days=self.RISK_DAYS)
        tasks_in_risk_qs = qs.filter(end_date__gte=today, end_date__lte=risk_cutoff).exclude(status=TaskStatus.COMPLETED)
        tasks_in_risk_count = tasks_in_risk_qs.count()
        tasks_in_risk_sample = []
        for t in tasks_in_risk_qs[:50]:
            tasks_in_risk_sample.append({
                'id': t.id,
                'name': t.name,
                'project': {'id': t.project_id, 'name': t.project.name if t.project else None},
                'assigned_to': {'id': t.assigned_to_id, 'name': self._human_name(t.assigned_to) if t.assigned_to else None},
                'end_date': t.end_date.isoformat() if t.end_date else None,
                'status': t.status,
            })

        # avg completion time (dias)
        completed_qs = qs.filter(status=TaskStatus.COMPLETED, completed_at__isnull=False, start_date__isnull=False)
        total_days = 0
        count_completed = 0
        for t in completed_qs:
            total_days += (t.completed_at.date() - t.start_date).days
            count_completed += 1
        avg_completion_time_days = round((total_days / count_completed), 2) if count_completed else None

        # completed by date series
        start_date = today - timezone.timedelta(days=self.days_series - 1)
        completed_qs_agg = qs.filter(status=TaskStatus.COMPLETED, completed_at__date__gte=start_date)\
                             .values('completed_at__date').annotate(count=Count('id')).order_by('completed_at__date')
        counts_map = {c['completed_at__date']: c['count'] for c in completed_qs_agg}
        completed_tasks_by_date = []
        for i in range(self.days_series):
            d = start_date + timezone.timedelta(days=i)
            completed_tasks_by_date.append({'date': d.strftime('%Y-%m-%d'), 'count': counts_map.get(d, 0)})

        sample_tasks = []
        for t in qs[:50]:
            sample_tasks.append({
                'id': t.id,
                'name': t.name,
                'project': {'id': t.project_id, 'name': t.project.name if t.project else None},
                'owner': {'id': t.owner_id, 'name': self._human_name(t.owner)},
                'assigned_to': {'id': t.assigned_to_id, 'name': self._human_name(t.assigned_to) if t.assigned_to else None},
                'status': t.status,
                'status_display': t.get_status_display(),
                'priority': t.priority,
                'priority_display': t.get_priority_display(),
                'start_date': t.start_date.isoformat() if t.start_date else None,
                'end_date': t.end_date.isoformat() if t.end_date else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
            })

        ctx.update({
            'total_tasks': total_tasks,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'completed_this_month': completed_this_month,
            'overdue_tasks': overdue_tasks,
            'tasks_in_risk_count': tasks_in_risk_count,
            'tasks_in_risk': tasks_in_risk_sample,
            'avg_completion_time_days': avg_completion_time_days,
            'completed_tasks_by_date': completed_tasks_by_date,
            'sample_tasks': sample_tasks,
            'days_series': self.days_series,
            'risk_days': self.RISK_DAYS,
        })
        return ctx

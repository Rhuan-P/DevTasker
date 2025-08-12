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


class TaskMetricsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))
        
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today = now.date()

        total_tasks = tasks.count()
        completed_this_month = tasks.filter(status=TaskStatus.COMPLETED, completed_at__gte=start_of_month).count()
        overdue_tasks = tasks.filter(end_date__lt=today).exclude(status=TaskStatus.COMPLETED).count()

        status_counts = []
        for status_val, label in TaskStatus.choices:
            count = tasks.filter(status=status_val).count()
            status_counts.append({'status': status_val, 'label': label, 'count': count})

        priority_counts = []
        for priority_val, label in TaskPriority.choices:
            count = tasks.filter(priority=priority_val).count()
            priority_counts.append({'priority': priority_val, 'label': label, 'count': count})

        # Série temporal: completadas últimos 30 dias
        days_series = 30
        start_date = today - timezone.timedelta(days=days_series-1)
        completed_qs = (
            tasks.filter(status=TaskStatus.COMPLETED, completed_at__date__gte=start_date)
                 .values('completed_at__date')
                 .annotate(count=Count('id'))
        )
        counts_map = {entry['completed_at__date']: entry['count'] for entry in completed_qs}
        completed_tasks_by_date = []
        for i in range(days_series):
            d = start_date + timezone.timedelta(days=i)
            completed_tasks_by_date.append({'date': d.strftime('%Y-%m-%d'), 'count': counts_map.get(d, 0)})

        data = {
            'total_tasks': total_tasks,
            'completed_this_month': completed_this_month,
            'overdue_tasks': overdue_tasks,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'completed_tasks_by_date': completed_tasks_by_date,
        }

        return JsonResponse(data)

class TaskListAPIView(LoginRequiredMixin, View):
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
    Renderiza o dashboard com métricas e dados para gráficos.
    """

    template_name = 'tasks/task_metrics.html'
    days_series = 30

    def _human_name(self, user_obj):
        if not user_obj:
            return None
        return getattr(user_obj, 'name', str(user_obj))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()

        # Query base (todas para superuser, só visíveis para outros)
        if user.is_superuser:
            qs = Task.objects.all()
        else:
            qs = Task.objects.filter(Q(owner=user) | Q(assigned_to=user))

        qs = qs.select_related('project', 'owner', 'assigned_to')

        # Total de tasks
        total_tasks = qs.count()

        # Status counts com labels legíveis
        raw_status = qs.values('status').annotate(count=Count('id'))
        status_counts = []
        for r in raw_status:
            val = r.get('status')
            try:
                label = TaskStatus(val).label
            except Exception:
                label = val
            status_counts.append({'status': val, 'label': label, 'count': r.get('count', 0)})

        # Priority counts com labels legíveis
        raw_pr = qs.values('priority').annotate(count=Count('id'))
        priority_counts = []
        for r in raw_pr:
            val = r.get('priority')
            try:
                label = TaskPriority(val).label
            except Exception:
                label = val
            priority_counts.append({'priority': val, 'label': label, 'count': r.get('count', 0)})

        # Completadas no mês atual
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = qs.filter(
            status=TaskStatus.COMPLETED,
            completed_at__gte=start_of_month
        ).count()

        # Atrasadas
        overdue_tasks = qs.filter(end_date__lt=today).exclude(status=TaskStatus.COMPLETED).count()

        # Série temporal últimas N dias (completadas por dia)
        start_date = today - timezone.timedelta(days=self.days_series - 1)
        completed_qs = qs.filter(
            status=TaskStatus.COMPLETED,
            completed_at__date__gte=start_date
        ).values('completed_at__date').annotate(count=Count('id')).order_by('completed_at__date')
        counts_map = {c['completed_at__date']: c['count'] for c in completed_qs}

        completed_tasks_by_date = []
        for i in range(self.days_series):
            d = start_date + timezone.timedelta(days=i)
            completed_tasks_by_date.append({'date': d.strftime('%Y-%m-%d'), 'count': counts_map.get(d, 0)})

        # Tarefas por projeto (nome e contagem)
        proj_qs = qs.values(project_name=F('project__name')).annotate(count=Count('id')).order_by('project_name')
        tasks_by_project = [{'project_name': p['project_name'] or '—', 'count': p['count']} for p in proj_qs]

        # Amostra para tabela (limite 50)
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
            'completed_tasks_by_date': completed_tasks_by_date,
            'tasks_by_project': tasks_by_project,
            'sample_tasks': sample_tasks,
            'days_series': self.days_series,
        })

        return ctx

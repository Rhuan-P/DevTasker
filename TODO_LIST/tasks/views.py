from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Task
from .forms import TaskForm
from projects.models import Project
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View



class TaskAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        if user != task.owner and user!= task.assigned_to and user != task.project.owner:
            raise PermissionDenied("Você não tem permissão para acessar esta tarefa.")
        return super().dispatch(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, ListView):
    
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)

from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .models import Task
from django.contrib.auth.mixins import LoginRequiredMixin
  

# View base para reutilização
class TaskStatusUpdateView(TaskAccessMixin, LoginRequiredMixin, SingleObjectMixin, View):
    model = Task
    success_url = reverse_lazy('task-list')
    template_name = ''            # definido pelas subclasses
    target_status = None          # definido pelas subclasses
    skip_if_status_is = None      # definido pelas subclasses

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.skip_if_status_is and self.object.status == self.skip_if_status_is:
            return redirect(self.success_url)
        return render(request, self.template_name, {'object': self.object})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status != self.target_status:
            self.object.status = self.target_status
            self.object.save()
        return redirect(self.success_url)



class TaskListViewbyProject(DetailView):
    model = Project
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(project=self.object)  # todas as tarefas do projeto
        return context

class AssignedTasksByProjectView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_mytasks.html'  # crie esse template
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project_id = self.kwargs.get('project_id')
        if project_id:
            project = Project.objects.get(pk=project_id)
            kwargs['project'] = project
        return kwargs

    def form_valid(self, form):
        project_id = self.kwargs.get('project_id')
        if project_id:
            project = Project.objects.get(pk=project_id)
            form.instance.project = project
            form.instance.owner = self.request.user  # <-- Aqui está certo!
        return super().form_valid(form)
    success_url = reverse_lazy('project-list')

class TaskCompleteView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_complete.html'
    target_status = 'completed'
    skip_if_status_is = 'completed'


class TaskReopenView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_reopen.html'
    target_status = 'in_progress'
    skip_if_status_is = 'in_progress'


class TaskCancelView(TaskStatusUpdateView):
    template_name = 'tasks/task_confirm_cancel.html'
    target_status = 'canceled'
    skip_if_status_is = 'canceled'

class TaskUpdateView(TaskAccessMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')
    def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            kwargs['project'] = self.object.project  # passa o projeto da tarefa para o form
            return kwargs
class TaskDeleteView(TaskAccessMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')


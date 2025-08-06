from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Task
from .forms import TaskForm
from projects.models import Project
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.core.exceptions import PermissionDenied



class TaskAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        if user != task.owner and user not in task.assigned_to:
            raise PermissionDenied("Você não tem permissão para acessar esta tarefa.")
        return super().dispatch(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, ListView):
    
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    

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
    success_url = reverse_lazy('task-list')

class TaskUpdateView(TaskAccessMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

class TaskDeleteView(TaskAccessMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')

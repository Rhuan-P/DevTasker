from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Project
from tasks.models import Task
from .forms import ProjectForm
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.core.exceptions import PermissionDenied

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(
            models.Q(owner=self.request.user) | models.Q(participants=self.request.user)
        ).distinct()
    
    

class ProjectAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if request.user != project.owner and request.user not in project.participants.all():
            raise PermissionDenied("Você não tem permissão para acessar este projeto.")
        return super().dispatch(request, *args, **kwargs)

class ProjectDetailView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        
        return Project.objects.filter(
            models.Q(owner=self.request.user) | models.Q(participants=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object é o projeto que está sendo exibido
        context['tasks'] = Task.objects.filter(project=self.object)
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project-list')
    form_class = ProjectForm
    

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(ProjectAccessMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project-list')

class ProjectDeleteView(ProjectAccessMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project-list')

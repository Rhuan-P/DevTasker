from django import forms
from .models import Task
from users.models import User
from projects.models import Project
from django.utils import timezone

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'start_date', 'end_date', 'status', 'priority', 'assigned_to']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),

            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }   

        

    def __init__(self, *args, **kwargs):
            project = kwargs.pop('project', None)  # Pega o projeto, se for passado
            super().__init__(*args, **kwargs)
            
            self.fields['start_date'].initial = timezone.now().date()  # Usa a data atual (sem a parte de horas)

            if project:
                self.fields['assigned_to'].queryset = project.participants.all()  # Filtra os participantes do projeto
            else:
                self.fields['assigned_to'].queryset = User.objects.none()  # Caso não tenha projeto, nenhum usuário será atribuído

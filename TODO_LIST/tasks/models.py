from django.db import models
from projects.models import Project
from django.conf import settings
from core.choices import TaskStatus, TaskPriority

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, 
    on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    priority = models.IntegerField(choices=TaskPriority.CHOICES, default=TaskPriority.LOW)
    status = models.CharField(max_length=20, choices=TaskStatus.CHOICES, default=TaskStatus.IN_PROGRESS)

    def __str__(self):
        return self.name

from django.db import models
from django.utils import timezone
from django.conf import settings
from core.choices import ProjectStatus
class Project(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    participants = models.ManyToManyField('users.User', related_name='participated_projects', blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=ProjectStatus, default=ProjectStatus.IN_PROGRESS)


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.participants.add(self.owner)

    def __str__(self):
        return self.name

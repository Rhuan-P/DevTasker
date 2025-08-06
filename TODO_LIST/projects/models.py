from django.db import models
from django.utils import timezone
from django.conf import settings
class Project(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    participants = models.ManyToManyField('users.User', related_name='participated_projects', blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    STATUS_CHOICES = (
        ('in_progress', 'Em andamento'),
        ('completed', 'Concluído'),
        ('canceled', 'Cancelado'),
        ('Pendent', 'Pendente'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.participants.add(self.owner)

    def __str__(self):
        return self.name

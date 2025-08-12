from django.db import models

from django.utils.translation import gettext_lazy as _

class TaskStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'Em andamento'
    COMPLETED = 'completed', 'Concluído'
    CANCELED = 'canceled', 'Cancelado'


class TaskPriority(models.TextChoices   ):
    LOW = 'LOW', 'Baixo'
    MEDIUM = 'MEDIUM', 'Medio'
    HIGH = 'HIGH', 'Alto'



class ProjectStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'Em andamento'
    COMPLETED = 'completed', 'Concluído'
    CANCELED = 'canceled', 'Cancelado'  
    PENDENT = 'pendent', 'Pendente'


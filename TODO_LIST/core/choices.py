# tasks/choices.py

from django.utils.translation import gettext_lazy as _

class TaskStatus:
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELED = 'canceled'

    CHOICES = (
        (IN_PROGRESS, _('Em andamento')),
        (COMPLETED, _('Concluído')),
        (CANCELED, _('Cancelado')),
    )

class TaskPriority:
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    CHOICES = (
        (LOW, _('Low')),
        (MEDIUM, _('Medium')),
        (HIGH, _('High')),
    )

class ProjectStatus:
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELED = 'canceled'
    PENDENT = 'pendent'

    CHOICES = (
        (IN_PROGRESS, _('Em andamento')),
        (COMPLETED, _('Concluído')),
        (CANCELED, _('Cancelado')),
        (PENDENT, _('Pendente')),
    )

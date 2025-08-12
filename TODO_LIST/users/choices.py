from django.db import models    

class Gender(models.TextChoices):
    MALE = 'M', 'Masculino'
    FEMALE = 'F', 'Feminino'
    OTHER = 'O', 'Outro'
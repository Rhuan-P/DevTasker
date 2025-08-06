from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager

class User(AbstractUser):
    username = None  # Remove o username padrão

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'     # Login pelo email
    REQUIRED_FIELDS = ['name']   # Campos obrigatórios para criação do superuser
    objects = CustomUserManager() 
    def __str__(self):
        return self.email
    
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager
from django_countries.fields import CountryField
from .choices import Gender

class User(AbstractUser):
    username = None 

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=11, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)

    gender =  models.CharField(max_length=1, choices=Gender.choices)
    country = CountryField(null=True, blank=True, default='BR')
  
   

    USERNAME_FIELD = 'email'     # Login pelo email
    REQUIRED_FIELDS = ['name']   # Campos obrigatórios para criação do superuser
    objects = CustomUserManager() 
    def __str__(self):
        return self.email
    
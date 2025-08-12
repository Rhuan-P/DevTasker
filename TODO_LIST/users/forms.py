from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('name', 'email','cpf', 'date_of_birth', 'country', 'gender')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('name', 'email')

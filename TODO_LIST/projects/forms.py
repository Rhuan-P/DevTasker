from django import forms
from .models import Project

from django import forms
from .models import Project
from users.models import User

class ProjectForm(forms.ModelForm):
   
    participants_emails = forms.CharField(
        required=False,
        label="Participantes (por e-mail)",
        help_text="Digite os e-mails separados por vírgula",
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'ex: user1@email.com, user2@email.com'})
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'status']
        widgets = {

            'description': forms.Textarea(attrs={'placeholder': 'Descrição do Projeto', 'class': 'px-4 py-2 border rounded  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'}),  
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

       
        for field in ['start_date', 'end_date']:
            if self.instance and getattr(self.instance, field):
                self.fields[field].initial = getattr(self.instance, field).strftime('%Y-%m-%d')

        
        if self.instance and self.instance.pk:
            emails = self.instance.participants.values_list('email', flat=True)
            self.fields['participants_emails'].initial = ', '.join(emails)

    def clean_participants_emails(self):
        raw = self.cleaned_data.get('participants_emails', '')
        emails = [email.strip() for email in raw.split(',') if email.strip()]
        invalid = []
        for email in emails:
            if not User.objects.filter(email=email).exists():
                invalid.append(email)
        if invalid:
            raise forms.ValidationError(f"Usuários não encontrados para os e-mails: {', '.join(invalid)}")
        return emails

    def save(self, commit=True):
        instance = super().save(commit=False)
        is_new = instance.pk is None

        if commit:
            instance.save()

            instance.participants.add(instance.owner)

            emails = self.cleaned_data.get('participants_emails', [])
            users = User.objects.filter(email__in=emails)
            instance.participants.add(*users)

        return instance

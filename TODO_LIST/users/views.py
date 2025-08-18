from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import User, Adress
from .forms import CustomUserCreationForm, CustomUserChangeForm, AdressForm
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import TemplateView

from django.http import JsonResponse

#Adress

class AdressCreateView(LoginRequiredMixin, CreateView):
    model = Adress
    form_class = AdressForm
    template_name = 'Adress/adress_form.html '
    success_url = reverse_lazy('task-metrics-dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# Only Superuser can list users
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_superuser

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('format') == 'json':
            users = context['users']
            users_list = []
            for user in users:
                users_list.append({
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'country': str(user.country),
                    'gender': user.gender,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,

                })
            return JsonResponse(users_list, safe=False)
        else:
            return super().render_to_response(context, **response_kwargs)

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'  # evita conflito com user logado

class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('adress-create')

               
class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('profile')
    def test_func(self):
        user_to_be_updated = self.get_object()
        return self.request.user.is_staff or user_to_be_updated == self.request.user        
class UserDeleteView(DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user-list')

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
    sucess_url = reverse_lazy('profile')

class UserPasswordChangeView(UserPassesTestMixin, PasswordChangeView):
    template_name = 'users/user_change_password.html'
    success_url = reverse_lazy('user-profile')

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.get_object()
        return kwargs

    def test_func(self):
        # Somente staff/admin pode alterar a senha de outro usu rio
        return self.request.user.is_staff



#Views de Metricas

from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils import timezone
from datetime import date

from .models import User

class UserMetricsAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    API JSON com métricas gerais de usuários:
    - total_users
    - users_by_country [{country, count}]
    - users_by_gender [{gender, count}]
    - new_users_last_month
    - users_staff_count
    - avg_age (em anos)
    """
    def test_func(self):
        return self.request.user.is_staff  # só staff acessa

    def get(self, request, *args, **kwargs):
        users = User.objects.all()

        total_users = users.count()

        # Por país (exemplo simples com annotate)
        from django.db.models import Count
        users_by_country_qs = users.values('country').annotate(count=Count('id')).order_by('-count')
        users_by_country = [{'country': c['country'], 'count': c['count']} for c in users_by_country_qs]

        # Por gênero
        users_by_gender_qs = users.values('gender').annotate(count=Count('id')).order_by('-count')
        users_by_gender = [{'gender': g['gender'], 'count': g['count']} for g in users_by_gender_qs]

        # Novos usuários no último mês
        today = timezone.now().date()
        last_month_start = today.replace(day=1) - timezone.timedelta(days=30)
        new_users_last_month = users.filter(date_joined__gte=last_month_start).count()

        # Staff x normal
        staff_count = users.filter(is_staff=True).count()

        # Média de idade
        # Para isso, precisamos calcular idade pela data de nascimento
        ages = []
        for u in users.exclude(date_of_birth=None):
            born = u.date_of_birth
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            ages.append(age)
        avg_age = round(sum(ages)/len(ages), 2) if ages else None

        data = {
            'total_users': total_users,
            'users_by_country': users_by_country,
            'users_by_gender': users_by_gender,
            'new_users_last_month': new_users_last_month,
            'staff_count': staff_count,
            'avg_age': avg_age,
        }
        return JsonResponse(data)

class UserMetricsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/user_metrics.html'

    def test_func(self):
        return self.request.user.is_staff  # só staff vê dashboard geral

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Você pode passar dados direto aqui ou usar JS para consumir API
        return ctx


class UserPersonalMetricsAPIView(LoginRequiredMixin, View):
    """
    API que retorna métricas pessoais do usuário logado, ex:
    - idade
    - status ativo
    - data de criação
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # calcular idade, se existir data de nascimento
        if user.date_of_birth:
            age = today.year - user.date_of_birth.year - (
                (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
            )
        else:
            age = None

        data = {
            'name': user.name,
            'email': user.email,
            'country': user.country.name if user.country else None,
            'gender': user.get_gender_display(),
            'age': age,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime("%Y-%m-%d"),
            # você pode adicionar mais métricas pessoais aqui
        }
        return JsonResponse(data)
from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    UserListView,
    UserDetailView,
    UserCreateView,
    AdressCreateView,
    UserUpdateView,
    UserDeleteView,
    UserPasswordChangeView,
    UserProfileView,
    UserMetricsAPIView,
    UserMetricsDashboardView,
    TemplateView,
    UserPersonalMetricsAPIView
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('new/', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user-edit'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),

    path('<int:pk>/password/', UserPasswordChangeView.as_view(), name='user-password-change'),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/users/login/'), name='logout'),

    #Adress
    path('adress/new/', AdressCreateView.as_view(), name='adress-create'),


    path('profile/', UserProfileView.as_view(), name='profile'),

    # URLs para métricas:
    path('metrics/', UserMetricsDashboardView.as_view(), name='user-metrics-admin'),          # Dashboard admin (view template)
    path('metrics/api/', UserMetricsAPIView.as_view(), name='user-metrics-api'),               # API JSON para métricas

    path('profile/metrics/', TemplateView.as_view(template_name='users/user_profile_metrics.html'), name='user-profile-metrics'),  # Métricas pessoais (template simples)
    path('api/user/personal-metrics/', UserPersonalMetricsAPIView.as_view(), name='user-personal-metrics-api'),
]

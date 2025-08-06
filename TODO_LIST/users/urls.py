
from django.urls import path
from django.contrib.auth import views as auth_views


from .views import (
    UserListView,
    UserDetailView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    UserPasswordChangeView,
    UserProfileView,
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user-edit'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),

    # Rota para alterar senha (Fazer integraçao depois)
    path('<int:pk>/password/', UserPasswordChangeView.as_view(), name='user-password-change'),

     path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/users/login/'), name='logout'),

    path('profile/', UserProfileView.as_view(), name='profile'),
]



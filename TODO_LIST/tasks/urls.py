from django.urls import path
from .views import (
    TaskListView, TaskDetailView, TaskCreateView, TaskUpdateView, TaskDeleteView,
    AssignedTasksByProjectView, TaskCompleteView, TaskReopenView, TaskCancelView,
    TaskListViewbyProject, TaskMetricsView, TaskListAPIView, TaskMetricsDashboardView
)

urlpatterns = [
    # Listagem geral de tasks do usuário
    path('', TaskListView.as_view(), name='task-list'),

    # CRUD básico
    path('create/<int:project_id>/', TaskCreateView.as_view(), name='task-create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),

    # Atualização de status (comandos específicos)
    path('<int:pk>/complete/', TaskCompleteView.as_view(), name='task-complete'),
    path('<int:pk>/reopen/', TaskReopenView.as_view(), name='task-reopen'),
    path('<int:pk>/cancel/', TaskCancelView.as_view(), name='task-cancel'),

    # Listagem de tasks por projeto
    path('project/<int:project_id>/tasks/', TaskListViewbyProject.as_view(), name='task-list-by-project'),
    path('project/<int:project_id>/my-tasks/', AssignedTasksByProjectView.as_view(), name='my-tasks'),

    # Métricas das tasks para dashboards
      path('api/list/', TaskListAPIView.as_view(), name='task-list-api'),
    path('metrics/', TaskMetricsView.as_view(), name='task-metrics'),
    path('metrics/dashboard/', TaskMetricsDashboardView.as_view(), name='task-metrics-dashboard')


]

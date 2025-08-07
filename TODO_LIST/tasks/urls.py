from django.urls import path
from . import views
from.models import Task
from .views import TaskListView, TaskDetailView, TaskCreateView, TaskUpdateView, TaskDeleteView, AssignedTasksByProjectView, TaskCompleteView, TaskReopenView, TaskCancelView   

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('create/<int:project_id>/', TaskCreateView.as_view(), name='task-create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/complete/', TaskCompleteView.as_view(), name='task-complete'),
    path('tasks/<int:pk>/reopen/', TaskReopenView.as_view(), name='task-reopen'),
    path('tasks/<int:pk>/cancel/', TaskCancelView.as_view(), name='task-cancel'),   
    path('<int:pk>/update/', TaskUpdateView.as_view(), name='task-update'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('project/<int:project_id>/my-tasks/', AssignedTasksByProjectView.as_view(), name='my-tasks'),
    path('project/<int:project_id>/tasks/', views.TaskListViewbyProject.as_view(), name='task-list-by-project'),  

]
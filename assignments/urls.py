from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('create/<int:course_id>/', views.create_assignment, name='create_assignment'),
    path('<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),
    path('<int:pk>/delete/', views.delete_assignment, name='delete_assignment'),
    path('<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('submission/<int:pk>/grade/', views.grade_submission, name='grade_submission'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('pending-submissions/', views.pending_submissions, name='pending_submissions'),
]
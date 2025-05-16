from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('create/', views.create_course, name='create_course'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/drop/', views.drop_course, name='drop_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('teaching/', views.teaching_courses, name='teaching_courses'),
]
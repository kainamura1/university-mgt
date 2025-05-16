from django.urls import path
from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.school_list, name='school_list'),
    path('<int:pk>/', views.school_detail, name='school_detail'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
]
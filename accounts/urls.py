from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='accounts/logout.html',
        next_page='accounts:login'
    ), name='logout'),
    path('register/', views.register, name='register'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    # Dashboard URLs
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
]
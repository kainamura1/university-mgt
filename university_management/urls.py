"""
URL configuration for university_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from core.views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('schools/', include('schools.urls')),
    path('courses/', include('courses.urls')),
    path('assignments/', include('assignments.urls')),
]

# Add favicon url pattern
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from django.contrib import admin
from .models import School, Department

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school', 'created_at', 'updated_at')
    list_filter = ('school',)
    search_fields = ('name', 'code', 'school__name')
    ordering = ('school', 'name')

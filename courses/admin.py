from django.contrib import admin
from django.db.models import Count
from .models import Course, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'lecturer', 'student_count', 'is_active')
    list_filter = ('department', 'is_active', 'created_at')
    search_fields = ('code', 'name', 'lecturer__username', 'department__name')
    ordering = ('department', 'code')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(student_count=Count('enrollments'))
    
    def student_count(self, obj):
        return obj.student_count
    student_count.admin_order_field = 'student_count'
    student_count.short_description = 'Enrolled Students'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new course
            obj.lecturer = request.user  # Set current user as lecturer
        super().save_model(request, obj, form, change)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at')
    list_filter = ('status', 'enrolled_at', 'course__department')
    search_fields = ('student__username', 'course__code', 'course__name')
    ordering = ('-enrolled_at',)
    
    def has_add_permission(self, request):
        # Only allow adding enrollments through the course interface
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Lecturers can only see enrollments for their courses
            if request.user.is_lecturer():
                return qs.filter(course__lecturer=request.user)
            # Students can only see their own enrollments
            elif request.user.is_student():
                return qs.filter(student=request.user)
        return qs

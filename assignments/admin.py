from django.contrib import admin
from .models import Assignment, Submission

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'total_marks', 'submission_count')
    list_filter = ('course__department', 'due_date', 'course')
    search_fields = ('title', 'course__code', 'course__name')
    date_hierarchy = 'due_date'
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if request.user.is_lecturer():
                return qs.filter(course__lecturer=request.user)
        return qs

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submitted_at', 'marks', 'is_late')
    list_filter = (
        'submitted_at',
        'assignment__course',
        ('marks', admin.EmptyFieldListFilter),  # Use EmptyFieldListFilter for nullable fields
    )
    search_fields = ('student__username', 'assignment__title', 'assignment__course__code')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at', 'is_late')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            if request.user.is_lecturer():
                return qs.filter(assignment__course__lecturer=request.user)
            elif request.user.is_student():
                return qs.filter(student=request.user)
        return qs

    def has_add_permission(self, request):
        # Only allow adding submissions through the website interface
        return False

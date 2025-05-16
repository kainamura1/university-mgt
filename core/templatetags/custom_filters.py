from django import template
from django.db.models import QuerySet

register = template.Library()

@register.filter
def calculate_percentage(value, total):
    """Calculate percentage of value against total"""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def graded_count(submissions):
    """Count number of graded submissions"""
    if isinstance(submissions, QuerySet):
        return submissions.exclude(marks__isnull=True).count()
    return sum(1 for sub in submissions if sub.marks is not None)

@register.filter
def average_score(submissions):
    """Calculate average score percentage across all graded submissions"""
    if not submissions:
        return None
    
    graded = [sub for sub in submissions if sub.marks is not None]
    if not graded:
        return None
    
    percentages = [
        (sub.marks / sub.assignment.total_marks) * 100 
        for sub in graded
    ]
    return sum(percentages) / len(percentages)
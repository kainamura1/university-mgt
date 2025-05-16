from django.db import models

class School(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    description = models.TextField(blank=True)
    required_courses = models.ManyToManyField('courses.Course', related_name='required_by_departments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.school.name}"

    class Meta:
        ordering = ['school__name', 'name']
        unique_together = ['school', 'code']  # Ensure unique department codes within each school

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    registration_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    staff_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.ForeignKey('schools.Department', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def is_student(self):
        return self.user_type == 'student'

    def is_lecturer(self):
        return self.user_type == 'lecturer'

    def get_enrolled_courses(self):
        if self.is_student():
            return [enrollment.course for enrollment in self.enrollments.all()]
        return []

    def get_teaching_courses(self):
        if self.is_lecturer():
            return self.courses_teaching.all()
        return []

    def clean(self):
        super().clean()
        if self.is_student():
            self.staff_number = None
        elif self.is_lecturer():
            self.registration_number = None

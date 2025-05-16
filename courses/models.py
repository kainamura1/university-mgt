from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        'schools.Department',
        on_delete=models.CASCADE,
        related_name='courses'
    )
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Changed from CASCADE to SET_NULL
        related_name='courses_teaching',
        limit_choices_to={'user_type': 'lecturer'},
        null=True  # Allow null for existing records
    )
    description = models.TextField(blank=True)
    credits = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        default=3  # Default number of credits
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'code']
        unique_together = ['department', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # Convert course code to uppercase
        self.code = self.code.upper()
        
        # If this is a new course, we'll need to handle auto-enrollment after saving
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Auto-enroll department students for new courses
        if is_new:
            self.auto_enroll_department_students()

    def auto_enroll_department_students(self):
        """
        Automatically enroll all students from the course's department.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all students from the department
        department_students = User.objects.filter(
            department=self.department,
            user_type='student'
        )
        
        # Create enrollments
        enrollments = []
        for student in department_students:
            enrollments.append(
                Enrollment(
                    student=student,
                    course=self,
                    status='enrolled'
                )
            )
        
        # Bulk create the enrollments
        if enrollments:
            Enrollment.objects.bulk_create(enrollments)

    def get_enrolled_students(self):
        """
        Get all students enrolled in this course.
        """
        return self.enrollments.select_related('student')

    def get_student_count(self):
        """
        Get the number of enrolled students.
        """
        return self.enrollments.count()

    def get_assignment_count(self):
        """
        Get the number of assignments for this course.
        """
        return self.assignments.count()

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'user_type': 'student'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='enrolled'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} - {self.course.code} ({self.get_status_display()})"

    def get_progress(self):
        """
        Calculate student's progress in the course based on assignments.
        Returns a dictionary with:
        - completed_assignments: number of assignments submitted
        - total_assignments: total number of assignments
        - progress_percentage: percentage of completed assignments
        """
        total_assignments = self.course.assignments.count()
        completed_assignments = self.student.submissions.filter(
            assignment__course=self.course
        ).count()
        
        progress = {
            'completed_assignments': completed_assignments,
            'total_assignments': total_assignments,
            'progress_percentage': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        }
        
        return progress

    def get_average_score(self):
        """
        Calculate the student's average score for graded assignments in this course.
        """
        from django.db.models import Avg
        
        avg_score = self.student.submissions.filter(
            assignment__course=self.course,
            marks__isnull=False
        ).aggregate(avg=Avg('marks'))['avg']
        
        return round(avg_score, 2) if avg_score is not None else None

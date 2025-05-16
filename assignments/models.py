from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

def submission_file_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/submissions/student_id/assignment_id/filename
    return f'submissions/{instance.student.id}/{instance.assignment.id}/{filename}'

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    description = models.TextField()
    due_date = models.DateTimeField()
    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_assignments'
    )

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.course.code}"

    def is_past_due(self):
        return timezone.now() > self.due_date

    def get_completion_rate(self):
        total_students = self.course.enrollments.count()
        if total_students == 0:
            return 0
        submissions_count = self.submissions.count()
        return (submissions_count / total_students) * 100

    def get_average_score(self):
        graded_submissions = self.submissions.filter(marks__isnull=False)
        if not graded_submissions.exists():
            return None
        total_marks = sum(sub.marks for sub in graded_submissions)
        return total_marks / graded_submissions.count()

class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'user_type': 'student'}
    )
    content = models.TextField(
        help_text="Your response to the assignment",
        blank=True
    )
    file = models.FileField(
        upload_to=submission_file_path,
        null=True,
        blank=True,
        help_text="Upload your assignment file (PDF format only)",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
        limit_choices_to={'user_type': 'lecturer'}
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

    def save(self, *args, **kwargs):
        if self.marks is not None and not self.graded_at:
            self.graded_at = timezone.now()
        super().save(*args, **kwargs)

    def is_late(self):
        return self.submitted_at > self.assignment.due_date

    def get_status(self):
        if self.marks is not None:
            return 'graded'
        return 'submitted'

    def get_file_extension(self):
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return None

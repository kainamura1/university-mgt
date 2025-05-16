from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.urls import reverse
from .forms import UserRegistrationForm, CustomAuthenticationForm, ProfileEditForm
from courses.models import Course, Enrollment
from assignments.models import Assignment, Submission

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        if self.request.user.is_student():
            return reverse('accounts:student_dashboard')
        else:
            return reverse('accounts:lecturer_dashboard')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def student_dashboard(request):
    if not request.user.is_student():
        messages.error(request, 'Access denied. Students only.')
        return redirect('home')
    
    # Get student's enrollments with course data
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related(
        'course',
        'course__lecturer',
        'course__department'
    )
    
    # Get all assignments from enrolled courses
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    all_assignments = Assignment.objects.filter(course_id__in=enrolled_course_ids)
    total_assignments = all_assignments.count()
    
    # Get completed assignments (with submissions)
    submitted_assignment_ids = request.user.submissions.values_list('assignment_id', flat=True)
    completed_assignments = len(submitted_assignment_ids)
    
    # Get pending (unsubmitted and not past due) assignments
    pending_assignments_list = Assignment.objects.filter(
        course_id__in=enrolled_course_ids,
        due_date__gt=timezone.now()
    ).exclude(
        id__in=submitted_assignment_ids
    ).select_related(
        'course'
    ).order_by('due_date')
    
    # Calculate course progress and averages
    for enrollment in enrollments:
        # Get all assignments for this course
        course_assignments = all_assignments.filter(course=enrollment.course)
        total = course_assignments.count()
        completed = request.user.submissions.filter(
            assignment__course=enrollment.course
        ).count()
        
        # Calculate average score for graded assignments
        avg_score = request.user.submissions.filter(
            assignment__course=enrollment.course,
            marks__isnull=False
        ).aggregate(avg=Avg('marks'))['avg']
        
        # Attach data to enrollment object
        enrollment.total_assignments = total
        enrollment.completed_assignments = completed
        enrollment.progress_percentage = (completed / total * 100) if total > 0 else 0
        enrollment.average_score = round(avg_score, 1) if avg_score else None
    
    context = {
        'enrollments': enrollments,
        'total_assignments': total_assignments,
        'completed_assignments': completed_assignments,
        'pending_assignments': total_assignments - completed_assignments,
        'pending_assignments_list': pending_assignments_list
    }
    
    return render(request, 'accounts/student_dashboard.html', context)

@login_required
def lecturer_dashboard(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Access denied. Lecturers only.')
        return redirect('home')
    
    # Get all courses taught by the lecturer with submission stats
    courses = Course.objects.filter(
        lecturer=request.user
    ).annotate(
        student_count=Count('enrollments', distinct=True),
        assignment_count=Count('assignments', distinct=True),
        submission_count=Count('assignments__submissions', distinct=True),
        ungraded_count=Count(
            'assignments__submissions',
            filter=Q(assignments__submissions__marks__isnull=True),
            distinct=True
        )
    )
    
    # Get all submissions for the lecturer's courses, ordered by submission date
    recent_submissions = Submission.objects.filter(
        assignment__course__lecturer=request.user
    ).select_related(
        'student',
        'assignment',
        'assignment__course'
    ).order_by(
        '-submitted_at'
    )[:10]
    
    # Calculate overall statistics
    total_students = sum(course.student_count for course in courses)
    total_assignments = sum(course.assignment_count for course in courses)
    total_submissions = sum(course.submission_count for course in courses)
    pending_submissions = sum(course.ungraded_count for course in courses)
    
    context = {
        'courses': courses,
        'recent_submissions': recent_submissions,
        'stats': {
            'total_students': total_students,
            'total_assignments': total_assignments,
            'total_submissions': total_submissions,
            'pending_submissions': pending_submissions
        }
    }
    
    return render(request, 'accounts/lecturer_dashboard.html', context)

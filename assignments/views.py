from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Assignment, Submission
from .forms import AssignmentForm, SubmissionForm, GradingForm
from courses.models import Course

@login_required
def assignment_list(request):
    if request.user.is_student():
        assignments = Assignment.objects.filter(
            course__enrollments__student=request.user
        ).select_related('course', 'course__lecturer')
        
        # Add submission status to each assignment
        for assignment in assignments:
            assignment.has_submitted = Submission.objects.filter(
                assignment=assignment,
                student=request.user
            ).exists()
            
    else:
        assignments = Assignment.objects.filter(
            course__lecturer=request.user
        ).select_related('course')
    
    return render(request, 'assignments/assignment_list.html', {
        'assignments': assignments
    })

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(
        Assignment.objects.select_related('course', 'course__lecturer'),
        pk=pk
    )
    context = {
        'assignment': assignment,
        'is_lecturer': request.user == assignment.course.lecturer,
        'submission': None,
        'can_submit': not assignment.is_past_due()
    }
    
    if request.user.is_student():
        try:
            context['submission'] = assignment.submissions.get(student=request.user)
            context['can_view'] = True  # Student can view their own submission
        except Submission.DoesNotExist:
            context['can_view'] = False  # Student cannot view if they haven't submitted
    else:
        context['can_view'] = True  # Lecturers can view all submissions
    
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, pk=course_id, lecturer=request.user)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, 'Assignment created successfully.')
            return redirect('assignments:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm()
    
    return render(request, 'assignments/assignment_form.html', {
        'form': form,
        'course': course
    })

@login_required
def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, course__lecturer=request.user)
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully.')
            return redirect('assignments:assignment_detail', pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'assignments/assignment_form.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, course__lecturer=request.user)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully.')
        return redirect('courses:course_detail', pk=assignment.course.pk)
    
    return render(request, 'assignments/assignment_confirm_delete.html', {
        'assignment': assignment
    })

@login_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    # Check if student is enrolled in the course
    if not assignment.course.enrollments.filter(student=request.user).exists():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('assignments:assignment_list')
    
    # Check if student has already submitted
    if Submission.objects.filter(assignment=assignment, student=request.user).exists():
        messages.error(request, 'You have already submitted this assignment.')
        return redirect('assignments:assignment_detail', pk=pk)
    
    if assignment.is_past_due():
        messages.error(request, 'This assignment is past its due date.')
        return redirect('assignments:assignment_detail', pk=pk)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            messages.success(request, 'Assignment submitted successfully.')
            return redirect('assignments:assignment_detail', pk=pk)
    else:
        form = SubmissionForm()
    
    return render(request, 'assignments/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('assignment', 'student', 'assignment__course'),
        pk=pk
    )
    
    # Check permissions
    if not (request.user == submission.student or 
            request.user == submission.assignment.course.lecturer):
        messages.error(request, 'You do not have permission to view this submission.')
        return redirect('assignments:assignment_list')
    
    return render(request, 'assignments/submission_detail.html', {
        'submission': submission
    })

@login_required
def grade_submission(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('assignment', 'student', 'assignment__course'),
        pk=pk
    )
    
    if request.user != submission.assignment.course.lecturer:
        messages.error(request, 'You do not have permission to grade this submission.')
        return redirect('assignments:submission_detail', pk=pk)
    
    if request.method == 'POST':
        form = GradingForm(submission.assignment, request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.graded_by = request.user
            submission.graded_at = timezone.now()
            submission.save()
            messages.success(request, 'Submission graded successfully.')
            return redirect('assignments:submission_detail', pk=pk)
    else:
        form = GradingForm(submission.assignment, instance=submission)
    
    return render(request, 'assignments/grade_submission.html', {
        'form': form,
        'submission': submission
    })

@login_required
def my_submissions(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view their submissions.')
        return redirect('home')
    
    submissions = request.user.submissions.select_related(
        'assignment',
        'assignment__course'
    ).order_by('-submitted_at')
    
    return render(request, 'assignments/my_submissions.html', {
        'submissions': submissions
    })

@login_required
def pending_submissions(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Only lecturers can view pending submissions.')
        return redirect('home')
    
    submissions = Submission.objects.filter(
        assignment__course__lecturer=request.user,
        marks__isnull=True
    ).select_related(
        'assignment',
        'student',
        'assignment__course'
    ).order_by('submitted_at')
    
    return render(request, 'assignments/pending_submissions.html', {
        'submissions': submissions
    })

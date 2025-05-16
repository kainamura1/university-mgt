from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Course, Enrollment
from .forms import CourseForm

@login_required
def course_list(request):
    if request.user.is_student():
        # Show all courses from student's department
        courses = Course.objects.filter(
            department=request.user.department,
            is_active=True
        ).select_related('department', 'lecturer')
        
        # Get the IDs of courses the student is already enrolled in
        enrolled_course_ids = Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)
        
        # Mark courses as enrolled or not
        for course in courses:
            course.is_enrolled = course.id in enrolled_course_ids
    else:
        courses = Course.objects.filter(is_active=True).select_related('department', 'lecturer')
    
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('department', 'lecturer'),
        pk=pk
    )
    
    context = {
        'course': course,
        'is_enrolled': False,
        'enrollment_count': course.enrollments.count(),
        'assignment_count': course.assignments.count(),
    }
    
    if request.user.is_student():
        context['is_enrolled'] = course.enrollments.filter(student=request.user).exists()
        if context['is_enrolled']:
            enrollment = course.enrollments.get(student=request.user)
            context['enrollment'] = enrollment
    
    return render(request, 'courses/course_detail.html', context)

@login_required
def create_course(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Only lecturers can create courses.')
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.lecturer = request.user
            course.save()
            messages.success(request, 'Course created successfully.')
            
            # Automatically enroll all students from the department
            department_students = course.department.user_set.filter(user_type='student')
            enrolled_count = 0
            
            for student in department_students:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={'status': 'enrolled'}
                )
                if created:
                    enrolled_count += 1
            
            if enrolled_count > 0:
                messages.info(request, f'Automatically enrolled {enrolled_count} students from {course.department}')
            
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_form.html', {'form': form})

@login_required
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user != course.lecturer:
        messages.error(request, 'You can only edit your own courses.')
        return redirect('courses:course_detail', pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'course': course
    })

@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user != course.lecturer:
        messages.error(request, 'You can only delete your own courses.')
        return redirect('courses:course_detail', pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('courses:teaching_courses')
    
    return render(request, 'courses/course_confirm_delete.html', {'course': course})

@login_required
def enroll_course(request, course_id):
    if not request.user.is_student():
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('courses:course_list')
    
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    
    # Check if the course is from student's department
    if course.department != request.user.department:
        messages.error(request, 'You can only enroll in courses from your department.')
        return redirect('courses:course_list')
    
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': 'enrolled'}
    )
    
    if created:
        messages.success(request, f'Successfully enrolled in {course.name}.')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    
    return redirect('courses:course_detail', pk=course_id)

@login_required
def drop_course(request, course_id):
    if not request.user.is_student():
        messages.error(request, 'Only students can drop courses.')
        return redirect('courses:course_list')
    
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course_id=course_id
    )
    
    # Don't allow dropping required courses
    if enrollment.course in request.user.department.required_courses.all():
        messages.error(request, 'You cannot drop required courses for your department.')
        return redirect('courses:course_detail', pk=course_id)
    
    enrollment.delete()
    messages.success(request, f'Successfully dropped {enrollment.course.name}.')
    
    return redirect('courses:my_courses')

@login_required
def my_courses(request):
    if not request.user.is_student():
        messages.error(request, 'Only students can view their courses.')
        return redirect('courses:course_list')
    
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related(
        'course',
        'course__lecturer',
        'course__department'
    )
    
    # Get available courses from student's department that they're not enrolled in
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    available_courses = Course.objects.filter(
        department=request.user.department,
        is_active=True
    ).exclude(
        id__in=enrolled_course_ids
    ).select_related('lecturer', 'department')
    
    context = {
        'enrollments': enrollments,
        'available_courses': available_courses
    }
    
    return render(request, 'courses/my_courses.html', context)

@login_required
def teaching_courses(request):
    if not request.user.is_lecturer():
        messages.error(request, 'Only lecturers can view their teaching courses.')
        return redirect('courses:course_list')
    
    courses = Course.objects.filter(
        lecturer=request.user
    ).select_related('department').annotate(
        student_count=Count('enrollments'),
        assignment_count=Count('assignments')
    )
    
    return render(request, 'courses/teaching_courses.html', {'courses': courses})

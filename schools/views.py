from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import School, Department

@login_required
def school_list(request):
    schools = School.objects.all()
    return render(request, 'schools/school_list.html', {'schools': schools})

@login_required
def school_detail(request, pk):
    school = get_object_or_404(School, pk=pk)
    departments = school.departments.all()
    return render(request, 'schools/school_detail.html', {
        'school': school,
        'departments': departments
    })

@login_required
def department_list(request):
    departments = Department.objects.select_related('school')
    return render(request, 'schools/department_list.html', {'departments': departments})

@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department.objects.select_related('school'), pk=pk)
    courses = department.courses.all()
    return render(request, 'schools/department_detail.html', {
        'department': department,
        'courses': courses
    })

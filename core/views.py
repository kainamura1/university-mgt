from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """
    Redirect users to their appropriate dashboard based on their user type
    """
    if request.user.is_student():
        return redirect('accounts:student_dashboard')
    else:
        return redirect('accounts:lecturer_dashboard')

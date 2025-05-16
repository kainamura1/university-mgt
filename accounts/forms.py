from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User
from schools.models import Department

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    registration_number = forms.CharField(required=False)
    staff_number = forms.CharField(required=False)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="Select your department",
        widget=forms.Select(attrs={'class': 'form-select'}),
        to_field_name="id"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'user_type', 'department', 'registration_number',
            'staff_number', 'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields:
            if not isinstance(self.fields[field].widget, (forms.Select, forms.CheckboxInput)):
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Update department choices to show school information
        self.fields['department'].queryset = Department.objects.select_related('school')
        self.fields['user_type'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        registration_number = cleaned_data.get('registration_number')
        staff_number = cleaned_data.get('staff_number')

        if user_type == 'student':
            if not registration_number:
                self.add_error('registration_number', 'Registration number is required for students')
            # Clear staff number for students
            cleaned_data['staff_number'] = None
        
        elif user_type == 'lecturer':
            if not staff_number:
                self.add_error('staff_number', 'Staff number is required for lecturers')
            # Clear registration number for lecturers
            cleaned_data['registration_number'] = None

        # Check for duplicate numbers
        if registration_number and User.objects.filter(registration_number=registration_number).exists():
            self.add_error('registration_number', 'This registration number is already in use')
        
        if staff_number and User.objects.filter(staff_number=staff_number).exists():
            self.add_error('staff_number', 'This staff number is already in use')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.department = self.cleaned_data['department']
        
        # Set appropriate number based on user type
        if user.is_student():
            user.registration_number = self.cleaned_data['registration_number']
            user.staff_number = None
        else:
            user.staff_number = self.cleaned_data['staff_number']
            user.registration_number = None
        
        if commit:
            user.save()
            # If user is a student and department has required courses, enroll them
            if user.is_student() and user.department:
                from courses.models import Enrollment
                required_courses = user.department.required_courses.all()
                for course in required_courses:
                    Enrollment.objects.create(
                        student=user,
                        course=course,
                        status='enrolled'
                    )
        return user

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        if User.is_student:
            fields.append('registration_number')
        if User.is_lecturer:
            fields.append('staff_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('Email address is already in use.')
        return email
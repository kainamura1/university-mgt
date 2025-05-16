from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'department', 'description', 'credits', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Make department select widget use a custom class
        self.fields['department'].widget.attrs.update({'class': 'form-select'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        
        # Custom help texts
        self.fields['code'].help_text = 'Enter a unique course code (e.g., CS101)'
        self.fields['credits'].help_text = 'Number of credit hours for this course'
        self.fields['is_active'].help_text = 'Inactive courses will not be visible to students'

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            # Convert to uppercase
            code = code.upper()
            # Check if code exists, excluding current instance
            if Course.objects.filter(code=code).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError('This course code is already in use.')
        return code

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        
        # If editing an existing course, check if it has enrollments before changing department
        if self.instance.pk and 'department' in self.changed_data:
            if self.instance.enrollments.exists():
                raise forms.ValidationError(
                    "Cannot change department of a course that has enrolled students."
                )
        
        return cleaned_data
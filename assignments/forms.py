from django import forms
from django.core.exceptions import ValidationError
from .models import Assignment, Submission

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'total_marks']
        widgets = {
            'due_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(
                attrs={
                    'rows': 6,
                    'class': 'form-control',
                    'placeholder': 'Enter your submission text here (optional if submitting a file)'
                }
            ),
            'file': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf'
                }
            )
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size
            if file.size > 5242880:  # 5MB
                raise ValidationError('File size must not exceed 5MB.')
            
            # Check file type
            if not file.name.endswith('.pdf'):
                raise ValidationError('Only PDF files are allowed.')

        return file

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        file = cleaned_data.get('file')

        if not content and not file:
            raise ValidationError(
                'You must either provide text content or upload a file.'
            )

        return cleaned_data

class GradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['marks', 'feedback']
        widgets = {
            'marks': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.1',
                    'min': '0'
                }
            ),
            'feedback': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Provide feedback for the student'
                }
            )
        }

    def __init__(self, assignment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment
        self.fields['marks'].widget.attrs['max'] = assignment.total_marks

    def clean_marks(self):
        marks = self.cleaned_data.get('marks')
        if marks > self.assignment.total_marks:
            raise ValidationError(
                f'Marks cannot exceed the total marks ({self.assignment.total_marks})'
            )
        return marks
# users/forms.py
from django import forms
from .models import CustomUser

class ProfileUpdateForm(forms.ModelForm):
    role = forms.CharField(disabled=True, required=False, label='Role')

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'department', 'role']

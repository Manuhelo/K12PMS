# forms.py
from django import forms
from .models import ProcurementThreshold

class ProcurementThresholdForm(forms.ModelForm):
    class Meta:
        model = ProcurementThreshold
        fields = ['low_threshold', 'medium_threshold']
        widgets = {
            'low_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'medium_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

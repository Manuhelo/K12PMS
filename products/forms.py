from django import forms

class EducationalProductUploadForm(forms.Form):
    csv_file = forms.FileField(label='Select a CSV file')

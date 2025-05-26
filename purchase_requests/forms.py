from django import forms

class PurchaseRequestUploadForm(forms.Form):
    SEGMENT_CHOICES = [
        ('OIS', 'OIS'),
        ('B2B', 'B2B'),
        ('OCSE', 'OCSE'),
    ]
    segment = forms.ChoiceField(choices=SEGMENT_CHOICES, required=True)
    description = forms.CharField(max_length=100)
    remarks = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(label="Upload CSV or Excel File",
        widget=forms.ClearableFileInput(attrs={'accept': '.csv, .xls, .xlsx'}))


class RequestItemCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV", required=False)

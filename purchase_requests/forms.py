from django import forms

class PurchaseRequestUploadForm(forms.Form):
    SEGMENT_CHOICES = [
        ('OIS', 'OIS'),
        ('B2B', 'B2B'),
    ]
    segment = forms.ChoiceField(choices=SEGMENT_CHOICES, required=True)
    description = forms.CharField(max_length=100)
    remarks = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(help_text="Upload a CSV file with columns: sku, quantity, remarks")


class RequestItemCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV", required=False)

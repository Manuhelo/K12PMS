from django import forms

class PurchaseRequestUploadForm(forms.Form):
    description = forms.CharField(max_length=100)
    remarks = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(help_text="Upload a CSV file with columns: sku, quantity, remarks")

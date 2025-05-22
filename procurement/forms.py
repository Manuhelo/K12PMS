from django import forms

class VendorQuotationUploadForm(forms.Form):
    csv_file = forms.FileField()
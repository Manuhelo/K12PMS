from django import forms
from .models import GoodsReceipt, GoodsReceiptItem, Warehouse
from django.forms.models import inlineformset_factory
from django.contrib.auth import get_user_model

User = get_user_model()


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        fields = ['warehouse', 'remarks']

GoodsReceiptItemFormSet = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptItem,
    fields=['product', 'quantity_received'],
    extra=0,
    can_delete=False,
    widgets={
        'product': forms.Select(attrs={'readonly': 'readonly', 'disabled': 'disabled'}),
        'quantity_received': forms.NumberInput(attrs={'min': 0}),
    }
)



class WarehouseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(WarehouseForm, self).__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(role='WarehouseManager')

    class Meta:
        fields = ['name','location','manager']
        model = Warehouse
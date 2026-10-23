from django import forms

from .models import Customer, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "phone", "email", "address", "kra_pin", "is_active"]


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "customer_type", "phone", "email", "address", "credit_limit", "is_active"]

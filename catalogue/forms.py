from django import forms

from .models import Category, Product


class ProductForm(forms.ModelForm):
    opening_stock = forms.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        min_value=0,
        help_text="Stock on hand at your branch right now. Only for new products.",
    )

    class Meta:
        model = Product
        fields = [
            "name", "category", "unit", "is_weighed", "barcode", "sku", "supplier",
            "buying_price", "retail_price", "wholesale_price", "wholesale_min_qty",
            "max_discount_percent", "low_stock_level", "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        if not self.instance._state.adding:
            del self.fields["opening_stock"]

    def clean_barcode(self):
        return self.cleaned_data["barcode"] or None

    def clean_sku(self):
        return self.cleaned_data["sku"] or None

    def clean(self):
        data = super().clean()
        unit = data.get("unit")
        opening = data.get("opening_stock")
        if unit and opening and not unit.allows_decimal and opening != opening.to_integral_value():
            self.add_error("opening_stock", f"{unit} is counted in whole numbers.")
        return data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "is_active"]


class ImportForm(forms.Form):
    file = forms.FileField(help_text="CSV or Excel (.xlsx) with the template columns.")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith((".csv", ".xlsx", ".xlsm")):
            raise forms.ValidationError("Upload a .csv or .xlsx file.")
        return f

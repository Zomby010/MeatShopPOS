from django import forms

from .models import MovementType


class OpeningStockForm(forms.Form):
    quantity = forms.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    unit_cost = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False,
        help_text="Cost per unit. Leave blank to use the product's buying price.",
    )


class HistoryFilterForm(forms.Form):
    movement_type = forms.ChoiceField(choices=[("", "All types")] + MovementType.choices, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    branch = forms.ChoiceField(required=False)
    staff = forms.ChoiceField(required=False)

    def __init__(self, *args, branches, staff, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].choices = [("", "All branches")] + [(str(b.pk), b.name) for b in branches]
        self.fields["staff"].choices = [("", "All staff")] + [
            (str(u.pk), u.get_full_name() or u.username) for u in staff
        ]

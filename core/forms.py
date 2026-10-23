from django import forms
from django.contrib.auth import get_user_model

from .models import Branch, Role, StaffProfile

User = get_user_model()


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ["code", "name", "location", "phone", "is_main", "is_active"]


class PinLoginForm(forms.Form):
    staff = forms.ModelChoiceField(queryset=StaffProfile.objects.none(), widget=forms.HiddenInput)
    pin = forms.CharField(max_length=8, widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "off"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["staff"].queryset = StaffProfile.objects.filter(user__is_active=True).exclude(pin_hash="")


class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=30, required=False)
    role = forms.ChoiceField(choices=Role.choices)
    branch = forms.ModelChoiceField(queryset=Branch.objects.filter(is_active=True), required=False)
    password = forms.CharField(
        widget=forms.PasswordInput, required=False, help_text="Leave blank to keep the current password."
    )
    pin = forms.RegexField(
        regex=r"^\d{4,6}$",
        required=False,
        widget=forms.PasswordInput(attrs={"inputmode": "numeric"}),
        help_text="4 to 6 digits for quick till login. Leave blank to keep the current PIN.",
    )
    is_active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, instance=None, acting_user_is_owner=True, acting_branch=None, **kwargs):
        self.instance = instance
        self.acting_user_is_owner = acting_user_is_owner
        self.acting_branch = acting_branch
        if instance and "initial" not in kwargs:
            user = instance.user
            kwargs["initial"] = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": instance.phone,
                "role": instance.role,
                "branch": instance.branch,
                "is_active": user.is_active,
            }
        super().__init__(*args, **kwargs)
        if not acting_user_is_owner:
            # Managers only manage cashiers in their own branch.
            self.fields["role"].choices = [(Role.CASHIER, Role.CASHIER.label)]
            self.fields["branch"].queryset = Branch.objects.filter(pk=getattr(acting_branch, "pk", None))
            self.fields["branch"].required = True
        if instance is None:
            self.fields["password"].required = True
            self.fields["password"].help_text = ""

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username__iexact=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("That username is taken.")
        return username

    def clean(self):
        data = super().clean()
        if data.get("role") in (Role.CASHIER, Role.MANAGER) and not data.get("branch"):
            self.add_error("branch", "Cashiers and managers need a home branch.")
        return data

    def save(self):
        data = self.cleaned_data
        if self.instance:
            profile = self.instance
            user = profile.user
        else:
            user = User()
            profile = StaffProfile(user=user)
        user.username = data["username"]
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.is_active = data["is_active"]
        if data["password"]:
            user.set_password(data["password"])
        user.save()
        profile.user = user
        profile.phone = data["phone"]
        profile.role = data["role"]
        profile.branch = data["branch"]
        if data["pin"]:
            profile.set_pin(data["pin"])
        profile.save()
        return profile

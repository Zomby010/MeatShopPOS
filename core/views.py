from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from catalogue.models import Product
from inventory.models import BranchStock, StockMovement

from .forms import BranchForm, PinLoginForm, StaffForm
from .models import Branch, Role, StaffProfile
from .permissions import RoleRequiredMixin, has_role, role_required

PIN_MAX_ATTEMPTS = 5
PIN_LOCK_SECONDS = 300


class LoginView(auth_views.LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


def pin_login(request):
    """Quick till login: tap your name, type your PIN."""
    form = PinLoginForm(request.POST or None)
    staff_list = form.fields["staff"].queryset.select_related("user", "branch")
    if request.method == "POST" and form.is_valid():
        profile = form.cleaned_data["staff"]
        lock_key = f"pin-fail-{profile.pk}"
        failures = cache.get(lock_key, 0)
        if failures >= PIN_MAX_ATTEMPTS:
            form.add_error(None, "Too many wrong PINs. Wait 5 minutes or log in with your password.")
        elif profile.check_pin(form.cleaned_data["pin"]):
            cache.delete(lock_key)
            login(request, profile.user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("core:dashboard")
        else:
            cache.set(lock_key, failures + 1, PIN_LOCK_SECONDS)
            form.add_error("pin", "Wrong PIN.")
    return render(request, "core/pin_login.html", {"form": form, "staff_list": staff_list})


@login_required
def dashboard(request):
    branch = request.branch
    stock = BranchStock.objects.filter(branch=branch, product__is_active=True)
    value = stock.aggregate(
        total=Sum(
            ExpressionWrapper(F("quantity") * F("product__average_cost"), output_field=DecimalField())
        )
    )["total"] or Decimal(0)
    low_stock = (
        stock.filter(quantity__lte=F("product__low_stock_level"), product__low_stock_level__gt=0)
        .select_related("product", "product__unit")
        .order_by("quantity")
    )
    context = {
        "product_count": Product.objects.filter(is_active=True).count(),
        "stock_value": value,
        "low_stock": low_stock[:10],
        "low_stock_count": low_stock.count(),
        "recent_movements": StockMovement.objects.filter(branch=branch)
        .select_related("product", "product__unit", "created_by")[:10],
    }
    return render(request, "core/dashboard.html", context)


@require_POST
@role_required(Role.OWNER)
def switch_branch(request):
    branch = get_object_or_404(Branch, pk=request.POST.get("branch"), is_active=True)
    request.session["branch_id"] = str(branch.pk)
    messages.info(request, f"Now working in {branch}.")
    return redirect(request.POST.get("next") or "core:dashboard")


class BranchList(RoleRequiredMixin, ListView):
    minimum_role = Role.OWNER
    model = Branch
    template_name = "core/branch_list.html"


class BranchFormMixin(RoleRequiredMixin):
    minimum_role = Role.OWNER
    model = Branch
    form_class = BranchForm
    template_name = "form.html"
    success_url = reverse_lazy("core:branch_list")


class BranchCreate(BranchFormMixin, CreateView):
    extra_context = {"title": "New branch"}


class BranchUpdate(BranchFormMixin, UpdateView):
    extra_context = {"title": "Edit branch"}


@role_required(Role.MANAGER)
def staff_list(request):
    qs = StaffProfile.objects.select_related("user", "branch")
    if not has_role(request.user, Role.OWNER):
        qs = qs.filter(branch=request.branch)
    return render(request, "core/staff_list.html", {"staff": qs})


def _staff_form(request, instance=None):
    is_owner = has_role(request.user, Role.OWNER)
    if instance and not is_owner and (
        instance.branch_id != getattr(request.branch, "pk", None) or instance.role != Role.CASHIER
    ):
        raise PermissionDenied
    form = StaffForm(
        request.POST or None,
        instance=instance,
        acting_user_is_owner=is_owner,
        acting_branch=request.branch,
    )
    if request.method == "POST" and form.is_valid():
        profile = form.save()
        messages.success(request, f"Saved {profile}.")
        return redirect("core:staff_list")
    title = f"Edit {instance}" if instance else "New staff member"
    return render(request, "form.html", {"form": form, "title": title})


@role_required(Role.MANAGER)
def staff_create(request):
    return _staff_form(request)


@role_required(Role.MANAGER)
def staff_update(request, pk):
    return _staff_form(request, get_object_or_404(StaffProfile, pk=pk))

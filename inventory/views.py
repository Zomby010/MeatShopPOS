from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from catalogue.models import Product
from core.models import Branch, Role
from core.permissions import has_role, role_required

from .forms import HistoryFilterForm, OpeningStockForm
from .models import StockMovement
from .services import StockError, set_opening_stock


@login_required
def product_history(request, pk):
    """Every stock movement of a product: its journey through each stage."""
    product = get_object_or_404(Product.objects.select_related("unit"), pk=pk)
    is_owner = has_role(request.user, Role.OWNER)
    branches = Branch.objects.all() if is_owner else Branch.objects.filter(pk=request.branch.pk)
    qs = product.movements.select_related("branch", "created_by")
    staff_ids = qs.exclude(created_by=None).values_list("created_by", flat=True).distinct()
    form = HistoryFilterForm(
        request.GET or None,
        branches=branches,
        staff=get_user_model().objects.filter(pk__in=staff_ids),
    )
    if not is_owner:
        qs = qs.filter(branch=request.branch)
    if form.is_valid():
        data = form.cleaned_data
        if data["movement_type"]:
            qs = qs.filter(movement_type=data["movement_type"])
        if data["date_from"]:
            qs = qs.filter(created_at__date__gte=data["date_from"])
        if data["date_to"]:
            qs = qs.filter(created_at__date__lte=data["date_to"])
        if data["branch"]:
            qs = qs.filter(branch_id=data["branch"])
        if data["staff"]:
            qs = qs.filter(created_by_id=data["staff"])
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "inventory/product_history.html",
        {"product": product, "page": page, "form": form, "querystring": params.urlencode()},
    )


@role_required(Role.MANAGER)
def opening_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = OpeningStockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            set_opening_stock(
                product=product,
                branch=request.branch,
                quantity=form.cleaned_data["quantity"],
                unit_cost=form.cleaned_data["unit_cost"],
                user=request.user,
            )
        except StockError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Opening stock recorded for {product}.")
            return redirect("catalogue:product_detail", pk=product.pk)
    title = f"Opening stock: {product} at {request.branch}"
    return render(request, "form.html", {"form": form, "title": title})


@login_required
def movement_list(request):
    """Recent stock movements at the current branch, across all products."""
    qs = StockMovement.objects.filter(branch=request.branch).select_related("product", "product__unit", "created_by")
    movement_type = request.GET.get("type")
    if movement_type:
        qs = qs.filter(movement_type=movement_type)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "inventory/movement_list.html", {"page": page, "types": StockMovement._meta.get_field("movement_type").choices})

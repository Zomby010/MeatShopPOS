from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from core.models import Role
from core.permissions import RoleRequiredMixin, role_required
from inventory.models import BranchStock
from inventory.services import set_opening_stock

from .forms import CategoryForm, ImportForm, ProductForm
from .importer import import_products, template_xlsx
from .models import Category, Product
from .services import save_product


def products_with_stock(branch):
    stock = BranchStock.objects.filter(product=OuterRef("pk"), branch=branch).values("quantity")[:1]
    return Product.objects.select_related("category", "unit").annotate(
        branch_qty=Coalesce(Subquery(stock), Value(0), output_field=Product._meta.get_field("low_stock_level"))
    )


@login_required
def product_list(request):
    qs = products_with_stock(request.branch)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__iexact=q) | Q(barcode=q))
    category = request.GET.get("category")
    if category:
        qs = qs.filter(category_id=category)
    if request.GET.get("low"):
        qs = qs.filter(low_stock_level__gt=0, branch_qty__lte=F("low_stock_level"))
    if not request.GET.get("inactive"):
        qs = qs.filter(is_active=True)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    context = {"page": page, "categories": Category.objects.filter(is_active=True), "q": q}
    template = "catalogue/_product_rows.html" if request.htmx else "catalogue/product_list.html"
    return render(request, template, context)


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("category", "unit", "supplier"), pk=pk)
    context = {
        "product": product,
        "stock": product.stock.select_related("branch").order_by("branch__name"),
        "price_history": product.price_history.select_related("changed_by")[:20],
        "has_history_here": product.movements.filter(branch=request.branch).exists(),
    }
    return render(request, "catalogue/product_detail.html", context)


def _product_form(request, instance=None):
    form = ProductForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            product = save_product(form.save(commit=False), request.user)
            opening = form.cleaned_data.get("opening_stock")
            if opening:
                set_opening_stock(product=product, branch=request.branch, quantity=opening, user=request.user)
        messages.success(request, f"Saved {product}.")
        return redirect("catalogue:product_detail", pk=product.pk)
    title = f"Edit {instance}" if instance else "New product"
    return render(request, "form.html", {"form": form, "title": title})


@role_required(Role.MANAGER)
def product_create(request):
    return _product_form(request)


@role_required(Role.MANAGER)
def product_update(request, pk):
    return _product_form(request, get_object_or_404(Product, pk=pk))


@role_required(Role.MANAGER)
def category_list(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save(commit=False)
        category.created_by = request.user
        category.save()
        messages.success(request, f"Added category {category}.")
        return redirect("catalogue:category_list")
    return render(request, "catalogue/category_list.html", {"categories": Category.objects.all(), "form": form})


class CategoryUpdate(RoleRequiredMixin, UpdateView):
    minimum_role = Role.MANAGER
    model = Category
    form_class = CategoryForm
    template_name = "form.html"
    success_url = reverse_lazy("catalogue:category_list")
    extra_context = {"title": "Edit category"}


@role_required(Role.MANAGER)
def product_import(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    result = None
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        result = import_products(upload.name, upload.read(), branch=request.branch, user=request.user)
        if not result.errors:
            messages.success(request, "Import finished.")
    return render(request, "catalogue/import.html", {"form": form, "result": result})


@role_required(Role.MANAGER)
def import_template(request):
    response = HttpResponse(
        template_xlsx(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="meatpos_product_import.xlsx"'
    return response

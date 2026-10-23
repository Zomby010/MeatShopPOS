from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from core.models import Role
from core.permissions import RoleRequiredMixin

from .forms import CustomerForm, SupplierForm
from .models import Customer, Supplier


class SearchListMixin:
    paginate_by = 50
    search_fields = ("name", "phone")

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            cond = Q()
            for f in self.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        return qs


class StampCreatorMixin:
    def form_valid(self, form):
        if form.instance._state.adding:
            form.instance.created_by = self.request.user
            form.instance.branch = self.request.branch
        return super().form_valid(form)


class SupplierList(RoleRequiredMixin, SearchListMixin, ListView):
    minimum_role = Role.MANAGER
    model = Supplier
    template_name = "parties/supplier_list.html"


class SupplierFormMixin(RoleRequiredMixin, StampCreatorMixin):
    minimum_role = Role.MANAGER
    model = Supplier
    form_class = SupplierForm
    template_name = "form.html"
    success_url = reverse_lazy("parties:supplier_list")


class SupplierCreate(SupplierFormMixin, CreateView):
    extra_context = {"title": "New supplier"}


class SupplierUpdate(SupplierFormMixin, UpdateView):
    extra_context = {"title": "Edit supplier"}


class CustomerList(RoleRequiredMixin, SearchListMixin, ListView):
    model = Customer
    template_name = "parties/customer_list.html"


class CustomerFormMixin(RoleRequiredMixin, StampCreatorMixin):
    model = Customer
    form_class = CustomerForm
    template_name = "form.html"
    success_url = reverse_lazy("parties:customer_list")


class CustomerCreate(CustomerFormMixin, CreateView):
    extra_context = {"title": "New customer"}


class CustomerUpdate(CustomerFormMixin, UpdateView):
    # Credit limits are a manager decision.
    minimum_role = Role.MANAGER
    extra_context = {"title": "Edit customer"}

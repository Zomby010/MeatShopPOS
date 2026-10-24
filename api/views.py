from django.db.models import Q
from rest_framework import viewsets

from catalogue.models import Category, Product
from core.models import Role
from core.permissions import has_role
from inventory.models import BranchStock, StockMovement

from .serializers import (
    BranchStockSerializer,
    CategorySerializer,
    ProductCostSerializer,
    ProductSerializer,
    StockMovementSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Products. Filters: ?q= (name, SKU, barcode), ?category=<id>, ?active=1."""

    def get_queryset(self):
        qs = Product.objects.select_related("category", "unit")
        params = self.request.query_params
        if q := params.get("q"):
            qs = qs.filter(Q(name__icontains=q) | Q(sku__iexact=q) | Q(barcode=q))
        if category := params.get("category"):
            qs = qs.filter(category_id=category)
        if params.get("active"):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if has_role(self.request.user, Role.MANAGER):
            return ProductCostSerializer
        return ProductSerializer


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """Stock levels at the user's branch; owners may pass ?branch=<code>."""

    serializer_class = BranchStockSerializer

    def get_queryset(self):
        qs = BranchStock.objects.select_related("product", "branch").order_by("product__name")
        code = self.request.query_params.get("branch")
        if code and has_role(self.request.user, Role.OWNER):
            return qs.filter(branch__code=code)
        return qs.filter(branch=self.request.branch)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """Stock ledger for the user's branch. Filter by ?product=<id>."""

    serializer_class = StockMovementSerializer

    def get_queryset(self):
        qs = StockMovement.objects.select_related("branch")
        if not has_role(self.request.user, Role.OWNER):
            qs = qs.filter(branch=self.request.branch)
        if product := self.request.query_params.get("product"):
            qs = qs.filter(product_id=product)
        return qs

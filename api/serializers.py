from rest_framework import serializers

from catalogue.models import Category, Product
from inventory.models import BranchStock, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active"]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")
    unit = serializers.CharField(source="unit.code")

    class Meta:
        model = Product
        fields = [
            "id", "name", "category", "unit", "barcode", "sku", "is_weighed", "is_active",
            "retail_price", "wholesale_price", "wholesale_min_qty", "max_discount_percent",
            "low_stock_level", "updated_at",
        ]


class ProductCostSerializer(ProductSerializer):
    """Adds cost fields, shown to managers and owners only."""

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["buying_price", "average_cost"]


class BranchStockSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(source="product_id")
    product_name = serializers.CharField(source="product.name")
    branch = serializers.CharField(source="branch.code")

    class Meta:
        model = BranchStock
        fields = ["product", "product_name", "branch", "quantity", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    branch = serializers.CharField(source="branch.code")

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "branch", "movement_type", "quantity_change", "quantity_before",
            "quantity_after", "unit_cost", "value_change", "reason", "created_by", "created_at",
        ]

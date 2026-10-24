from django.contrib import admin

from .models import Category, PriceHistory, Product, UnitOfMeasure

admin.site.register(Category)
admin.site.register(UnitOfMeasure)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit", "retail_price", "wholesale_price", "average_cost", "is_active"]
    list_filter = ["category", "unit", "is_active"]
    search_fields = ["name", "sku", "barcode"]
    readonly_fields = ["average_cost"]


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ["product", "field", "old_value", "new_value", "changed_by", "created_at"]

    def has_change_permission(self, request, obj=None):
        return False

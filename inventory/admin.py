from django.contrib import admin

from .models import BranchStock, StockMovement


class ReadOnlyAdmin(admin.ModelAdmin):
    """Stock is changed only through the app, never by hand in the admin."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BranchStock)
class BranchStockAdmin(ReadOnlyAdmin):
    list_display = ["product", "branch", "quantity"]
    list_filter = ["branch"]


@admin.register(StockMovement)
class StockMovementAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "product", "branch", "movement_type", "quantity_change", "quantity_after", "created_by"]
    list_filter = ["movement_type", "branch"]

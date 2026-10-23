from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"

    def ready(self):
        from django.db.models.signals import pre_delete

        from .models import ImmutableMovementError, StockMovement

        def block_delete(sender, instance, **kwargs):
            raise ImmutableMovementError("Stock movements cannot be deleted.")

        # Also catches queryset.delete(), which skips Model.delete().
        pre_delete.connect(block_delete, sender=StockMovement, weak=False)

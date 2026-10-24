from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from catalogue.models import MONEY, QTY
from core.models import SyncModel, TimeStampedModel


class BranchStock(TimeStampedModel):
    """Cached stock level of one product at one branch.

    Only inventory.services may change `quantity`; the ledger is the truth.
    """

    product = models.ForeignKey("catalogue.Product", on_delete=models.PROTECT, related_name="stock")
    branch = models.ForeignKey("core.Branch", on_delete=models.PROTECT, related_name="stock")
    quantity = models.DecimalField(**QTY, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "branch"], name="unique_branch_stock")
        ]

    def __str__(self):
        return f"{self.product} @ {self.branch}: {self.quantity}"


class MovementType(models.TextChoices):
    OPENING = "OPENING", "Opening stock"
    PURCHASE = "PURCHASE", "Purchase"
    SALE = "SALE", "Sale"
    SALE_RETURN = "SALE_RETURN", "Sale return"
    CONVERSION_OUT = "CONVERSION_OUT", "Conversion out"
    CONVERSION_IN = "CONVERSION_IN", "Conversion in"
    RECOUNT = "RECOUNT", "Stock recount"
    TRANSFER_OUT = "TRANSFER_OUT", "Transfer out"
    TRANSFER_IN = "TRANSFER_IN", "Transfer in"
    DELIVERY = "DELIVERY", "Delivery"
    WRITE_OFF = "WRITE_OFF", "Write-off"


class ImmutableMovementError(Exception):
    pass


class StockMovement(SyncModel):
    """One change to the stock of a product at a branch. Rows are never edited
    or deleted; mistakes are corrected with a new movement."""

    product = models.ForeignKey("catalogue.Product", on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_change = models.DecimalField(**QTY)
    quantity_before = models.DecimalField(**QTY)
    quantity_after = models.DecimalField(**QTY)
    unit_cost = models.DecimalField(**MONEY, default=0)
    value_change = models.DecimalField(**MONEY, default=0)
    reference_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    reference_id = models.CharField(max_length=64, blank=True)
    reference = GenericForeignKey("reference_type", "reference_id")
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "branch", "created_at"]),
            models.Index(fields=["movement_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity_change} {self.product}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableMovementError("Stock movements cannot be edited.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableMovementError("Stock movements cannot be deleted.")

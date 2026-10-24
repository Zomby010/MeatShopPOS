from django.db import models

from core.models import SyncModel


class Supplier(SyncModel):
    name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    kra_pin = models.CharField("KRA PIN", max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(SyncModel):
    class Type(models.TextChoices):
        RETAIL = "retail", "Retail"
        WHOLESALE = "wholesale", "Wholesale"

    name = models.CharField(max_length=150)
    customer_type = models.CharField(max_length=20, choices=Type.choices, default=Type.RETAIL)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Maintained by sales and payments from Phase 3; read-only in forms.
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

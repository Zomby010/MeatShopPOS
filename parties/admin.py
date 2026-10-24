from django.contrib import admin

from .models import Customer, Supplier

admin.site.register(Supplier)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "customer_type", "phone", "credit_limit", "balance"]
    readonly_fields = ["balance"]

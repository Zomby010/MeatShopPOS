from django.contrib import admin

from .models import Branch, StaffProfile


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location", "is_main", "is_active"]


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "branch", "phone"]
    list_filter = ["role", "branch"]
    exclude = ["pin_hash"]

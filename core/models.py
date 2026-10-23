import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import Group
from django.db import models


class TimeStampedModel(models.Model):
    """UUID key and timestamps, so rows made at different branches never clash."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SyncModel(TimeStampedModel):
    """Base for every table that is synced to the central server.

    `branch` is where the row was created. Shared tables such as products
    leave it empty, meaning the row belongs to the whole business.
    """

    branch = models.ForeignKey(
        "core.Branch", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class Branch(TimeStampedModel):
    code = models.SlugField(max_length=20, unique=True, help_text="Short code, e.g. MAIN")
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_main = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_main", "name"]
        verbose_name_plural = "branches"

    def __str__(self):
        return self.name


class Role(models.TextChoices):
    CASHIER = "cashier", "Cashier"
    MANAGER = "manager", "Branch Manager"
    OWNER = "owner", "Owner/Admin"


# Django group that mirrors each role, so permissions can also be granted
# through the admin if ever needed.
ROLE_GROUPS = {
    Role.CASHIER: "Cashier",
    Role.MANAGER: "Branch Manager",
    Role.OWNER: "Owner/Admin",
}

# Higher number = more access. Used by core.permissions.
ROLE_RANK = {Role.CASHIER: 1, Role.MANAGER: 2, Role.OWNER: 3}


class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="staff",
        help_text="Home branch. Owners may leave this empty.",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    phone = models.CharField(max_length=30, blank=True)
    pin_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["user__first_name", "user__username"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def rank(self):
        return ROLE_RANK.get(self.role, 0)

    def set_pin(self, pin):
        self.pin_hash = make_password(pin) if pin else ""

    def check_pin(self, pin):
        return bool(self.pin_hash) and check_password(pin, self.pin_hash)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_groups()

    def sync_groups(self):
        names = set(ROLE_GROUPS.values())
        groups = {g.name: g for g in Group.objects.filter(name__in=names)}
        self.user.groups.remove(*[g for n, g in groups.items() if n != ROLE_GROUPS[self.role]])
        target = groups.get(ROLE_GROUPS[self.role])
        if target:
            self.user.groups.add(target)

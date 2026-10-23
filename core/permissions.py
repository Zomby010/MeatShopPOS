from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import ROLE_RANK, Role


def user_rank(user):
    if not user.is_authenticated:
        return 0
    if user.is_superuser:
        return ROLE_RANK[Role.OWNER]
    profile = getattr(user, "staff", None)
    return profile.rank if profile else 0


def has_role(user, minimum_role):
    """True if the user's role is at least `minimum_role`."""
    return user_rank(user) >= ROLE_RANK[minimum_role]


def role_required(minimum_role):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("core:login")
            if not has_role(request.user, minimum_role):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(AccessMixin):
    minimum_role = Role.CASHIER

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_role(request.user, self.minimum_role):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

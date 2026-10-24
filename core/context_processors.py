from .models import Branch, Role
from .permissions import has_role


def current_branch(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    is_owner = has_role(user, Role.OWNER)
    return {
        "current_branch": getattr(request, "branch", None),
        "is_manager": has_role(user, Role.MANAGER),
        "is_owner": is_owner,
        "switchable_branches": Branch.objects.filter(is_active=True) if is_owner else [],
    }

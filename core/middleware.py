from django.conf import settings

from .models import Branch, Role


def resolve_branch(request):
    """The branch the user is working in for this request.

    Staff are tied to their home branch. Owners can switch branch, which is
    kept in the session; otherwise they get the install's default branch.
    """
    user = request.user
    if not user.is_authenticated:
        return None
    profile = getattr(user, "staff", None)
    is_owner = user.is_superuser or (profile and profile.role == Role.OWNER)
    if is_owner:
        branch_id = request.session.get("branch_id")
        if branch_id:
            branch = Branch.objects.filter(pk=branch_id, is_active=True).first()
            if branch:
                return branch
    if profile and profile.branch_id:
        return profile.branch
    code = settings.MEATPOS_DEFAULT_BRANCH_CODE
    qs = Branch.objects.filter(is_active=True)
    return (code and qs.filter(code=code).first()) or qs.first()


class CurrentBranchMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.branch = resolve_branch(request)
        request.htmx = request.headers.get("HX-Request") == "true"
        return self.get_response(request)

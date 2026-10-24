from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("login/pin/", views.pin_login, name="pin_login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("switch-branch/", views.switch_branch, name="switch_branch"),
    path("branches/", views.BranchList.as_view(), name="branch_list"),
    path("branches/new/", views.BranchCreate.as_view(), name="branch_create"),
    path("branches/<uuid:pk>/", views.BranchUpdate.as_view(), name="branch_update"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/new/", views.staff_create, name="staff_create"),
    path("staff/<uuid:pk>/", views.staff_update, name="staff_update"),
]

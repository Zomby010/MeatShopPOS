from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("products/", include("catalogue.urls")),
    path("stock/", include("inventory.urls")),
    path("", include("parties.urls")),
    path("", include("core.urls")),
]

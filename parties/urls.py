from django.urls import path

from . import views

app_name = "parties"

urlpatterns = [
    path("suppliers/", views.SupplierList.as_view(), name="supplier_list"),
    path("suppliers/new/", views.SupplierCreate.as_view(), name="supplier_create"),
    path("suppliers/<uuid:pk>/", views.SupplierUpdate.as_view(), name="supplier_update"),
    path("customers/", views.CustomerList.as_view(), name="customer_list"),
    path("customers/new/", views.CustomerCreate.as_view(), name="customer_create"),
    path("customers/<uuid:pk>/", views.CustomerUpdate.as_view(), name="customer_update"),
]

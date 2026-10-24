from django.urls import path

from . import views

app_name = "catalogue"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("new/", views.product_create, name="product_create"),
    path("import/", views.product_import, name="product_import"),
    path("import/template.xlsx", views.import_template, name="import_template"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/<uuid:pk>/", views.CategoryUpdate.as_view(), name="category_update"),
    path("<uuid:pk>/", views.product_detail, name="product_detail"),
    path("<uuid:pk>/edit/", views.product_update, name="product_update"),
]

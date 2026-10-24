from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("movements/", views.movement_list, name="movement_list"),
    path("products/<uuid:pk>/history/", views.product_history, name="product_history"),
    path("products/<uuid:pk>/opening/", views.opening_stock, name="opening_stock"),
]

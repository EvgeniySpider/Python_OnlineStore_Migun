from django.urls import path

from .views import OrderCancelView, OrderCreateView, OrderListView

urlpatterns = [
    path("order_create/", OrderCreateView.as_view(), name="order_create"),
    path("my-orders/", OrderListView.as_view(), name="order_list"),
    path("cancel/<int:order_id>/", OrderCancelView.as_view(), name="order_cancel"),
]

from django.urls import path
from .views import OrderCreateView, OrderListView


urlpatterns = [
    path('order_create/', OrderCreateView.as_view(), name='order_create'),
    path('my-orders/', OrderListView.as_view(), name='order_list')
]


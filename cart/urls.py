from django.urls import path
from .views import AddToCartView, ShowCartView, CartItemDeleteView

app_name = 'cart'

urlpatterns = [
    path('add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart_detail/', ShowCartView.as_view(), name='cart_detail'),
    path('delete/<int:item_id>/', CartItemDeleteView.as_view(), name='cart_item_delete'),
]
from django.urls import path
from .views import AddToCartView, ShowCartView, CartItemDeleteView, CartItemUpdateQuantityView

app_name = 'cart'

urlpatterns = [
    path('add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart_detail/', ShowCartView.as_view(), name='cart_detail'),
    path('delete/<int:item_id>/', CartItemDeleteView.as_view(), name='cart_item_delete'),
    path('cart_update/<int:item_id>/<str:action>/', CartItemUpdateQuantityView.as_view(),
         name='quantity_item_update')
]
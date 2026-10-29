from django.urls import path

from goods.views import ProductDetailView

urlpatterns = [path("<int:pk>", ProductDetailView.as_view(), name="product_detail")]

from goods.views import ProductDetailView
from django.urls import path


urlpatterns = [
    path('<int:pk>', ProductDetailView.as_view(), name='product_detail')
]

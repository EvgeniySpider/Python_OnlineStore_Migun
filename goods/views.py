from django.shortcuts import render
from django.views.generic import ListView, DetailView
from goods.models import Product


# Create your views here.
class IndexView(ListView):
    template_name = 'index.html'
    context_object_name = 'products'  # Имя переменной в шаблоне
    def get_queryset(self):
        # Жадная загрузка категории и остатка за один SQL JOIN
        return Product.objects.select_related('category', 'stock').all()


class ProductDetailView(DetailView):
    model = Product
    context_object_name = 'product_object'
  

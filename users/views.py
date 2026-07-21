from django.shortcuts import render

# Create your views here.
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from goods.models import Product


class IndexView(ListView):
    model = Product
    template_name = 'index.html'
    context_object_name = 'products'  # Имя переменной в шаблоне
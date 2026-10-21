from django.contrib import admin

# Register your models here.
from goods.models import Category, Product, Stock

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Stock)

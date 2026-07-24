from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from goods.models import Product
from .models import Cart, CartItem


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        # 1. Получаем товар или 404
        product = get_object_or_404(Product, id=product_id)

        # 2. Берем или создаем корзину для текущего юзера
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # 3. Ищем товар в корзине или создаем
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product
        )

        if not created:
            # Если товар уже был в корзине — увеличиваем количество
            cart_item.quantity += 1
            cart_item.save()
            
        # 4. Перенаправляем пользователя (например, в саму корзину или обратно)
        return redirect('home')

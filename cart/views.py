from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from goods.models import Product, Stock
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


class ShowCartView(LoginRequiredMixin, ListView):
    model = CartItem
    template_name = 'cart/cart_detail.html'
    context_object_name = 'cart_items'

    def get_queryset(self):
        return (CartItem.objects.filter(cart_id=self.request.user.id)
                .select_related('product'))


class CartItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        # Достаем позицию из корзины, проверяя, что она принадлежит ИМЕННО ТЕКУЩЕМУ юзеру
        cart_item = get_object_or_404(CartItem, id=item_id, cart_id=request.user.id)
        

        cart_item.delete()
        return redirect('cart:cart_detail')


class CartItemUpdateQuantityView(LoginRequiredMixin, View):
    def post(self, request, item_id, action):
        cart_item = get_object_or_404(CartItem, id=item_id, cart_id=request.user.id)

        if action == 'increase':
            stock = get_object_or_404(Stock, product_id=cart_item.product_id)
            if stock.quantity > cart_item.quantity:
                cart_item.quantity += 1
            
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1

        cart_item.save()
        return redirect('cart:cart_detail')

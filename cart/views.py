from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from goods.models import Product, Stock
from .models import Cart, CartItem
from django.contrib import messages


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):

        stock = get_object_or_404(Stock, product_id=product_id)
        product = get_object_or_404(Product, id=product_id)

        if stock.quantity <= 0:
            messages.error(
                request,
                f'Товара "{product.name}" на складе сейчас нет'
            )
            return redirect('home')

        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            product=product
        )

        if not created:
            if cart_item.quantity >= stock.quantity:
                messages.error(
                    request,
                    f'Товар "{product.name}" закончился на складе, всего {stock.quantity} шт'
                )
                return redirect('home')

            # Если товар уже был в корзине — увеличиваем количество
            cart_item.quantity += 1
            cart_item.save()

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
            else:
                messages.warning(request, f'На складе больше нет товара \
                "{cart_item.product.name}". Доступно всего: {stock.quantity} шт.')
            
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                messages.warning(request, 'Минимальное количество товара в корзине — 1 шт.')

        cart_item.save()
        return redirect('cart:cart_detail')

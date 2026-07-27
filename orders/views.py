from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.db import transaction
from goods.models import Stock
from orders.models import OrderItem
from .forms import OrderModelForm
from cart.models import CartItem


class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        # Если у пользователя пустая корзина то оформлять нечего
        if not CartItem.objects.filter(cart_id=user.id).exists():
            return redirect('cart:cart_detail')

        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'city': user.city,
            'street': user.street,
            'house_number': user.house_number,
            'apartment_number': user.apartment_number,
        }

        form = OrderModelForm(initial=initial_data)
        context = {
            'form':form
        }

        return render(request, 'orders/order_create.html', context)

    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        user = request.user
        form = OrderModelForm(data=request.POST)

        # Проверка формы на валидность
        if not form.is_valid():
            return render(request, 'orders/order_create.html', {'form': form})

        cart_items = CartItem.objects.filter(cart_id=user.id).select_related('product')

        if not cart_items.exists():
            return redirect('cart:cart_detail')

        # ПРОВЕРКА: Сначала проверяем ВСЕ товары на складские остатки
        for cart_item in cart_items:
            try:
                stock_obj = Stock.objects.get(product_id=cart_item.product_id)
            except Stock.DoesNotExist:
                form.add_error(None, f"Товар {cart_item.product.name} отсутствует на складе.")
                return render(request, 'orders/order_create.html', {'form': form})
            
            if cart_item.quantity > stock_obj.quantity:
                form.add_error(None, f"Недостаточно товара '{cart_item.product.name}'. Доступно: {stock_obj.quantity} шт.")
                return render(request, 'orders/order_create.html', {'form': form})

        order = form.save(commit=False)
        order.user = user # Вручную указываем id, всё остальное ввёл пользователь
        order.save()

        # Списываем товары, создаем OrderItem и чистим корзину
        for cart_item in cart_items:
            # Уменьшаем склад
            stock_obj = Stock.objects.get(product_id=cart_item.product_id)
            stock_obj.quantity -= cart_item.quantity
            stock_obj.save()

            # Фиксируем товар в заказе
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,  # Фиксируем цену на момент покупки
                quantity=cart_item.quantity
            )

        # Очищаем корзину пользователя
        cart_items.delete()

        return redirect('home')

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from cart.models import CartItem
from goods.models import Stock
from orders.models import Order

from .forms import OrderModelForm
from .services import create_order


class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        # Если у пользователя пустая корзина то оформлять нечего
        if not CartItem.objects.filter(cart_id=user.id).exists():
            return redirect("cart:cart_detail")

        initial_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "city": user.city,
            "street": user.street,
            "house_number": user.house_number,
            "apartment_number": user.apartment_number,
        }

        form = OrderModelForm(initial=initial_data)
        context = {"form": form}

        return render(request, "orders/order_create.html", context)

    def post(self, request, *args, **kwargs):
        user = request.user
        form = OrderModelForm(data=request.POST)

        # Проверка формы на валидность
        if not form.is_valid():
            messages.error(
                request, "Пожалуйста, исправьте ошибки в форме и повторите попытку"
            )
            return render(request, "orders/order_create.html", {"form": form})

        # Бизнес-логика оформления заказа вынесена в сервис
        # (orders/services.py), который не знает про request/response.
        order, errors = create_order(user=user, form_data=form.cleaned_data)

        # Сервис сообщил, что корзина пуста — оформлять нечего
        if order is None and not errors:
            return redirect("cart:cart_detail")

        # Сервис вернул ошибки по складским остаткам
        if errors:
            for error in errors:
                form.add_error(None, error)
            messages.error(request, "Заказ не был оформлен")
            return render(request, "orders/order_create.html", {"form": form})

        messages.success(request, "Заказ успешно оформлен")
        return redirect("home")


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        # Достаем пользователя через self.request.user
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )


class OrderCancelView(LoginRequiredMixin, View):
    @method_decorator(transaction.atomic)
    def post(self, request, order_id: int):
        # 1. Достаем заказ. Ищем строго по id заказа И текущему юзеру (защита от чужих заказов)
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # 2. Проверяем статус по:
        if order.status == Order.Status.IN_PROGRESS:
            messages.error(
                request,
                f"Заказ №{order.id} уже передан в обработку и не может быть отменён.",
            )
            return redirect("order_list")

        if order.status != Order.Status.CREATED:
            messages.warning(
                request,
                f"Заказ №{order.id} со статусом «{order.get_status_display()}» нельзя отменить.",
            )
            return redirect("order_list")

        # 3. Если статус "created" — возвращаем товары на склад:
        for item in order.items.all():
            stock = Stock.objects.get(product=item.product)
            stock.quantity += item.quantity
            stock.save()

        # 4. Переводим статус в "Отменён":
        order.status = Order.Status.CANCELED
        order.save()

        messages.success(
            request, f"Заказ №{order.id} успешно отменён, товары возвращены на склад."
        )
        return redirect("order_list")

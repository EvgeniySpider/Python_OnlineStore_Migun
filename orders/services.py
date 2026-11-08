"""Сервисный слой приложения orders.

Здесь живёт бизнес-логика, не зависящая от request/response:
функции можно вызывать из вьюх, management-команд и модульных тестов.
"""

from django.contrib.auth import get_user_model
from django.db import transaction

from cart.models import CartItem
from goods.models import Stock

from .models import Order, OrderItem

User = get_user_model()


@transaction.atomic
def create_order(user, form_data: dict) -> tuple[Order | None, list[str]]:
    """Оформляет заказ на основе корзины пользователя.

    Функция ничего не знает про request/response (POST/GET, редиректы,
    messages)

    Args:
        user: пользователь, от имени которого оформляется заказ.
        form_data: валидированные данные формы заказа (form.cleaned_data).

    Returns:
        Кортеж (order, errors):
        - (Order, [])      — заказ успешно создан, корзина очищена;
        - (None, [])       — корзина пользователя пуста, оформлять нечего;
        - (None, errors)   — заказ не создан, errors — список текстов ошибок.
    """
    cart_items = CartItem.objects.filter(cart_id=user.id).select_related("product")

    # Корзина пуста — оформлять нечего
    if not cart_items.exists():
        return None, []

    # ПРОВЕРКА: Сначала проверяем ВСЕ товары на складские остатки
    errors: list[str] = []
    for cart_item in cart_items:
        try:
            stock_obj = Stock.objects.get(product_id=cart_item.product_id)
        except Stock.DoesNotExist:
            errors.append(f"Товар {cart_item.product.name} отсутствует на складе.")
            continue

        if cart_item.quantity > stock_obj.quantity:
            errors.append(
                f"Недостаточно товара '{cart_item.product.name}'. "
                f"Доступно: {stock_obj.quantity} шт."
            )

    if errors:
        return None, errors

    order = Order.objects.create(user=user, **form_data)

    # Списываем товары, создаём OrderItem и чистим корзину
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
            quantity=cart_item.quantity,
        )

    # Очищаем корзину пользователя
    cart_items.delete()

    return order, []

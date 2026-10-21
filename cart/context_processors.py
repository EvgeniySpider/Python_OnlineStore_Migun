from django.db.models import Sum
from .models import CartItem


def cart(request):
    """
    Контекстный процессор для подсчёта общего количества товаров в корзине.
    Возвращает словарь, ключи которого становятся переменными во всех шаблонах.
    """
    if request.user.is_authenticated:
        total_quantity = (
            CartItem.objects.filter(cart_id=request.user.id).aggregate(
                Sum('quantity')
            )['quantity__sum']
            or 0
        )
    else:
        # Для неавторизованных пользователей возвращаем 0
        total_quantity = 0

    return {'cart_total_quantity': total_quantity}


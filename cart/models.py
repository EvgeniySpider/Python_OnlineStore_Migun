from django.db import models
from django.contrib.auth import get_user_model
from goods.models import Product


User = get_user_model()


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='cart',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='cart_items',  # Говорим прямо: элементы этой корзины
        verbose_name='Корзина',
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name='Количество'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'], name='unique_cart_product'
            )
        ]

    def __str__(self):
        return f'{self.product.name} ({self.quantity} шт.)'

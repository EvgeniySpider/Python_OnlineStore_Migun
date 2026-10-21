from django.db import models
from django.contrib.auth import get_user_model
from goods.models import Product


User = get_user_model()

# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершён'),
        ('canceled', 'Отменён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Покупатель',
    )
    # Контакты и адрес, зафиксированные на момент заказа
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    phone_number = models.CharField(max_length=20, verbose_name='Телефон')

    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=150, verbose_name='Улица')
    house_number = models.CharField(max_length=20, verbose_name='Номер дома')
    apartment_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Квартира/Офис'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name='Статус заказа',
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ №{self.id} | {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар',
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Цена покупки'
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product.name} ({self.quantity} шт.)'
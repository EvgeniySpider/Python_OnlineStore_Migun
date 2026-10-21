from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название товара')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Изображение')
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='products', 
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True, # Указываем Django НЕ создавать стандартное поле id
        related_name='stock',
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        default=0, 
        verbose_name='Количество на складе'
    )

    class Meta:
        verbose_name = 'Остаток на складе'
        verbose_name_plural = 'Остатки на складе'

    def __str__(self):
        return f"{self.product.name} — {self.quantity} шт."

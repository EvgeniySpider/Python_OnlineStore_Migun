from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    # 1. ФИО
    # last_name и first_name уже есть в AbstractUser.
    # Отчество — необязательное поле (у кого-то его нет)
    patronymic = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        verbose_name='Отчество'
    )

    # 2. Контактная информация
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='Номер телефона'
    )

    # 3. Адресные данные
    city = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='Город'
    )
    street = models.CharField(
        max_length=150, 
        blank=True, 
        null=True, 
        verbose_name='Улица'
    )
    house_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='Номер дома'
    )
    # Квартира/Офис — необязательное поле (для частных домов)
    apartment_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='Квартира/Офис'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
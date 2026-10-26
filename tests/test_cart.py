from http import HTTPStatus
import pytest
from django.test import Client
from django.urls import reverse
from cart.models import Cart, CartItem
from goods.models import Product, Stock
from users.models import User


@pytest.mark.django_db
class TestAddToCart:
    
    def test_add_to_cart_new_item(
        self,
        auth_client: Client,
        user: User,
        product: Product
    ):
        """Тест: Первое добавление товара в корзину"""
        url = reverse('cart:add_to_cart', args=[product.id])
        
        # Делаем POST-запрос на добавление
        response = auth_client.post(url)
        
        # Проверяем редирект на главную страницу
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse('home')
        
        # Проверяем, что корзина и элемент корзины создались
        cart = Cart.objects.get(user=user)
        cart_item = CartItem.objects.get(cart=cart, product=product)
        
        assert cart_item.quantity == 1

    def test_add_to_cart_existing_item(
        self,
        auth_client: Client,
        user: User,
        product: Product
    ):
        """Тест: Добавление товара, который уже есть в корзине (увеличение количества)"""
        url = reverse('cart:add_to_cart', args=[product.id])
        
        # Добавляем товар дважды
        auth_client.post(url)
        auth_client.post(url)
        
        cart_item = CartItem.objects.get(cart__user=user, product=product)
        
        # Количество должно увеличиться до 2
        assert cart_item.quantity == 2

    def test_add_to_cart_out_of_stock(
        self,
        auth_client: Client,
        user: User,
        product: Product,
        stock: Stock
    ):
        """Тест: Попытка добавить товар, которого нет на складе"""
        # Обнуляем остатки
        stock.quantity = 0
        stock.save()
        
        url = reverse('cart:add_to_cart', args=[product.id])
        response = auth_client.post(url, follow=True)
        
        # Проверяем, что товар не добавился
        assert not CartItem.objects.filter(cart__user=user, product=product).exists()
        
        # Проверяем сообщение об ошибке (messages)
        messages = list(response.context['messages'])
        assert len(messages) == 1
        assert 'на складе сейчас нет' in str(messages[0])

    def test_add_to_cart_exceed_stock_limit(
        self, auth_client: Client,
        user: User,
        product: Product,
        stock: Stock
    ):
        """Тест: Попытка добавить товара больше, чем есть на складе"""
        # Устанавливаем на складе ровно 1 шт.
        stock.quantity = 1
        stock.save()
        
        url = reverse('cart:add_to_cart', args=[product.id])
        
        # Добавляем первый раз (успешно)
        auth_client.post(url)
        # Пытаемся добавить второй раз (должна сработать защита)
        response = auth_client.post(url, follow=True)
        
        cart_item = CartItem.objects.get(cart__user=user, product=product)

        # Количество осталось равным 1
        assert cart_item.quantity == 1
        
        # Проверяем оба сообщения (первое от успешного добавления, второе от ошибки лимита)
        messages = list(response.context['messages'])
        assert len(messages) == 2
        assert 'Товар "Ноутбук MSI" успешно добавлен в корзину!' in str(messages[0])
        assert 'Товар "Ноутбук MSI" закончился на складе, всего 1 шт' in str(messages[1])
    
    def test_anonymous_user_cannot_add_to_cart(
        self,
        client: Client,
        product: Product
    ):
        """Тест: Анонимный пользователь перенаправляется на страницу логина"""
        url = reverse('cart:add_to_cart', args=[product.id])
        response = client.post(url)
        
        assert response.status_code == HTTPStatus.FOUND
        assert response.url.startswith(reverse('login'))
        assert not CartItem.objects.exists()
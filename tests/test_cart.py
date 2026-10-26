from http import HTTPStatus
import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects
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
        url: str = reverse('cart:add_to_cart', args=[product.id])
        
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
        url: str = reverse('cart:add_to_cart', args=[product.id])
        
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
        
        url: str = reverse('cart:add_to_cart', args=[product.id])
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
        
        url: str = reverse('cart:add_to_cart', args=[product.id])
        
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
        url: str = reverse('cart:add_to_cart', args=[product.id])
        response = client.post(url)
        
        assert response.status_code == HTTPStatus.FOUND
        assert response.url.startswith(reverse('login'))
        assert not CartItem.objects.exists()


def test_empty_cart(auth_client: Client):
    url: str =  reverse('cart:cart_detail')
    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'Корзина пуста'.encode('utf-8') in response.content

def test_goods_in_cart(
    auth_client: Client,
    cart_item: CartItem
):
    url: str =  reverse('cart:cart_detail')
    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert cart_item.product.name.encode('utf-8') in response.content
    assert cart_item.product.description.encode('utf-8') in response.content
    assert cart_item in response.context['cart_items']


@pytest.mark.parametrize(
    'action, quantity',
    (
        ('increase', 3), ('decrease', 1)
    )
)
def test_change_quantity_goods_in_cart_positive(
    action: str,
    quantity: int,
    auth_client: Client,
    cart_item: CartItem
):
    url = reverse(
        'cart:quantity_item_update',
        kwargs={'item_id': cart_item.id, 'action': action}
    )
    # Начальное количество товара в корзине
    assert cart_item.quantity == 2

    response = auth_client.post(url, follow=True)
    cart_item.refresh_from_db()

    # Проверка изменения данных
    assert cart_item.quantity == quantity

    # Проверка редиректа
    expected_redirect_url = reverse('cart:cart_detail')
    assert response.redirect_chain == [(expected_redirect_url, HTTPStatus.FOUND)]



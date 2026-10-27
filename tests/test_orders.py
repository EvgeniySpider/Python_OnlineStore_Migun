from http import HTTPStatus
import pytest
from django.test import Client
from django.urls import reverse, reverse_lazy
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from orders.forms import OrderModelForm

def test_empty_orders(auth_client: Client):
    url: str = reverse('order_list')

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'У вас пока нет оформленных заказов.'.encode('utf-8') in response.content
    assert not OrderItem.objects.exists()
    assert not Order.objects.exists()
    assert not response.context['orders']


def test_order_create_success(auth_client: Client, cart_item: CartItem):
    url: str = reverse('order_create')

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.context['form'], OrderModelForm)
    assert 'Оформление заказа'.encode('utf-8') in response.content
    assert CartItem.objects.filter(pk=cart_item.pk).exists()

    # Проверка предзаполненной формы данными пользователя
    assert response.context['form'].initial['first_name'] == cart_item.cart.user.first_name
    assert response.context['form'].initial['last_name'] == cart_item.cart.user.last_name
    assert response.context['form'].initial['phone_number'] == cart_item.cart.user.phone_number
    assert response.context['form'].initial['city'] == cart_item.cart.user.city
    assert response.context['form'].initial['street'] == cart_item.cart.user.street
    assert response.context['form'].initial['house_number'] == cart_item.cart.user.house_number
    # Номера квартиры нет
    assert response.context['form'].initial['apartment_number'] is None


@pytest.mark.django_db
class TestNegativeOrderCreateButton:
    URL = reverse_lazy('order_create')
    EXPECTED_REDIRECT_URL = reverse_lazy('cart:cart_detail')

    def test_order_create_when_cart_is_alien(self, alien_auth_client: Client, cart_item: CartItem):
        """В базе есть чужая корзина с товарами, но у текущего юзера пусто."""
        response = alien_auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get('form')
        assert response.redirect_chain == [(self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)]

    def test_order_create_when_cart_does_not_exist(self, auth_client: Client):
        """У пользователя вообще нет объекта корзины."""
        response = auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get('form')
        assert response.redirect_chain == [(self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)]

    def test_order_create_when_cart_is_empty(self, auth_client: Client, user: User):
        """Корзина у пользователя создана, но в ней нет товаров."""
        Cart.objects.create(user=user)

        response = auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get('form')
        assert response.redirect_chain == [(self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)]
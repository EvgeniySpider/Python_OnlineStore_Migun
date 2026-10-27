from http import HTTPStatus
from django.test import Client
from django.urls import reverse
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


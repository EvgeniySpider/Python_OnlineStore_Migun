from http import HTTPStatus
from django.test import Client
from django.urls import reverse
from orders.models import Order, OrderItem


def test_empty_orders(auth_client: Client):
    url: str = reverse('order_list')

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'У вас пока нет оформленных заказов.'.encode('utf-8') in response.content
    assert not OrderItem.objects.exists()
    assert not Order.objects.exists()
    assert not response.context['orders']
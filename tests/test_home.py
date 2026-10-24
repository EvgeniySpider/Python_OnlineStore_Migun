from http import HTTPStatus

from django.test import Client
from django.urls import reverse

from goods.models import Product


def test_home_page_anonymous_user(client: Client, product: Product):
    url: str = reverse('home')
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert product in response.context['products']
    assert product.name.encode('utf-8') in response.content


def test_home_page_authenticated_user(auth_client: Client, product: Product):
    url: str = reverse('home')

    response = auth_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert product in response.context['products']
    assert product.name.encode('utf-8') in response.content




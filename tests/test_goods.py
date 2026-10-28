from http import HTTPStatus
import pytest

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


def test_product_detail_anonymous_user(client: Client, product: Product):
    """Анонимный пользователь может просматривать детальную страницу товара."""
    url = reverse('product_detail', kwargs={'pk': product.pk})
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert response.context['product_object'] == product

    # decode
    content = response.content.decode('utf-8')
    
    assert product.name in content
    assert product.description in content
    assert product.category.name in content
    # Ищем только целую часть цены
    assert str(int(product.price)) in content
    assert f'{product.stock.quantity} шт.' in content


def test_product_detail_authenticated_user(auth_client: Client, product: Product):
    """Авторизованный пользователь также видит детальную страницу товара."""
    url = reverse('product_detail', kwargs={'pk': product.pk})
    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert response.context['product_object'] == product

    content = response.content.decode('utf-8')
    
    assert product.name in content
    # Убеждаемся, что цена на месте
    assert str(int(product.price)) in content
    # И остаток на складе тоже
    assert f'{product.stock.quantity} шт.' in content


@pytest.mark.django_db
def test_product_detail_not_found(client: Client):
    """При запросе несуществующего товара возвращается 404."""
    url = reverse('product_detail', kwargs={'pk': 99999})
    response = client.get(url)
    
    assert response.status_code == HTTPStatus.NOT_FOUND
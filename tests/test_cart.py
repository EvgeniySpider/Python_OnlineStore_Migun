from http import HTTPStatus
import pytest
from django.test import Client
from django.urls import reverse
from cart.models import Cart, CartItem
from goods.models import Category, Product, Stock
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
    url: str = reverse(
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


@pytest.mark.parametrize(
    'action, initial_cart_quantity, stock_quantity, expected_message',
    [
        ('increase', 2, 2, 'На складе больше нет товара'),
        ('decrease', 1, 10, 'Минимальное количество товара в корзине — 1 шт.'),
    ]
)
def test_change_quantity_goods_in_cart_negative(
    action: str,
    initial_cart_quantity: int,
    stock_quantity: int,
    expected_message: str,
    auth_client: Client,
    cart_item: CartItem
):
    # Устанавливаем количество товара В КОРЗИНЕ
    cart_item.quantity = initial_cart_quantity
    cart_item.save()
    # Устанавливаем количество товара НА СКЛАДЕ
    stock = cart_item.product.stock
    stock.quantity = stock_quantity
    stock.save()

    url: str = reverse(
        'cart:quantity_item_update',
        kwargs={'item_id': cart_item.id, 'action': action}
    )

    response = auth_client.post(url, follow=True)
    cart_item.refresh_from_db()

    # Количество не должно измениться
    assert cart_item.quantity == initial_cart_quantity

    # Проверка предупреждения
    messages = list(response.context['messages'])
    assert expected_message in str(messages[0])


    # Проверка редиректа
    assert response.redirect_chain == [(reverse('cart:cart_detail'), HTTPStatus.FOUND)]


def test_delete_cart_success(auth_client: Client, cart_item: CartItem):
    url: str = reverse('cart:cart_item_delete',  kwargs={'item_id': cart_item.id})

    response = auth_client.post(url, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert 'Корзина пуста 🛒'.encode('utf-8') in response.content
    assert not response.context.get('cart_items', [])
    assert response.redirect_chain == [(reverse('cart:cart_detail'), HTTPStatus.FOUND)]
    assert not CartItem.objects.filter(pk=cart_item.pk).exists()


@pytest.mark.parametrize('use_existing_item, should_exist_in_db', [
    (True, True),    # Чужой товар: получаем 404, товар в БД НЕ удаляется
    (False, False),  # Несуществующий id: получаем 404, в БД такого товара как не было, так и нет
])
def test_delete_cart_negative(
    use_existing_item: bool,
    should_exist_in_db: bool,
    alien_auth_client: Client,
    cart_item: CartItem
):
    target_id = cart_item.id if use_existing_item else 99999

    url = reverse('cart:cart_item_delete', kwargs={'item_id': target_id})
    response = alien_auth_client.post(url)

    # Вьюха отдаёт 404 и не пускает чужака
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Проверяем состояние в базе данных
    assert CartItem.objects.filter(pk=target_id).exists() is should_exist_in_db


@pytest.mark.parametrize(
    'url_name, kwargs',
    [
        ('cart:cart_item_delete', {}),
        ('cart:quantity_item_update', {'action': 'increase'}),
        ('cart:quantity_item_update', {'action': 'decrease'}),
    ]
)
def test_anonymous_user_cannot_modify_cart_items(
    url_name: str,
    kwargs: dict,
    client: Client,
    cart_item: CartItem
):
    """Анонимный пользователь при попытке изменить/удалить товар редиректится на логин."""
    # Подставляем реальный item_id в параметры маршрута
    kwargs['item_id'] = cart_item.id
    target_url: str = reverse(url_name, kwargs=kwargs)

    # Делаем POST от неавторизованного клиента
    response = client.post(target_url)

    # Проверяем редирект на страницу входа с параметром ?next=
    expected_redirect_url = f"{reverse('login')}?next={target_url}"
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers['Location'] == expected_redirect_url

    # Проверяем, что в базе ничего не изменилось и не удалилось
    cart_item.refresh_from_db()
    assert cart_item.quantity == 2


@pytest.mark.django_db
def test_cart_context_processor_anonymous_user(client: Client):
    """Для неавторизованного пользователя счётчик корзины в шапке равен 0."""
    response = client.get(reverse('home'))
    assert response.status_code == HTTPStatus.OK
    
    # 1. Проверяем значение переменной в контексте шаблона
    assert response.context['cart_total_quantity'] == 0
    
    # 2. Проверяем отображение в шапке base.html
    assert '🛒 Корзина (0)' in response.content.decode('utf-8')


def test_cart_context_processor_empty_cart_authenticated(auth_client: Client):
    """Для авторизованного пользователя с пустой корзиной счётчик равен 0."""
    response = auth_client.get(reverse('home'))
    assert response.status_code == HTTPStatus.OK

    assert response.context['cart_total_quantity'] == 0
    assert '🛒 Корзина (0)' in response.content.decode('utf-8')


def test_cart_context_processor_sums_multiple_items(
    auth_client: Client,
    user: User,
    category: Category
):
    """Счётчик в шапке корректно суммирует количество нескольких разных товаров."""
    cart = Cart.objects.create(user=user)

    # Создаём 2 разных товара
    product_1 = Product.objects.create(
        name='Клавиатура', price=3000.00, category=category
    )
    Stock.objects.create(product=product_1, quantity=10)

    product_2 = Product.objects.create(
        name='Мышь', price=1500.00, category=category
    )
    Stock.objects.create(product=product_2, quantity=10)

    # Кладём в корзину: 2 клавиатуры и 3 мыши (в сумме 5 шт.)
    CartItem.objects.create(cart=cart, product=product_1, quantity=2)
    CartItem.objects.create(cart=cart, product=product_2, quantity=3)

    # Запрашиваем любую страницу (например, главную)
    response = auth_client.get(reverse('home'))
    assert response.status_code == HTTPStatus.OK

    # Проверяем сумму: 2 + 3 = 5
    assert response.context['cart_total_quantity'] == 5
    assert '🛒 Корзина (5)' in response.content.decode('utf-8')
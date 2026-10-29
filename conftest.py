from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from cart.models import Cart, CartItem
from goods.models import Category, Product, Stock
from orders.models import Order, OrderItem
from users.models import User

# ==========================================
# 1. ПОЛЬЗОВАТЕЛИ И КЛИЕНТ
# ==========================================


@pytest.fixture
def user(db) -> User:
    """Обычный пользователь с заполненным профилем"""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
        first_name="Иван",
        last_name="Иванов",
        phone_number="+79991112233",
        city="Москва",
        street="Ленина",
        house_number="10",
    )


@pytest.fixture
def auth_client(client: Client, user: User) -> Client:
    """Тестовый клиент Django, уже залогиненный под пользователем"""
    client.force_login(user)
    return client


@pytest.fixture
def alien_user(db) -> User:
    """Обычный пользователь с заполненным профилем"""
    return User.objects.create_user(
        username="alien_testuser",
        email="alien_test@example.com",
        password="password123",
        first_name="Иван",
        last_name="Иванов",
        phone_number="+79991112234",
        city="Москва",
        street="Ленина",
        house_number="10",
    )


@pytest.fixture
def alien_auth_client(client: Client, alien_user: User) -> Client:
    """Тестовый клиент Django, уже залогиненный под пользователем"""
    client.force_login(alien_user)
    return client


# ==========================================
# 2. ТОВАРЫ И СКЛАД
# ==========================================


@pytest.fixture
def category(db):
    """Категория товаров"""
    return Category.objects.create(name="Электроника")


@pytest.fixture
def product(category: Category) -> Product:
    """Товар с привязанной категорией и количеством на складе"""
    prod = Product.objects.create(
        name="Ноутбук MSI",
        description="Игровой ноутбук",
        price=75000.00,
        category=category,
    )
    Stock.objects.create(product=prod, quantity=10)
    return prod


@pytest.fixture
def stock(product: Product) -> Stock:
    """Складской остаток (10 шт.) для товара"""
    return product.stock


# ==========================================
# 3. КОРЗИНА
# ==========================================


@pytest.fixture
def cart(user: User) -> Cart:
    """Корзина пользователя"""
    return Cart.objects.create(user=user)


@pytest.fixture
def cart_item(cart: Cart, product: Product) -> CartItem:
    """Элемент в корзине (2 шт. ноутбука)"""
    return CartItem.objects.create(cart=cart, product=product, quantity=2)


@pytest.fixture
def created_order(user: User, product: Product) -> Order:
    order = Order.objects.create(
        user=user,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        city=user.city,
        street=user.street,
        house_number=user.house_number,
    )

    OrderItem.objects.create(
        order=order, product=product, price=product.price, quantity=2
    )

    return order


@pytest.fixture
def product_with_image(category: Category, tmp_path, settings) -> Product:
    """Товар с реальным изображением, изолированным во временной папке tmp_path."""
    # 1. СНАЧАЛА перенаправляем MEDIA_ROOT во временную папку pytest
    settings.MEDIA_ROOT = tmp_path

    # 2. Создаем виртуальный байтовый буфер в RAM
    image_buffer = BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    uploaded_image = SimpleUploadedFile(
        name="test_product.png", content=image_buffer.read(), content_type="image/png"
    )

    # 3. Файл запишется в tmp_path, а не в реальную папку media/
    prod = Product.objects.create(
        name="Смартфон с фото",
        description="Классный телефон",
        price=50000.00,
        category=category,
        image=uploaded_image,
    )
    Stock.objects.create(product=prod, quantity=5)
    return prod

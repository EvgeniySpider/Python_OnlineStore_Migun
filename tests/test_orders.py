from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse, reverse_lazy

from cart.models import Cart, CartItem
from goods.models import Stock
from orders.forms import OrderModelForm
from orders.models import Order, OrderItem
from orders.services import create_order
from users.models import User


def _form_data(user: User, apartment_number: str = "42") -> dict:
    """Валидные данные формы заказа для пользователя.

    Точка переопределения: через ключи возвращаемого словаря можно
    подменить любое поле (например, сделать форму неполной).
    """
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "city": user.city,
        "street": user.street,
        "house_number": user.house_number,
        "apartment_number": apartment_number,
    }


def test_empty_orders(auth_client: Client):
    url: str = reverse("order_list")

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert "У вас пока нет оформленных заказов.".encode() in response.content
    assert not OrderItem.objects.exists()
    assert not Order.objects.exists()
    assert not response.context["orders"]


def test_order_create_success(auth_client: Client, cart_item: CartItem):
    url: str = reverse("order_create")

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.context["form"], OrderModelForm)
    assert "Оформление заказа".encode() in response.content
    assert CartItem.objects.filter(pk=cart_item.pk).exists()

    # Проверка предзаполненной формы данными пользователя
    assert (
        response.context["form"].initial["first_name"] == cart_item.cart.user.first_name
    )
    assert (
        response.context["form"].initial["last_name"] == cart_item.cart.user.last_name
    )
    assert (
        response.context["form"].initial["phone_number"]
        == cart_item.cart.user.phone_number
    )
    assert response.context["form"].initial["city"] == cart_item.cart.user.city
    assert response.context["form"].initial["street"] == cart_item.cart.user.street
    assert (
        response.context["form"].initial["house_number"]
        == cart_item.cart.user.house_number
    )
    # Номера квартиры нет
    assert response.context["form"].initial["apartment_number"] is None


@pytest.mark.django_db
class TestNegativeOrderCreateButton:
    URL = reverse_lazy("order_create")
    EXPECTED_REDIRECT_URL = reverse_lazy("cart:cart_detail")

    def test_order_create_when_cart_is_alien(
        self, alien_auth_client: Client, cart_item: CartItem
    ):
        """В базе есть чужая корзина с товарами, но у текущего юзера пусто."""
        response = alien_auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get("form")
        assert response.redirect_chain == [
            (self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)
        ]

    def test_order_create_when_cart_does_not_exist(self, auth_client: Client):
        """У пользователя вообще нет объекта корзины."""
        response = auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get("form")
        assert response.redirect_chain == [
            (self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)
        ]

    def test_order_create_when_cart_is_empty(self, auth_client: Client, user: User):
        """Корзина у пользователя создана, но в ней нет товаров."""
        Cart.objects.create(user=user)

        response = auth_client.get(self.URL, follow=True)

        assert response.status_code == HTTPStatus.OK
        assert not response.context.get("form")
        assert response.redirect_chain == [
            (self.EXPECTED_REDIRECT_URL, HTTPStatus.FOUND)
        ]


@pytest.mark.parametrize(
    "apartment_number, expected_apartment",
    [
        ("42", "42"),  # Заказ в квартиру
        ("", None),  # Заказ в частный дом (пустая строка в форме)
    ],
)
def test_confirm_order_success(
    apartment_number: str,
    expected_apartment: str,
    auth_client: Client,
    cart_item: CartItem,
    stock: Stock,
):
    url: str = reverse("order_create")
    user = cart_item.cart.user

    initial_stock_quantity = stock.quantity
    ordered_quantity = cart_item.quantity
    expected_price = cart_item.product.price

    form_data = _form_data(user, apartment_number=apartment_number)

    response = auth_client.post(url, data=form_data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(reverse("home"), HTTPStatus.FOUND)]

    # 1. Проверяем Order
    order = Order.objects.get(user=user)
    assert order.status == "created"
    assert order.phone_number == user.phone_number
    assert order.apartment_number == expected_apartment

    # 2. Проверяем OrderItem
    order_item = order.items.first()
    assert order_item.product == cart_item.product
    assert order_item.quantity == ordered_quantity
    assert order_item.price == expected_price

    # 3. Проверяем списание со склада
    stock.refresh_from_db()
    assert stock.quantity == initial_stock_quantity - ordered_quantity

    # 4. Проверяем очистку корзины
    assert not CartItem.objects.filter(cart__user=user).exists()

    # 5. Проверяем сообщение
    messages = list(response.context["messages"])
    assert "Заказ успешно оформлен" in str(messages[0])


@pytest.mark.django_db
class TestConfirmOrderNegativeScenarios:
    URL = reverse_lazy("order_create")
    EXPECTED_REDIRECT_URL = reverse_lazy("cart:cart_detail")

    @pytest.mark.parametrize(
        "key",
        ("first_name", "last_name", "phone_number", "city", "street", "house_number"),
    )
    def test_confirm_order_send_incomplete_form(
        self,
        key: str,
        auth_client: Client,
        cart_item: CartItem,
    ):

        user = cart_item.cart.user
        # Берём валидную форму и удаляем одно обязательное поле
        form_data = _form_data(user)
        del form_data[key]

        response = auth_client.post(self.URL, data=form_data)

        assert response.status_code == HTTPStatus.OK
        assert not Order.objects.exists()
        assert CartItem.objects.filter(pk=cart_item.pk).exists()
        assert key in response.context["form"].errors
        assert "Оформление заказа".encode() in response.content

        messages = list(response.context["messages"])
        assert "Пожалуйста, исправьте ошибки в форме" in str(messages[0])

    def test_confirm_order_when_goods_isnt_enough(
        self, auth_client: Client, cart_item: CartItem
    ):
        user = cart_item.cart.user
        form_data = _form_data(user)

        # В корзине 2 шт, а на складе оставляем только 1 шт.
        stock = Stock.objects.get(pk=cart_item.product.id)
        stock.quantity = 1
        stock.save()

        response = auth_client.post(self.URL, data=form_data)

        assert response.status_code == HTTPStatus.OK
        assert not Order.objects.exists()

        # Корзина осталась нетронутой
        assert CartItem.objects.filter(pk=cart_item.pk).exists()

        # На складе ничего не списалось
        stock.refresh_from_db()
        assert stock.quantity == 1

        # Ошибка в форме (non-field errors)
        assert "__all__" in response.context["form"].errors
        error_message = response.context["form"].errors["__all__"][0]
        assert "Недостаточно товара" in error_message
        assert "Доступно: 1 шт." in error_message

        # Сообщение пользователю
        messages = list(response.context["messages"])
        assert "Заказ не был оформлен" in str(messages[0])


@pytest.mark.django_db
class TestOrderCancel:
    def test_cancel_order_success(
        self, auth_client: Client, created_order: Order, stock: Stock
    ):
        """Успешная отмена заказа: статус меняется на canceled, товары возвращаются на склад."""
        url: str = reverse("order_cancel", kwargs={"order_id": created_order.id})
        assert created_order.status == "created"

        initial_stock = stock.quantity
        ordered_quantity = created_order.items.first().quantity

        response = auth_client.post(url, follow=True)
        created_order.refresh_from_db()
        stock.refresh_from_db()

        assert response.status_code == HTTPStatus.OK
        assert created_order.status == "canceled"
        # Товары вернулись на склад
        assert stock.quantity == initial_stock + ordered_quantity
        # Редирект в список заказов
        assert response.redirect_chain == [(reverse("order_list"), HTTPStatus.FOUND)]
        # Сообщение об успехе
        messages = list(response.context["messages"])
        assert "успешно отменён, товары возвращены на склад" in str(messages[0])

    @pytest.mark.parametrize(
        "status, expected_message",
        [
            ("in_progress", "уже передан в обработку и не может быть отменён"),
            ("completed", "нельзя отменить"),
        ],
    )
    def test_cancel_order_invalid_status_negative(
        self,
        status: str,
        expected_message: str,
        auth_client: Client,
        created_order: Order,
        stock: Stock,
    ):
        """Нельзя отменить заказ со статусами in_progress или completed."""
        # Меняем статус заказа перед попыткой отмены
        created_order.status = status
        created_order.save()

        initial_stock = stock.quantity
        url: str = reverse("order_cancel", kwargs={"order_id": created_order.id})

        response = auth_client.post(url, follow=True)
        created_order.refresh_from_db()
        stock.refresh_from_db()

        # Статус не должен измениться
        assert created_order.status == status
        # Склад не должен измениться (товары не возвращаются)
        assert stock.quantity == initial_stock
        # Редирект в список заказов
        assert response.redirect_chain == [(reverse("order_list"), HTTPStatus.FOUND)]
        # Проверяем сообщение пользователю
        messages = list(response.context["messages"])
        assert expected_message in str(messages[0])

    def test_cancel_alien_order_forbidden_negative(
        self, alien_auth_client: Client, created_order: Order, stock: Stock
    ):
        """Попытка отменить чужой заказ возвращает 404 (защита от IDOR)."""
        url: str = reverse("order_cancel", kwargs={"order_id": created_order.id})
        initial_stock = stock.quantity

        # Запрос делает сторонний пользователь
        response = alien_auth_client.post(url)

        # get_object_or_404(Order, id=order_id, user=request.user) даёт 404
        assert response.status_code == HTTPStatus.NOT_FOUND

        created_order.refresh_from_db()
        stock.refresh_from_db()

        # Данные заказа и склада не пострадали
        assert created_order.status == "created"
        assert stock.quantity == initial_stock


@pytest.mark.django_db
class TestCreateOrderService:
    def test_create_order_success(self, user: User, cart_item: CartItem, stock: Stock):
        """Успешное оформление: заказ создан, склад списан, корзина очищена."""
        initial_stock_quantity = stock.quantity
        ordered_quantity = cart_item.quantity

        order, errors = create_order(user=user, form_data=_form_data(user))

        assert not errors
        assert order is not None
        assert order.user == user
        assert order.status == Order.Status.CREATED

        # Товар зафиксирован в заказе по цене на момент покупки
        order_item = order.items.first()
        assert order_item.product == cart_item.product
        assert order_item.quantity == ordered_quantity
        assert order_item.price == cart_item.product.price

        # Склад списан
        stock.refresh_from_db()
        assert stock.quantity == initial_stock_quantity - ordered_quantity

        # Корзина очищена
        assert not CartItem.objects.filter(cart_id=user.id).exists()

    def test_create_order_with_empty_cart(self, user: User):
        """Пустая корзина: сервис сообщает об этом, ничего не создавая."""
        Cart.objects.create(user=user)

        order, errors = create_order(user=user, form_data=_form_data(user))

        assert order is None
        assert errors == []
        assert not Order.objects.exists()

    def test_create_order_with_no_cart_at_all(self, user: User):
        """У пользователя вообще нет корзины — поведение как с пустой корзиной."""
        order, errors = create_order(user=user, form_data=_form_data(user))

        assert order is None
        assert errors == []
        assert not Order.objects.exists()

    def test_create_order_with_insufficient_stock(
        self, user: User, cart_item: CartItem, stock: Stock
    ):
        """Товара на складе меньше, чем в корзине — заказ не создаётся."""
        stock.quantity = 1  # В корзине 2 шт.
        stock.save()

        order, errors = create_order(user=user, form_data=_form_data(user))

        assert order is None
        assert len(errors) == 1
        assert "Недостаточно товара" in errors[0]
        assert "Доступно: 1 шт." in errors[0]

        # Ничего не изменилось: заказ не создан, склад и корзина целы
        assert not Order.objects.exists()
        stock.refresh_from_db()
        assert stock.quantity == 1
        assert CartItem.objects.filter(pk=cart_item.pk).exists()

    def test_create_order_with_product_missing_on_stock(
        self, user: User, cart_item: CartItem, stock: Stock
    ):
        """Товар есть в корзине, но записи на складе нет — заказ не создаётся."""
        product = cart_item.product
        Stock.objects.filter(product=product).delete()

        order, errors = create_order(user=user, form_data=_form_data(user))

        assert order is None
        assert len(errors) == 1
        assert f"Товар {product.name} отсутствует на складе." in errors[0]

        # Ничего не изменилось
        assert not Order.objects.exists()
        assert CartItem.objects.filter(pk=cart_item.pk).exists()

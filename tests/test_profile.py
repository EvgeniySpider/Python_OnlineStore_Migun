from http import HTTPStatus
from django.test import Client
from django.urls import reverse
import pytest
from users.forms import UserDataForm
from users.models import User


def test_profile(auth_client: Client, user: User):
    url: str = reverse('user_profile')

    response = auth_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.context['form'], UserDataForm)
    assert 'Ваши персональные данные'.encode('utf-8') in response.content

    # Проверка предзаполненной формы данными пользователя
    form_initial = response.context['form'].initial
    assert form_initial['first_name'] == user.first_name
    assert form_initial['last_name'] == user.last_name
    assert form_initial['email'] == user.email
    assert form_initial['phone_number'] == user.phone_number
    assert form_initial['city'] == user.city
    assert form_initial['street'] == user.street
    assert form_initial['house_number'] == user.house_number
    # Необязательные незаполненные поля
    assert form_initial['patronymic'] is None
    assert form_initial['apartment_number'] is None


def test_success_change_user_data_in_profile(auth_client: Client, user: User):
    url: str = reverse('user_profile')

    first_name, last_name = 'Вася', 'Пупкин'
    phone_number = '+7(952)999-10-10'
    city = 'Пномпень'
    street = 'Khum Trapeang Kong'
    house_number = '10'
    apartment_number = '10'

    form_data = {
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'city': city,
        'street': street,
        'house_number': house_number,
        'apartment_number': apartment_number,
    }

    response = auth_client.post(url, data=form_data, follow=True)
    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(url, HTTPStatus.FOUND)]

    user.refresh_from_db()
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.phone_number == '+79529991010'
    assert user.city == city
    assert user.street == street
    assert user.house_number == house_number
    assert user.apartment_number == apartment_number

    messages = list(response.context['messages'])
    assert 'Данные в профиле успешно обновлены!' in str(messages[0])


@pytest.mark.parametrize('invalid_field, invalid_value, expected_error', [
    ('phone_number', 'invalid-phone-abc', 'Номер телефона должен содержать только цифры'),
    ('apartment_number', 'flat_abc', 'Номер квартиры/офиса должен состоять только из цифр'),
    ('email', 'not-an-email', 'Введите правильный адрес электронной почты'),
])
def test_profile_invalid_fields_negative(
    invalid_field: str,
    invalid_value: str,
    expected_error: str,
    auth_client: Client,
    user: User
):
    url = reverse('user_profile')
    old_phone = user.phone_number

    form_data = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'city': user.city,
        'street': user.street,
        'house_number': user.house_number,
        'email': user.email,
    }
    # Подменяем валидное поле на недопустимое значение с буквами
    form_data[invalid_field] = invalid_value

    response = auth_client.post(url, data=form_data)

    # 1. Форма не валидна, страница перерисовывается (200 OK)
    assert response.status_code == HTTPStatus.OK
    
    # 2. Ошибка привязана к конкретному полю
    assert invalid_field in response.context['form'].errors
    assert expected_error in response.context['form'].errors[invalid_field][0]

    # 3. Данные в базе НЕ изменились
    user.refresh_from_db()
    assert user.phone_number == old_phone
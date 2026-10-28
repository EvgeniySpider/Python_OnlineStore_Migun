from http import HTTPStatus
from django.test import Client
from django.urls import reverse
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
    phone_number = '+79529991010'
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
    assert user.phone_number == phone_number
    assert user.city == city
    assert user.street == street
    assert user.house_number == house_number
    assert user.apartment_number == apartment_number

    messages = list(response.context['messages'])
    assert 'Данные в профиле успешно обновлены!' in str(messages[0])
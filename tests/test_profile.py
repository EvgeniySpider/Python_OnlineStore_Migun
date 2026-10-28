from http import HTTPStatus
from django.test import Client
from django.urls import reverse
from users.models import User


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
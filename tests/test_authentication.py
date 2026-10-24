from http import HTTPStatus

from django.test import Client
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from users.forms import CustomUserCreationForm
import pytest

from users.models import User


def test_login_page_get(client: Client):
    url: str = reverse('login')

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'Вход в аккаунт'.encode('utf-8') in response.content
    assert 'Имя пользователя'.encode('utf-8') in response.content
    assert 'Пароль'.encode('utf-8') in response.content
    assert isinstance(response.context['form'], AuthenticationForm)

    form: AuthenticationForm = response.context['form']
    assert set(form.fields.keys()) == {'username', 'password'}


def test_registration_page_get(client: Client):
    url: str = reverse('register')

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'Регистрация нового пользователя'.encode('utf-8') in response.content
    assert 'Адрес электронной почты'.encode('utf-8') in response.content
    assert 'Имя пользователя'.encode('utf-8') in response.content
    assert 'Пароль'.encode('utf-8') in response.content
    assert 'Подтверждение пароля'.encode('utf-8') in response.content
    assert isinstance(response.context['form'], CustomUserCreationForm)

    form: CustomUserCreationForm = response.context['form']
    assert set(form.fields.keys()) == {'username', 'email', 'first_name', 'last_name', 'password1', 'password2'}
    

@pytest.mark.django_db
def test_success_registration(client: Client):
    url: str = reverse('register')
    data = {
        'username': 'user',
        'email': 'user@gmail.com',
        'first_name': 'Ivan',
        'last_name': 'Ivanov',
        'password1': '123456789abcdef',
        'password2': '123456789abcdef'
    }

    response = client.post(url, data=data)

    user = User.objects.get(username='user')
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers['Location'] == reverse('login')
    assert user.check_password('123456789abcdef')


def test_success_login(client: Client, user: User):
    url: str = reverse('login')
    data = {'username': user.username, 'password': 'password123'}

    response = client.post(url, data=data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(reverse('home'), HTTPStatus.FOUND)]
    assert f'Привет, {user.username}!'.encode('utf-8') in response.content
    assert response.context['user'].is_authenticated

    


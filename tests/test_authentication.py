from http import HTTPStatus

from django.test import Client
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from users.forms import CustomUserCreationForm


def test_login(client: Client):
    url: str = reverse('login')

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert 'Вход в аккаунт'.encode('utf-8') in response.content
    assert 'Имя пользователя'.encode('utf-8') in response.content
    assert 'Пароль'.encode('utf-8') in response.content
    assert isinstance(response.context['form'], AuthenticationForm)

    form: AuthenticationForm = response.context['form']
    assert set(form.fields.keys()) == {'username', 'password'}

    

def test_registration(client: Client):
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


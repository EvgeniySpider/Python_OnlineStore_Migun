from http import HTTPStatus

from django.test import Client
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from pytest_django.asserts import assertRedirects
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
@pytest.mark.parametrize(
    'form_data, expected_first_name, expected_last_name, expected_email',
    [
        (
            {
                'username': 'user_full',
                'email': 'user@gmail.com',
                'first_name': 'Ivan',
                'last_name': 'Ivanov',
                'password1': '123456789abcdef',
                'password2': '123456789abcdef',
            },
            'Ivan',
            'Ivanov',
            'user@gmail.com',
        ),
        (
            {
                'username': 'user_minimal',
                'email': '',
                'first_name': '',
                'last_name': '',
                'password1': '123456789abcdef',
                'password2': '123456789abcdef',
            },
            '',
            '',
            '',
        ),
    ],
)
def test_success_registration(
    client: Client,
    form_data: dict[str, str],
    expected_first_name: str,
    expected_last_name: str,
    expected_email: str,
):
    url: str = reverse('register')

    response = client.post(url, data=form_data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(reverse('home'), HTTPStatus.FOUND)]

    user = User.objects.get(username=form_data['username'])
    assert user.first_name == expected_first_name
    assert user.last_name == expected_last_name
    assert user.email == expected_email
    assert user.check_password(form_data['password1'])

    # Проверка, что после регистрации пользователь авторизован и отображается приветствие:
    assert response.context['user'].is_authenticated
    assert f'Привет, {user.username}!'.encode('utf-8') in response.content


def test_success_login(client: Client, user: User):
    url: str = reverse('login')
    data = {'username': user.username, 'password': 'password123'}

    response = client.post(url, data=data, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.redirect_chain == [(reverse('home'), HTTPStatus.FOUND)]
    assert f'Привет, {user.username}!'.encode('utf-8') in response.content
    assert response.context['user'].is_authenticated


@pytest.mark.django_db
@pytest.mark.parametrize(
    'key, value, expected_error_field',
    (
        ('username', '', 'username'),
        ('password1', 'incorrect_password', 'password2'),
        ('password2', 'incorrect_password', 'password2'),
    )
)
def test_unsuccessful_registration(
    client: Client,
    key: str,
    value: str,
    expected_error_field: str,
):
    url: str = reverse('register')
    data = {
        'username': 'user',
        'email': 'user@gmail.com',
        'first_name': 'Ivan',
        'last_name': 'Ivanov',
        'password1': '123456789abcdef',
        'password2': '123456789abcdef',
    }
    data[key] = value

    response = client.post(url, data=data)

    assert response.status_code == HTTPStatus.OK
    assert not User.objects.filter(username='user').exists()
    assert expected_error_field in response.context['form'].errors


def test_logout(auth_client: Client):
    url: str = reverse('logout')

    response = auth_client.post(url, follow=True)

    assert response.status_code == HTTPStatus.OK
    assert not response.context['user'].is_authenticated
    assert 'Регистрация'.encode('utf-8') in response.content
    assert response.redirect_chain == [(reverse('home'), HTTPStatus.FOUND)]


@pytest.mark.parametrize(
    'username, password', (
        ('testuser', 'unexist_password'),
        ('unexist_username', 'password123'),
        ('unexist_username', 'unexist_password'),
    )
)
def test_unsuccessful_login(
    username: str,
    password: str,
    client: Client,
    user: User
):
    url: str = reverse('login')
    data = {'username': username, 'password': password}
    
    response = client.post(url, data=data)

    assert response.status_code == HTTPStatus.OK
    assert not response.context['user'].is_authenticated
    assert '__all__' in response.context['form'].errors


def test_authenticated_client_login_and_register(auth_client: Client):
    url_login = reverse('login')
    url_register = reverse('register')
    expected_url = reverse('home')

    # Проверка для логина
    response_login = auth_client.get(url_login)
    assertRedirects(response_login, expected_url)

    # Проверка для регистрации
    response_register = auth_client.get(url_register)
    assertRedirects(response_register, expected_url)

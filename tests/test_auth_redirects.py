from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.parametrize(
    "view_name",
    [
        "cart:cart_detail",
        "user_profile",
        "order_list",
    ],
)
def test_anonymous_user_redirected_to_login(client: Client, view_name: str):
    target_url = reverse(view_name)
    response = client.get(target_url)

    expected_url = f"{reverse('login')}?next={target_url}"
    assert response.status_code == HTTPStatus.FOUND
    assert response.headers["Location"] == expected_url

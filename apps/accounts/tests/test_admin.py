import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def admin_client(client, db):
    admin = User.objects.create_superuser(
        email="admin@example.com", password="pw-Admin-123", handle="site_owner", name="Owner"
    )
    client.force_login(admin)
    return client


def test_admin_can_create_user(admin_client):
    response = admin_client.post(
        reverse("admin:accounts_user_add"),
        {
            "email": "New@Example.com",
            "handle": "New_Lawyer",
            "name": "New Lawyer",
            "usable_password": "true",
            "password1": "a-Strong-pass-123",
            "password2": "a-Strong-pass-123",
        },
    )
    assert response.status_code == 302
    created = User.objects.get(email="new@example.com")
    assert created.handle == "new_lawyer"


@pytest.mark.parametrize("url", ["admin:accounts_user_changelist", "admin:accounts_user_add"])
def test_admin_pages_render(admin_client, url):
    assert admin_client.get(reverse(url)).status_code == 200

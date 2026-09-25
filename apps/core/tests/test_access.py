import pytest
from django.urls import reverse

from apps.core.templatetags.core_tags import initials

PUBLIC = ["home", "lawyers:signup", "accounts:login", "accounts:password_reset"]
PRIVATE = ["lawyers:profile_edit", "lawyers:bar_admissions", "accounts:password_change"]


@pytest.mark.parametrize("name", PUBLIC)
def test_public_pages_open_to_anonymous(client, db, name):
    assert client.get(reverse(name)).status_code == 200


@pytest.mark.parametrize("name", PRIVATE)
def test_everything_else_requires_login(client, db, name):
    response = client.get(reverse(name))
    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_admin_keeps_its_own_login(client, db):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response.url.startswith("/admin/login/")


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Ayesha Siddiqui", "AS"), ("Muhammad Ali Khan", "MA"), ("Farid", "F"), ("", "?")],
)
def test_initials(name, expected):
    assert initials(name) == expected

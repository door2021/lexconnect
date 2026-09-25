from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


def make_user():
    return User.objects.create_user(
        email="farid@example.com", password="Correct-Horse-42", handle="farid", name="Farid"
    )


def test_login_with_mixed_case_email(client, db):
    user = make_user()
    response = client.post(
        reverse("accounts:login"),
        {"username": "FARID@Example.com", "password": "Correct-Horse-42"},
    )
    assert response.status_code == 302
    assert client.get(reverse("home")).context["user"] == user


def test_logout_requires_post(client, db):
    client.force_login(make_user())
    assert client.get(reverse("accounts:logout")).status_code == 405
    assert client.post(reverse("accounts:logout")).status_code == 302


def test_home_renders_for_anonymous_and_staff_without_profile(client, db):
    assert client.get(reverse("home")).status_code == 200
    staff = User.objects.create_superuser(
        email="admin@example.com", password="Correct-Horse-42", handle="site_owner", name="Owner"
    )
    client.force_login(staff)
    assert client.get(reverse("home")).status_code == 200


def test_base_template_loads_tailwind_htmx_and_csrf_header(client, db):
    html = client.get(reverse("home")).content.decode()
    assert "css/tailwind.css" in html
    assert "htmx" in html
    assert "X-CSRFToken" in html

import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

User = get_user_model()
OLD, NEW = "Correct-Horse-42", "Brand-New-Pass-77"


def make_user():
    return User.objects.create_user(
        email="farid@example.com", password=OLD, handle="farid", name="Farid"
    )


def test_full_password_reset_flow(client, db):
    user = make_user()
    client.post(reverse("accounts:password_reset"), {"email": "FARID@example.com"})
    assert len(mail.outbox) == 1
    link = re.search(r"http://testserver(\S+)", mail.outbox[0].body).group(1)

    form_page = client.get(link, follow=True)
    set_url = form_page.redirect_chain[-1][0]
    client.post(set_url, {"new_password1": NEW, "new_password2": NEW})

    user.refresh_from_db()
    assert user.check_password(NEW)


def test_unknown_email_looks_identical_and_sends_nothing(client, db):
    response = client.post(reverse("accounts:password_reset"), {"email": "nobody@example.com"})
    assert response.url == reverse("accounts:password_reset_done")
    assert mail.outbox == []


def test_invalid_reset_link_shows_message(client, db):
    response = client.get("/accounts/password/reset/MQ/bad-token/", follow=True)
    assert b"invalid or has already been used" in response.content


def test_password_change_requires_login_then_works(client, db):
    url = reverse("accounts:password_change")
    assert client.get(url).status_code == 302
    user = make_user()
    client.force_login(user)
    client.post(url, {"old_password": OLD, "new_password1": NEW, "new_password2": NEW})
    user.refresh_from_db()
    assert user.check_password(NEW)

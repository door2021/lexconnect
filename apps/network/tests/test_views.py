import pytest
from django.urls import reverse

from apps.network.models import ConnectionRequest
from apps.network.services import are_connected, send_request


@pytest.fixture
def ayesha(make_lawyer):
    return make_lawyer("ayesha", name="Ayesha Siddiqui")


def test_connect_without_js_redirects_to_safe_next(client, me, ayesha):
    response = client.post(
        reverse("network:connect", args=["ayesha"]), {"next": "/network/search/?q=a"}
    )
    assert response.status_code == 302
    assert response.url == "/network/search/?q=a"
    assert ConnectionRequest.objects.filter(sender=me, recipient=ayesha).exists()


def test_unsafe_next_is_ignored(client, me, ayesha):
    response = client.post(
        reverse("network:connect", args=["ayesha"]), {"next": "https://evil.example.com/"}
    )
    assert response.url == reverse("lawyers:profile", args=["ayesha"])


def test_htmx_returns_button_fragment_and_oob_count(client, me, ayesha):
    send_request(sender=ayesha, recipient=me)
    response = client.post(
        reverse("network:accept", args=["ayesha"]), headers={"HX-Request": "true"}
    )
    html = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in html
    assert "Connected" in html
    assert 'id="request-count" hx-swap-oob="true"' in html
    assert are_connected(me, ayesha)


def test_action_errors_are_shown_not_crashes(client, me, ayesha):
    response = client.post(
        reverse("network:accept", args=["ayesha"]), headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    assert "no pending request" in response.content.decode()


def test_actions_require_post_and_unknown_handles_404(client, me, ayesha):
    assert client.get(reverse("network:connect", args=["ayesha"])).status_code == 405
    assert client.post(reverse("network:connect", args=["nobody_here"])).status_code == 404


def test_navbar_shows_pending_request_count(client, me, make_lawyer):
    for handle in ("ayesha", "bilal"):
        send_request(sender=make_lawyer(handle), recipient=me)
    html = client.get(reverse("network:index")).content.decode()
    assert '<span id="request-count"' in html
    assert ">2</span>" in html.replace("\n", "").replace(" ", "")


def test_profile_page_shows_connect_button_but_not_on_own_profile(client, me, ayesha):
    assert b'action="/network/@ayesha/connect/"' in client.get("/@ayesha/").content
    assert b"/connect/" not in client.get("/@farid/").content


def test_staff_without_profile_gets_404_on_network_pages(client, django_user_model, db):
    staff = django_user_model.objects.create_superuser(
        email="admin@example.com", password="Correct-Horse-42", handle="site_owner", name="Owner"
    )
    client.force_login(staff)
    assert client.get(reverse("network:search")).status_code == 404
    assert client.get(reverse("home")).status_code == 200

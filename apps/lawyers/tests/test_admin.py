import pytest
from django.urls import reverse

from apps.lawyers.models import BarAdmission, Jurisdiction
from apps.lawyers.services import register_lawyer


@pytest.fixture
def staff_client(client, django_user_model, db):
    admin = django_user_model.objects.create_superuser(
        email="admin@example.com", password="pw-Admin-123", handle="reviewer", name="Reviewer"
    )
    client.force_login(admin)
    return client


def test_admin_approve_action_and_competing_claims(staff_client):
    kp = Jurisdiction.objects.get(code="pk-kp")
    for n in (1, 2):
        register_lawyer(
            email=f"l{n}@example.com",
            password="a-Strong-pass-123",
            handle=f"lawyer_{n}",
            name=f"Lawyer {n}",
            jurisdiction=kp,
            license_number="KP-9",
        )
    url = reverse("admin:lawyers_baradmission_changelist")
    page = staff_client.get(url)
    assert page.status_code == 200
    assert page.context["cl"].result_list[0]._competing == 1

    ids = list(BarAdmission.objects.values_list("pk", flat=True))
    staff_client.post(url, {"action": "approve_selected", "_selected_action": ids})
    statuses = sorted(BarAdmission.objects.values_list("status", flat=True))
    assert statuses == ["pending", "verified"]


@pytest.mark.parametrize(
    "name",
    ["admin:lawyers_lawyerprofile_changelist", "admin:lawyers_jurisdiction_changelist"],
)
def test_admin_pages_render(staff_client, name):
    assert staff_client.get(reverse(name)).status_code == 200

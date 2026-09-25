import pytest

from apps.lawyers.services import register_lawyer


@pytest.fixture
def make_lawyer(db):
    def _make(handle, name=None, city="", email=None):
        profile = register_lawyer(
            email=email or f"{handle}@example.com",
            password="Correct-Horse-42",
            handle=handle,
            name=name or handle.title(),
        )
        if city:
            profile.city = city
            profile.save()
        return profile

    return _make


@pytest.fixture
def me(client, make_lawyer):
    profile = make_lawyer("farid", name="Farid Khan")
    client.force_login(profile.user)
    return profile

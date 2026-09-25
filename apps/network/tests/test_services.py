import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.network.models import Connection, ConnectionRequest
from apps.network.selectors import contacts_of
from apps.network.services import (
    accept_request,
    are_connected,
    cancel_request,
    decline_request,
    remove_connection,
    send_request,
)


@pytest.fixture
def pair(make_lawyer):
    return make_lawyer("ayesha"), make_lawyer("bilal")


def test_request_then_accept_connects_both_ways(pair):
    a, b = pair
    assert send_request(sender=a, recipient=b) == "sent"
    accept_request(recipient=b, sender=a)
    assert are_connected(a, b) and are_connected(b, a)
    assert list(contacts_of(a)) == [b]
    assert list(contacts_of(b)) == [a]
    assert not ConnectionRequest.objects.exists()


def test_connection_is_stored_once_in_order(pair):
    a, b = pair
    send_request(sender=b, recipient=a)
    accept_request(recipient=a, sender=b)
    connection = Connection.objects.get()
    assert connection.lawyer_a.pk < connection.lawyer_b.pk


def test_database_rejects_reversed_pair(pair):
    a, b = pair
    low, high = sorted([a, b], key=lambda p: p.pk)
    with pytest.raises(IntegrityError):
        Connection.objects.create(lawyer_a=high, lawyer_b=low)


def test_crossed_requests_connect_automatically(pair):
    a, b = pair
    send_request(sender=a, recipient=b)
    assert send_request(sender=b, recipient=a) == "connected"
    assert are_connected(a, b)
    assert not ConnectionRequest.objects.exists()


@pytest.mark.parametrize("case", ["self", "duplicate", "already_connected"])
def test_invalid_requests(pair, case):
    a, b = pair
    if case == "self":
        with pytest.raises(ValidationError):
            send_request(sender=a, recipient=a)
    elif case == "duplicate":
        send_request(sender=a, recipient=b)
        with pytest.raises(ValidationError, match="already sent"):
            send_request(sender=a, recipient=b)
    else:
        send_request(sender=a, recipient=b)
        accept_request(recipient=b, sender=a)
        with pytest.raises(ValidationError, match="already connected"):
            send_request(sender=a, recipient=b)


def test_declined_sender_can_ask_again_anytime(pair):
    a, b = pair
    send_request(sender=a, recipient=b)
    decline_request(recipient=b, sender=a)
    assert send_request(sender=a, recipient=b) == "sent"


def test_only_the_recipient_can_accept(pair):
    a, b = pair
    send_request(sender=a, recipient=b)
    with pytest.raises(ValidationError):
        accept_request(recipient=a, sender=b)
    assert not are_connected(a, b)


def test_cancel_and_remove(pair):
    a, b = pair
    send_request(sender=a, recipient=b)
    cancel_request(sender=a, recipient=b)
    assert not ConnectionRequest.objects.exists()

    send_request(sender=a, recipient=b)
    accept_request(recipient=b, sender=a)
    remove_connection(profile=b, other=a)
    assert not are_connected(a, b)


def test_cannot_request_inactive_member(pair):
    a, b = pair
    b.user.is_active = False
    b.user.save()
    with pytest.raises(ValidationError):
        send_request(sender=a, recipient=b)

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from apps.lawyers.models import LawyerProfile

from .models import Connection, ConnectionRequest


def are_connected(first: LawyerProfile, second: LawyerProfile) -> bool:
    return Connection.objects.filter(Connection.between(first, second)).exists()


def _connect(first: LawyerProfile, second: LawyerProfile) -> Connection:
    a, b = Connection.ordered(first, second)
    connection, _created = Connection.objects.get_or_create(lawyer_a=a, lawyer_b=b)
    ConnectionRequest.objects.filter(sender=first, recipient=second).delete()
    ConnectionRequest.objects.filter(sender=second, recipient=first).delete()
    return connection


@transaction.atomic
def send_request(*, sender: LawyerProfile, recipient: LawyerProfile) -> str:
    """Return "sent", or "connected" when the recipient had already asked us."""
    if sender.pk == recipient.pk:
        raise ValidationError(_("You can't connect with yourself."))
    if not recipient.user.is_active:
        raise ValidationError(_("This member is no longer active."))
    if are_connected(sender, recipient):
        raise ValidationError(_("You're already connected."))

    if ConnectionRequest.objects.filter(sender=recipient, recipient=sender).exists():
        _connect(sender, recipient)
        return "connected"

    try:
        with transaction.atomic():
            ConnectionRequest.objects.create(sender=sender, recipient=recipient)
    except IntegrityError as exc:
        raise ValidationError(_("Request already sent.")) from exc
    return "sent"


def cancel_request(*, sender: LawyerProfile, recipient: LawyerProfile) -> None:
    deleted, _ = ConnectionRequest.objects.filter(sender=sender, recipient=recipient).delete()
    if not deleted:
        raise ValidationError(_("There is no pending request to cancel."))


@transaction.atomic
def accept_request(*, recipient: LawyerProfile, sender: LawyerProfile) -> Connection:
    if not ConnectionRequest.objects.filter(sender=sender, recipient=recipient).exists():
        raise ValidationError(_("There is no pending request to accept."))
    return _connect(sender, recipient)


def decline_request(*, recipient: LawyerProfile, sender: LawyerProfile) -> None:
    # Declining deletes the request; the sender may ask again at any time.
    deleted, _ = ConnectionRequest.objects.filter(sender=sender, recipient=recipient).delete()
    if not deleted:
        raise ValidationError(_("There is no pending request to decline."))


def remove_connection(*, profile: LawyerProfile, other: LawyerProfile) -> None:
    deleted, _ = Connection.objects.filter(Connection.between(profile, other)).delete()
    if not deleted:
        raise ValidationError(_("You're not connected."))

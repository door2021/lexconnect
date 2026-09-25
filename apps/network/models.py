from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.lawyers.models import LawyerProfile


class ConnectionRequest(TimeStampedModel):
    """A pending invitation. Accepting or declining deletes it."""

    sender = models.ForeignKey(
        LawyerProfile, on_delete=models.CASCADE, related_name="sent_requests"
    )
    recipient = models.ForeignKey(
        LawyerProfile, on_delete=models.CASCADE, related_name="received_requests"
    )

    class Meta:
        verbose_name = _("connection request")
        verbose_name_plural = _("connection requests")
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "recipient"], name="network_one_request_per_pair"
            ),
            models.CheckConstraint(
                condition=~Q(sender=F("recipient")), name="network_no_self_request"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sender_id} → {self.recipient_id}"


class Connection(TimeStampedModel):
    """A mutual connection, stored once per pair with lawyer_a.pk < lawyer_b.pk."""

    lawyer_a = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="+")
    lawyer_b = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name="+")

    class Meta:
        verbose_name = _("connection")
        verbose_name_plural = _("connections")
        constraints = [
            models.UniqueConstraint(
                fields=["lawyer_a", "lawyer_b"], name="network_one_connection_per_pair"
            ),
            models.CheckConstraint(
                condition=Q(lawyer_a__lt=F("lawyer_b")), name="network_connection_ordered_pair"
            ),
        ]
        indexes = [models.Index(fields=["lawyer_b"], name="network_conn_lawyer_b_idx")]

    def __str__(self) -> str:
        return f"{self.lawyer_a_id} ↔ {self.lawyer_b_id}"

    @staticmethod
    def ordered(first: LawyerProfile, second: LawyerProfile) -> tuple[LawyerProfile, LawyerProfile]:
        return (first, second) if first.pk < second.pk else (second, first)

    @classmethod
    def between(cls, first: LawyerProfile, second: LawyerProfile) -> Q:
        a, b = cls.ordered(first, second)
        return Q(lawyer_a=a, lawyer_b=b)

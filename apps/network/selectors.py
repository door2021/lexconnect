from django.db.models import Exists, OuterRef, Q, QuerySet

from apps.lawyers.models import LawyerProfile

from .models import Connection, ConnectionRequest


def with_relationship(queryset: QuerySet, viewer: LawyerProfile) -> QuerySet:
    """Annotate profiles with the viewer's relationship to each, in one query."""
    return queryset.annotate(
        is_contact=Exists(
            Connection.objects.filter(
                Q(lawyer_a=viewer, lawyer_b=OuterRef("pk"))
                | Q(lawyer_b=viewer, lawyer_a=OuterRef("pk"))
            )
        ),
        request_sent=Exists(
            ConnectionRequest.objects.filter(sender=viewer, recipient=OuterRef("pk"))
        ),
        request_received=Exists(
            ConnectionRequest.objects.filter(sender=OuterRef("pk"), recipient=viewer)
        ),
    )


def contacts_of(profile: LawyerProfile) -> QuerySet:
    return (
        LawyerProfile.objects.filter(
            Exists(
                Connection.objects.filter(
                    Q(lawyer_a=profile, lawyer_b=OuterRef("pk"))
                    | Q(lawyer_b=profile, lawyer_a=OuterRef("pk"))
                )
            ),
            user__is_active=True,
        )
        .select_related("user")
        .order_by("user__name")
    )


def search_lawyers(*, query: str, viewer: LawyerProfile) -> QuerySet:
    """Name/handle/city substring search; email only on an exact full match."""
    query = query.strip()
    base = LawyerProfile.objects.filter(user__is_active=True).exclude(pk=viewer.pk)

    if not query:
        return base.none()
    if query.startswith("@"):
        condition = Q(user__handle__icontains=query[1:])
    elif "@" in query:
        condition = Q(user__email=query.lower())
    else:
        condition = (
            Q(user__name__icontains=query)
            | Q(user__handle__icontains=query)
            | Q(city__icontains=query)
        )
    return base.filter(condition).select_related("user").order_by("user__name")


def pending_request_count(profile: LawyerProfile) -> int:
    return ConnectionRequest.objects.filter(recipient=profile).count()

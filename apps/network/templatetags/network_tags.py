from django import template

from apps.lawyers.models import LawyerProfile

from ..selectors import with_relationship

register = template.Library()


@register.inclusion_tag("network/partials/connect_button.html", takes_context=True)
def connect_button(context, profile):
    """Connection button for any profile page; renders nothing for yourself or staff."""
    request = context["request"]
    viewer = getattr(request.user, "lawyer_profile", None)
    if viewer is None or viewer.pk == profile.pk:
        return {"profile": None}
    annotated = with_relationship(LawyerProfile.objects.filter(pk=profile.pk), viewer).get()
    return {"profile": annotated, "next": request.get_full_path()}

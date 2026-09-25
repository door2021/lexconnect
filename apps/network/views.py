from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.lawyers.models import LawyerProfile

from . import services
from .selectors import contacts_of, search_lawyers, with_relationship

ACTIONS = {
    "connect": lambda me, other: services.send_request(sender=me, recipient=other),
    "cancel": lambda me, other: services.cancel_request(sender=me, recipient=other),
    "accept": lambda me, other: services.accept_request(recipient=me, sender=other),
    "decline": lambda me, other: services.decline_request(recipient=me, sender=other),
    "remove": lambda me, other: services.remove_connection(profile=me, other=other),
}

SUCCESS_MESSAGES = {
    "connect": _("Request sent."),
    "cancel": _("Request cancelled."),
    "accept": _("You're now connected."),
    "decline": _("Request declined."),
    "remove": _("Contact removed."),
}


class ViewerProfileMixin:
    """The logged-in lawyer's profile; staff accounts without one get a 404."""

    def get_viewer(self) -> LawyerProfile:
        if not hasattr(self, "_viewer"):
            self._viewer = get_object_or_404(LawyerProfile, user=self.request.user)
        return self._viewer


class SearchView(ViewerProfileMixin, ListView):
    template_name = "network/search.html"
    context_object_name = "results"
    paginate_by = 20

    def get_queryset(self):
        viewer = self.get_viewer()
        results = search_lawyers(query=self.request.GET.get("q", ""), viewer=viewer)
        return with_relationship(results, viewer).prefetch_related("admissions")

    def get_context_data(self, **kwargs):
        return super().get_context_data(q=self.request.GET.get("q", "").strip(), **kwargs)


class NetworkView(ViewerProfileMixin, TemplateView):
    template_name = "network/network.html"

    def get_context_data(self, **kwargs):
        viewer = self.get_viewer()
        profiles = LawyerProfile.objects.select_related("user").filter(user__is_active=True)
        return super().get_context_data(
            incoming=with_relationship(profiles.filter(sent_requests__recipient=viewer), viewer),
            outgoing=with_relationship(profiles.filter(received_requests__sender=viewer), viewer),
            contacts=with_relationship(contacts_of(viewer), viewer),
            **kwargs,
        )


class ConnectionActionView(ViewerProfileMixin, View):
    http_method_names = ["post"]
    action = ""  # set per URL in urls.py

    def post(self, request, handle):
        viewer = self.get_viewer()
        other = get_object_or_404(
            LawyerProfile.objects.select_related("user"), user__handle=handle.lower()
        )
        error = None
        try:
            ACTIONS[self.action](viewer, other)
        except ValidationError as exc:
            error = exc.messages[0]

        if request.htmx:
            profile = with_relationship(
                LawyerProfile.objects.filter(pk=other.pk).select_related("user"), viewer
            ).get()
            return render(
                request,
                "network/partials/action_response.html",
                {"profile": profile, "error": error, "next": request.POST.get("next", "")},
            )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, SUCCESS_MESSAGES[self.action])
        return redirect(self._safe_next() or reverse("lawyers:profile", args=[other.user.handle]))

    def _safe_next(self) -> str | None:
        target = self.request.POST.get("next", "")
        if url_has_allowed_host_and_scheme(
            target,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return target
        return None

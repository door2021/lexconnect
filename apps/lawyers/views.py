from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, FormView

from .forms import BarAdmissionForm, ProfileForm, SignupForm
from .models import BarAdmission, LawyerProfile
from .services import (
    register_lawyer,
    submit_bar_admission,
    update_profile,
    withdraw_admission,
)


@method_decorator(login_not_required, name="dispatch")
class SignupView(FormView):
    template_name = "lawyers/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            profile = register_lawyer(
                email=data["email"],
                password=data["password1"],
                handle=data["handle"],
                name=data["name"],
                jurisdiction=data["jurisdiction"],
                license_number=data["license_number"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        login(self.request, profile.user)
        messages.success(self.request, _("Welcome! Your account is ready."))
        return super().form_valid(form)


class ProfileDetailView(DetailView):
    template_name = "lawyers/profile_detail.html"
    context_object_name = "profile"

    def get(self, request, *args, **kwargs):
        handle = kwargs["handle"]
        if handle != handle.lower():
            return redirect("lawyers:profile", handle=handle.lower(), permanent=True)
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        queryset = LawyerProfile.objects.select_related("user").prefetch_related(
            Prefetch("admissions", queryset=BarAdmission.objects.select_related("jurisdiction"))
        )
        return get_object_or_404(queryset, user__handle=self.kwargs["handle"], user__is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_own_profile"] = self.object.user_id == self.request.user.pk
        return context


class OwnProfileMixin:
    """Resolve the logged-in user's lawyer profile (404 for staff without one)."""

    def get_profile(self) -> LawyerProfile:
        if not hasattr(self, "_profile"):
            self._profile = get_object_or_404(
                LawyerProfile.objects.select_related("user"), user=self.request.user
            )
        return self._profile


class ProfileEditView(OwnProfileMixin, FormView):
    template_name = "lawyers/profile_edit.html"
    form_class = ProfileForm

    def get_initial(self):
        profile = self.get_profile()
        return {
            "name": profile.user.name,
            "headline": profile.headline,
            "city": profile.city,
            "bio": profile.bio,
        }

    def form_valid(self, form):
        profile = update_profile(profile=self.get_profile(), **form.cleaned_data)
        messages.success(self.request, _("Profile updated."))
        return redirect("lawyers:profile", handle=profile.user.handle)


class BarAdmissionsView(OwnProfileMixin, FormView):
    template_name = "lawyers/bar_admissions.html"
    form_class = BarAdmissionForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "profile": self.get_profile()}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admissions"] = self.get_profile().admissions.select_related("jurisdiction")
        return context

    def form_valid(self, form):
        try:
            submit_bar_admission(profile=self.get_profile(), **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, _("Submitted for verification."))
        return redirect("lawyers:bar_admissions")


class WithdrawAdmissionView(View):
    http_method_names = ["post"]

    def post(self, request, pk):
        # Scoped to the current user: other members' admissions are simply "not found".
        admission = get_object_or_404(BarAdmission, pk=pk, lawyer__user=request.user)
        try:
            withdraw_admission(admission=admission)
            messages.success(request, _("Admission withdrawn."))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect(reverse("lawyers:bar_admissions"))

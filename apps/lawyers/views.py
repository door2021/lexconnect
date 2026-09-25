from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView

from .forms import SignupForm
from .services import register_lawyer


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

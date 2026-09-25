from .selectors import pending_request_count


def network(request):
    profile = (
        getattr(request.user, "lawyer_profile", None) if request.user.is_authenticated else None
    )
    return {"pending_request_count": pending_request_count(profile) if profile else 0}

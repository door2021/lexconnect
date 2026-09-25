# ADR-0006: MVP scope and access policy
Status: Accepted
Scope: profiles, search & connections, messaging between contacts (manual refresh),
simple feed. Removed: referrals, notifications, groups, practice areas, photos.
Access: LoginRequiredMiddleware; public views opt out via login_not_required.
License numbers never shown to other members. Object access scoped to request.user
(404, not 403). Email via Django 6.1 MAILERS, SMTP enabled by EMAIL_HOST env var.
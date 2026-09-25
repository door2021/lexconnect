# ADR-0004: Business writes go through services, not signals
Status: Accepted
Decision: Multi-model writes and state transitions live in <app>/services.py
(keyword-only functions, full_clean() before save, transaction.atomic).
Models hold single-object logic. No post_save signals for domain behavior.
Why: explicit control flow, one tested entry point for views/admin/commands,
no side effects on createsuperuser or fixtures.
# ADR-0001: Stack and tooling
Status: Accepted
Decision: Django 6.x server-rendered templates + HTMX/Alpine, PostgreSQL,
Tailwind via django-tailwind-cli, uv + pyproject.toml, ruff, pytest-django,
env-driven single settings file.
Why: one deployable monolith, no Node toolchain, dev/prod DB parity,
reproducible installs via committed uv.lock.
Rejected: SPA + DRF (duplicate API layer), SQLite (no parity, weak search),
split settings files (drift).
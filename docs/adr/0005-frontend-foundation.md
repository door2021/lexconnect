# ADR-0005: Frontend foundation
Status: Accepted
Decision: Tailwind v4.3.3 pinned via django-tailwind-cli (source in assets/,
compiled CSS gitignored, built at deploy). htmx 2 served by django-htmx
(htmx 4 is beta). Alpine deferred until a feature needs client state.
Forms styled through a project FORM_RENDERER + scoped .field CSS.
App dependency direction: core <- accounts <- lawyers <- feature apps.
Rejected: CDN scripts, crispy-forms/widget-tweaks, npm toolchain.
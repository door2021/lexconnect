# ADR-0002: Jurisdictions as data, Pakistan first
Status: Accepted
Decision: Licensing bodies are rows in a Jurisdiction table, seeded with
Pakistan Bar Council + Punjab, Sindh, KP, Balochistan, Islamabad bar councils.
A lawyer has many BarAdmissions (council + license number).
Why: licenses come from councils, not countries; one advocate can hold
several enrollments (provincial + Supreme Court). New countries = new rows.
Rejected: bar_number field on profile (can't express multiple enrollments).
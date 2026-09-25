# ADR-0007: Mutual connections
Status: Accepted
Decision: ConnectionRequest (sender, recipient) + Connection stored once per pair
with lawyer_a.pk < lawyer_b.pk (check + unique constraints). Relations link
LawyerProfiles, so staff are outside the graph by schema. Decline deletes the
request (re-request anytime). Crossed requests auto-connect. Actions are
addressed by handle and scoped to the viewer. Reads in selectors.py,
writes in services.py. Search: icontains now; pg_trgm index if it gets slow.
Rejected: status column on one table; two rows per friendship.
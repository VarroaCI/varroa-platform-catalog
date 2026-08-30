# Plugin sets

Each file is a `plugins:` list of `artifactId` + `version` pairs. The
composer deduplicates by `artifactId` across all inputs (later entries win,
with a warning on version conflicts) and every entry must carry an exact pin —
unpinned entries are rejected as invalid.

**The one rule that matters:** any plugin here that also appears in the
platform's `JenkinsVersionProfile` plugin-set lock must use the identical
version string. A mismatch makes the operator abort every controller
reconcile with a "plugin version conflict". The lock snapshot this catalog
tracks lives in [`locks/`](../locks/), and `hack/validate-catalog.py` fails CI
on any drift — update the snapshot and the pins together when the platform
bumps its lock.

In the index, plugin entries use `version: bundle`; the real pins live in
these files.

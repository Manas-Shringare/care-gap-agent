# Scope: care-gap-agent

*Draft. Lives in `docs/SCOPE.md`. Public-safe: no personal or career material, no account identifiers. Not yet reviewed or committed.*

## User

A care coordinator at an outpatient clinic who manages a panel of patients and does outreach.

## Decision it supports

"Which patients on my panel are overdue for a recommended test or measure, and why?" The coordinator uses the answer to decide who to contact first.

Example: *"Which of my diabetic patients haven't had an A1c test in 6 months?"* The agent returns the patient list and states the guideline rule behind the answer.

## Data

Synthetic patient records from Synthea (CSV export), stored in S3 and queried through Athena. The data is synthetic, but the project handles it as PHI: role-based access, minimum necessary data in answers, and an audit log of every request. This demonstrates HIPAA-style patterns and makes no compliance claim.

- **Source:** the pre-generated Synthea CSV sample from Nov 2021 (the README gives the file name and SHA-256). It has 1,163 patient rows: 163 deceased and 1,000 living.
- **Tables:** 11 of the 18 CSV files are loaded (clinical and provider tables). Billing and imaging files are not used.
- **As-of date: 2021-11-19.** The sample ends on that date, so every "last N months" rule is measured from it, not from today's date. Answers state the as-of date.

## Cohort definitions (fixed before the golden set is labeled)

- **Diabetic patient:** a living patient with condition code `44054006` (Diabetes). Matching on condition text is not allowed, because it would also match prediabetes (`15777000`).
- **A1c test:** observation code `4548-4` (LOINC, hemoglobin A1c).
- **Care gap for the A1c measure:** a diabetic patient whose most recent A1c is before 2021-05-19 (six months before the as-of date), or who has none.
- **Excluded:** deceased patients (any row with a death date).

## Roles (simulated)

- **Care coordinator:** sees identified data for their own patient panel.
- **Researcher:** sees de-identified aggregates only.

Roles are simulated. There is no real authentication.

## Success metric (proposed; confirm before the golden set is labeled)

Primary is **correctness**, because it is the only metric that can be measured and enforced in CI:

1. For cohort questions in the golden set (~50 labeled questions), the returned patient set exactly matches the ground-truth SQL result. The target percentage is set after the first baseline run, not before.
2. **Zero** role leaks: every role-leak test returns nothing.
3. **Zero** failures on should-refuse questions.

Tracked, not gated except for cost jumps: cost per question and latency.

Coordinator time saved is not measured. It cannot be measured on synthetic data.

## Priority order

- **Tier A (must ship):** audit store, Synthea in Athena, agent with cohort search + read-only SQL + rules lookup, role-based access with audit log, golden set with deterministic eval runner and CI gate, README with Findings.
- **Tier B (if ahead):** LLM-as-judge with agreement against human labels; retries, backoff and cost capture; Lambda deploy.
- **Tier C (if well ahead):** grounded answers with citations and abstention; OpenTelemetry traces; model comparison; Terraform.

## Out of scope

Real authentication, dashboards, prompt versioning, fine-tuning or training models, FHIR flattening (CSV is used), always-on infrastructure, and any real patient data.

## Known limitations

Synthea records are cleaner and more regular than real EHR data. The sample is a 2021 snapshot, so answers are "as of 2021-11-19". Roles are simulated. See the README for the full list.
---
name: auto-job-application
description: Find, verify, rank, tailor, approve, submit, and track job applications across employer career sites and job boards. Use when Codex needs to automate a job search or application workflow; maintain candidate facts and work-authorization answers; select a resume variant; write required cover letters and screening answers; fill application forms; create temporary application accounts when authorized; pause for CAPTCHA, MFA, or unresolved legal declarations; or maintain job, resume-usage, and submission trackers.
---

# Auto Job Application

Build a fact-grounded, approval-gated application pipeline. Automate repetitive work, but never invent candidate facts or report success without a verified confirmation.

## Start from trusted state

1. Locate the candidate profile, source resumes, portfolio links, supporting documents, job tracker, resume-usage tracker, and any local account registry.
2. If no workspace exists, run:

   `python scripts/application_records.py init <workspace>`

3. Copy verified facts into the generated candidate profile. Leave unknown fields marked `Unknown - ask once`.
4. Treat the candidate profile and current trackers as authoritative. Reuse confirmed identity, contact, education, work-authorization, availability, and compensation answers without asking again.
5. Ask only when a form requests a missing fact or uses wording that materially changes a legal declaration.
6. Keep credentials, resumes, transcripts, identity documents, candidate profiles, and generated trackers out of the skill repository.

Read [references/data-contracts.md](references/data-contracts.md) before creating or modifying records. Read [references/browser-playbook.md](references/browser-playbook.md) before filling browser forms.

## Run the workflow

### 1. Discover and verify roles

- Search current official employer pages first; use job boards for discovery and fallback.
- Verify that the role is live, full-time or otherwise within the user's configured scope, and in the target location.
- Apply the eligibility rules recorded in the candidate profile. Do not infer a restriction from silence.
- Exclude explicit mismatches such as location, employment type, seniority, citizenship, work-pass, or sponsorship restrictions.
- Merge duplicates by canonical URL; otherwise use normalized company and title.
- Record every considered role before application work.

### 2. Rank fit

- Score verified evidence only: required skills, relevant experience, education, seniority, location, employment type, and work authorization.
- Record matched skills and missing requirements separately.
- Do not inflate fit by treating coursework, prototypes, internships, or exposure as production ownership.
- Prefer roles whose core requirements are supported by the resume, even if several preferred qualifications are missing.

### 3. Prepare a tailored packet

For each selected role:

- Choose the closest verified resume variant and record its internal path and variant ID.
- Tailor wording only from verified source material. Preserve dates, titles, metrics, technologies, and scope.
- Use the employer-facing filename requested by the candidate, while retaining the internal variant in `resume_usage.csv`.
- Write a concise cover letter when required or materially useful. Address the role's priorities and state work authorization truthfully.
- Draft short screening answers from the candidate profile and job description.
- Attach optional supporting documents only when the field is appropriate and the candidate profile authorizes their use.
- Create or update the application packet with `user_approval: pending`.

### 4. Present an approval batch

Show company, title, official URL, fit rationale, eligibility signal, missing requirements, resume variant, cover letter, and unresolved questions. Keep batches small enough to review.

Do not submit from a general instruction given earlier in the workflow. Obtain explicit action-time approval for the specific role or clearly identified batch. Record approval with:

`python scripts/application_records.py approve --packets <packets.json> --job-id <job-id>`

### 5. Fill and submit

- Use the browser named by the user; otherwise use the current authenticated browser suitable for the target URL.
- Reinspect the visible page after every navigation, modal, upload, dropdown, or validation change.
- Reuse confirmed candidate-profile answers exactly where the form wording matches.
- Stop and ask for missing identity, compensation, work-authorization, consent, criminal-history, conflict-of-interest, export-control, or other legally significant answers.
- Stop for CAPTCHA, MFA, email verification, identity verification, salary ambiguity, or browser safety interstitials. Tell the user exactly what to do and keep the page open.
- Create a temporary application account only when authorized. Record the platform, login email, and authentication method in a local-only registry; never commit it.
- Immediately before the final click, verify the employer, role, uploaded file name, screening answers, and recorded approval.
- Submit only the approved packet.

### 6. Verify and record

- Treat a success URL plus receipt text, application-history entry, or confirmation number as evidence.
- Do not treat a disabled button, spinner, sent click, or absence of an error as success.
- Save the exact confirmation text or number and submission date.
- Update all three records atomically after confirmation:

  `python scripts/application_records.py mark-submitted --tracker <application_tracker.csv> --resume-usage <resume_usage.csv> --packets <application_packets.json> --job-id <job-id> --confirmation <text>`

- Preserve the confirmation tab when the user may need it. Keep CAPTCHA/MFA tabs as handoffs; close disposable tabs.
- Set and record a follow-up date.

## Guardrails

- Never fabricate facts, metrics, links, work rights, consent, or demographic answers.
- Never submit an unapproved or already-submitted packet.
- Never solve or bypass CAPTCHA without the user's explicit direction; prefer user completion.
- Never save credentials in this repository or include candidate PII in a public commit.
- Never overwrite unrelated tracker rows or user edits.
- Never apply to an explicit eligibility mismatch unless the user knowingly overrides it.
- Never claim submission without evidence.

## Record utilities

- Initialize workspace: `python scripts/application_records.py init <workspace>`
- Upsert job: `python scripts/application_records.py upsert-job --tracker <csv> --record-json <json>`
- Upsert resume usage: `python scripts/application_records.py upsert-resume --resume-usage <csv> --record-json <json>`
- Approve packet: `python scripts/application_records.py approve --packets <json> --job-id <id>`
- Mark verified submission: `python scripts/application_records.py mark-submitted ...`
- Audit records: `python scripts/application_records.py validate --tracker <csv> --resume-usage <csv> --packets <json>`

Run validation before and after each application batch.

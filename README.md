# Auto Job Application Skill

An approval-gated Codex skill for finding, verifying, tailoring, submitting, and tracking job applications across employer career sites and job boards.

It automates repetitive application work while keeping candidate facts, legal declarations, credentials, and final submission decisions under explicit user control.

## What it does

- Finds current roles and verifies them against location, employment type, seniority, and work-authorization requirements.
- Ranks opportunities using verified resume evidence rather than inflated or invented claims.
- Selects and tracks the exact resume variant used for every application.
- Drafts tailored cover letters and screening answers from a reusable candidate profile.
- Fills browser-based applications and pauses for CAPTCHA, MFA, identity checks, or unresolved legal questions.
- Requires role-specific approval before submission and records authoritative confirmation evidence afterward.
- Keeps application, resume-usage, packet, and follow-up records consistent through a tested Python utility.

## Safety model

The skill is designed around four invariants:

1. **Verified facts only** — never invent identity details, experience, metrics, links, work rights, consent, or demographic answers.
2. **Approval before submission** — an application packet cannot be submitted or recorded as submitted without explicit approval.
3. **Human handoff for sensitive gates** — pause for CAPTCHA, MFA, email verification, identity verification, salary ambiguity, and materially different legal declarations.
4. **Evidence-backed completion** — a click or spinner is not success; record a confirmation number, application-history entry, or explicit receipt page.

Personal resumes, transcripts, candidate profiles, credentials, and generated application records are excluded by `.gitignore` and should remain local.

## Prerequisites

- Codex with personal skills support
- Python 3.9 or later
- An available browser-control capability for form filling
- GitHub CLI if cloning this private repository with `gh`

## Installation

Clone the repository into your personal Codex skills directory.

### PowerShell

```powershell
$skillsRoot = if ($env:CODEX_HOME) { "$env:CODEX_HOME\skills" } else { "$HOME\.codex\skills" }
gh repo clone Lee-Juntong/auto-job-application-skill "$skillsRoot\auto-job-application"
```

### Bash

```bash
skills_root="${CODEX_HOME:-$HOME/.codex}/skills"
gh repo clone Lee-Juntong/auto-job-application-skill "$skills_root/auto-job-application"
```

Restart or refresh Codex if the skill does not appear immediately.

## Quick start

### 1. Initialize a private application workspace

From the skill directory:

```bash
python scripts/application_records.py init /path/to/job-applications
```

This creates:

- `candidate_profile.md`
- `application_tracker.csv`
- `resume_usage.csv`
- `jobs.json`
- `application_packets.json`

Fill `candidate_profile.md` only with verified facts. Leave unknown values as `Unknown - ask once` so Codex asks once and reuses the confirmed answer later.

### 2. Invoke the skill

```text
Use $auto-job-application to find five full-time AI engineering roles in Singapore, prepare tailored application packets, and show me the approval batch before submitting anything.
```

The expected workflow is:

```text
Discover → Verify → Rank → Tailor → Approve → Submit → Confirm → Track
```

### 3. Validate records

Run this before and after an application batch:

```bash
python scripts/application_records.py validate \
  --tracker /path/to/job-applications/application_tracker.csv \
  --resume-usage /path/to/job-applications/resume_usage.csv \
  --packets /path/to/job-applications/application_packets.json
```

A healthy workspace prints:

```text
Validation passed
```

## Record utility

`scripts/application_records.py` provides deterministic updates for the application records.

| Command | Purpose |
| --- | --- |
| `init` | Create a new local workspace from the bundled templates. |
| `upsert-job` | Insert or replace one job in `application_tracker.csv`. |
| `upsert-resume` | Insert or replace one resume-usage record. |
| `approve` | Record explicit approval when no unresolved questions remain. |
| `mark-submitted` | Atomically record confirmation evidence, submission date, resume status, and follow-up date. |
| `validate` | Audit headers, duplicates, cross-file consistency, approvals, dates, and confirmation evidence. |

Show all commands:

```bash
python scripts/application_records.py --help
```

### Approval example

```bash
python scripts/application_records.py approve \
  --packets /path/to/job-applications/application_packets.json \
  --job-id example-ai-engineer
```

Approval is blocked if the packet still contains unresolved questions or has already been submitted.

### Verified submission example

```bash
python scripts/application_records.py mark-submitted \
  --tracker /path/to/job-applications/application_tracker.csv \
  --resume-usage /path/to/job-applications/resume_usage.csv \
  --packets /path/to/job-applications/application_packets.json \
  --job-id example-ai-engineer \
  --confirmation "Application received"
```

This command records submission only; the browser workflow must first verify the real employer confirmation.

## Browser workflow coverage

The bundled playbook captures tested patterns for:

- Greenhouse
- Workday
- Eightfold
- SmartRecruiters
- JobStreet / SEEK
- ByteDance / TikTok
- LinkedIn Easy Apply

It includes dynamic-locator refreshes, file-chooser uploads, exact dropdown verification, phone country-code checks, session recovery, account creation boundaries, and confirmation evidence hierarchy.

See [references/browser-playbook.md](references/browser-playbook.md) for the browser procedure and [references/data-contracts.md](references/data-contracts.md) for record schemas and status transitions.

## Repository structure

```text
auto-job-application-skill/
├── SKILL.md                         # Agent workflow and guardrails
├── agents/openai.yaml               # Codex skill metadata
├── assets/                          # Safe starter templates
├── references/
│   ├── browser-playbook.md          # Browser form patterns
│   └── data-contracts.md            # Tracker and packet schemas
└── scripts/
    ├── application_records.py       # Record-management CLI
    └── test_application_records.py  # Behavioral tests
```

## Development and validation

Run the behavioral tests:

```bash
python -m unittest discover -s scripts -p "test_application_records.py" -v
```

The test suite verifies:

- workspace initialization is non-destructive
- approved submissions update all records consistently
- unapproved submissions are blocked
- packets with unresolved questions cannot be approved

Validate the skill structure with Codex's `quick_validate.py` from the `skill-creator` skill.

## Privacy notes

- Keep the working application workspace outside this repository.
- Never commit candidate profiles, resumes, transcripts, credentials, identity documents, or application confirmations containing personal data.
- Store temporary application-account details in a local-only registry.
- Review staged files before every push, even when `.gitignore` is configured.

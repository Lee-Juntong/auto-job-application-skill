# Data contracts

## Workspace files

- `candidate_profile.md`: verified candidate facts and reusable answers.
- `jobs.json`: optional detailed job records.
- `application_tracker.csv`: one current row per job.
- `resume_usage.csv`: the exact internal resume variant and employer-facing filename used per job.
- `application_packets.json`: tailored materials, approval, and submission evidence.
- Local account registry: keep outside the repository and never commit credentials.

## Job record

Required fields:

`job_id`, `company`, `title`, `location`, `employment_type`, `source_url`, `closing_date`, `sponsorship_signal`, `matched_skills`, `missing_requirements`, `fit_score`, `status`, `submission_date`, `follow_up_date`, `notes`.

Use a stable lowercase hyphenated `job_id`. Store matched and missing skills as semicolon-separated values in CSV or arrays in JSON. Fit score is 0-100.

Recommended status transitions:

`discovered -> verified -> packet_prepared -> approved -> in_progress -> submitted`

Alternative terminal or paused states:

`rejected`, `closed`, `duplicate`, `explicit_eligibility_mismatch`, `captcha_required`, `mfa_required`, `user_action_required`, `failed`, `withdrawn`.

## Resume-usage record

Required fields:

`job_id`, `company`, `title`, `resume_variant_id`, `internal_resume_pdf`, `submitted_filename`, `cover_letter_internal_source`, `cover_letter_submitted_filename`, `application_status`, `submission_date`, `notes`.

Never infer the internal variant from the submitted filename; many candidates intentionally use one natural employer-facing filename for every tailored PDF.

## Application packet

Each JSON object contains:

```json
{
  "job_id": "company-role-id",
  "resume_variant": {
    "variant_id": "ai-software-engineer-v2",
    "internal_path": "resumes/ai-software-engineer-v2.pdf",
    "submitted_filename": "Candidate Resume.pdf"
  },
  "cover_letter": "",
  "form_answers": {},
  "unresolved_questions": [],
  "user_approval": "pending",
  "submission_status": "not_submitted",
  "submission_confirmation": "",
  "submission_date": ""
}
```

Approval values: `pending`, `approved`, `rejected`.

Submission values: `not_submitted`, `ready`, `in_progress`, `submitted`, `blocked`, `failed`.

A submitted packet must have approval, confirmation evidence, and a submission date.

## Candidate profile

Separate stable facts from role-specific defaults and employer-specific answers. Mark unverified values explicitly. Recommended sections:

- identity and contact
- location and address
- work authorization and sponsorship
- availability and notice period
- compensation defaults and when they may be reused
- education and supporting documents
- languages
- portfolio links
- recurring legal or demographic answers supplied by the candidate
- employer-specific facts
- facts that must not be inferred

Update the profile only from the candidate or authoritative documents. Preserve an audit date.

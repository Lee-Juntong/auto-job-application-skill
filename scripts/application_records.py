#!/usr/bin/env python3
"""Initialize, update, and audit approval-gated job application records."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable


JOB_FIELDS = [
    "job_id",
    "company",
    "title",
    "location",
    "employment_type",
    "source_url",
    "closing_date",
    "sponsorship_signal",
    "matched_skills",
    "missing_requirements",
    "fit_score",
    "status",
    "submission_date",
    "follow_up_date",
    "notes",
]

RESUME_FIELDS = [
    "job_id",
    "company",
    "title",
    "resume_variant_id",
    "internal_resume_pdf",
    "submitted_filename",
    "cover_letter_internal_source",
    "cover_letter_submitted_filename",
    "application_status",
    "submission_date",
    "notes",
]

PACKET_FIELDS = {
    "job_id",
    "resume_variant",
    "cover_letter",
    "form_answers",
    "unresolved_questions",
    "user_approval",
    "submission_status",
    "submission_confirmation",
    "submission_date",
}

APPROVAL_VALUES = {"pending", "approved", "rejected"}
SUBMISSION_VALUES = {"not_submitted", "ready", "in_progress", "submitted", "blocked", "failed"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def normalize_record(record: dict[str, Any], fields: list[str]) -> dict[str, str]:
    missing = [field for field in ("job_id", "company", "title") if not record.get(field)]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    return {field: str(record.get(field, "")) for field in fields}


def upsert_csv(path: Path, fields: list[str], record: dict[str, Any]) -> None:
    normalized = normalize_record(record, fields)
    current_fields, rows = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected header in {path}")
    replaced = False
    for index, row in enumerate(rows):
        if row["job_id"] == normalized["job_id"]:
            rows[index] = normalized
            replaced = True
            break
    if not replaced:
        rows.append(normalized)
    write_csv(path, fields, rows)


def init_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parents[1] / "assets"
    copies = {
        "candidate-profile.template.md": "candidate_profile.md",
        "application_tracker.template.csv": "application_tracker.csv",
        "resume_usage.template.csv": "resume_usage.csv",
        "jobs.template.json": "jobs.json",
        "application_packets.template.json": "application_packets.json",
    }
    for source_name, target_name in copies.items():
        target = workspace / target_name
        if not target.exists():
            shutil.copyfile(assets / source_name, target)


def find_packet(packets: list[dict[str, Any]], job_id: str) -> dict[str, Any]:
    matches = [packet for packet in packets if packet.get("job_id") == job_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one packet for {job_id}, found {len(matches)}")
    return matches[0]


def approve_packet(path: Path, job_id: str) -> None:
    packets = load_json(path)
    packet = find_packet(packets, job_id)
    if packet.get("submission_status") == "submitted":
        raise ValueError("cannot approve an already-submitted packet")
    if packet.get("unresolved_questions"):
        raise ValueError("cannot approve a packet with unresolved questions")
    packet["user_approval"] = "approved"
    packet["submission_status"] = "ready"
    save_json(path, packets)


def update_row(
    path: Path,
    fields: list[str],
    job_id: str,
    updates: dict[str, str],
    *,
    require: bool,
) -> None:
    current_fields, rows = read_csv(path)
    if current_fields != fields:
        raise ValueError(f"unexpected header in {path}")
    found = False
    for row in rows:
        if row.get("job_id") == job_id:
            row.update(updates)
            found = True
            break
    if require and not found:
        raise ValueError(f"job_id {job_id} not found in {path}")
    write_csv(path, fields, rows)


def mark_submitted(
    tracker: Path,
    resume_usage: Path,
    packets_path: Path,
    job_id: str,
    confirmation: str,
    submission_date: str,
    follow_up_days: int,
) -> None:
    if not confirmation.strip():
        raise ValueError("confirmation evidence is required")
    packets = load_json(packets_path)
    packet = find_packet(packets, job_id)
    if packet.get("user_approval") != "approved":
        raise PermissionError("submission record blocked: packet is not approved")
    if packet.get("submission_status") == "submitted":
        raise ValueError("packet is already submitted")
    if packet.get("unresolved_questions"):
        raise ValueError("submission record blocked: unresolved questions remain")

    submitted = date.fromisoformat(submission_date)
    follow_up = submitted + timedelta(days=follow_up_days)
    tracker_updates = {
        "status": "submitted",
        "submission_date": submitted.isoformat(),
        "follow_up_date": follow_up.isoformat(),
    }
    fields, rows = read_csv(tracker)
    if fields != JOB_FIELDS:
        raise ValueError(f"unexpected header in {tracker}")
    matched = False
    for row in rows:
        if row.get("job_id") == job_id:
            row.update(tracker_updates)
            evidence = f"confirmation: {confirmation.strip()}"
            row["notes"] = " | ".join(part for part in [row.get("notes", ""), evidence] if part)
            matched = True
            break
    if not matched:
        raise ValueError(f"job_id {job_id} not found in {tracker}")
    write_csv(tracker, JOB_FIELDS, rows)

    update_row(
        resume_usage,
        RESUME_FIELDS,
        job_id,
        {"application_status": "submitted", "submission_date": submitted.isoformat()},
        require=True,
    )
    packet["submission_status"] = "submitted"
    packet["submission_confirmation"] = confirmation.strip()
    packet["submission_date"] = submitted.isoformat()
    save_json(packets_path, packets)


def validate_records(tracker: Path, resume_usage: Path, packets_path: Path) -> list[str]:
    errors: list[str] = []
    tracker_fields, jobs = read_csv(tracker)
    resume_fields, resumes = read_csv(resume_usage)
    packets = load_json(packets_path)
    if tracker_fields != JOB_FIELDS:
        errors.append("application tracker header does not match the contract")
    if resume_fields != RESUME_FIELDS:
        errors.append("resume usage header does not match the contract")

    def duplicates(values: list[str]) -> list[str]:
        return sorted({value for value in values if value and values.count(value) > 1})

    for duplicate in duplicates([row.get("job_id", "") for row in jobs]):
        errors.append(f"duplicate job_id in tracker: {duplicate}")
    for duplicate in duplicates([row.get("source_url", "") for row in jobs]):
        errors.append(f"duplicate source_url in tracker: {duplicate}")
    for duplicate in duplicates([row.get("job_id", "") for row in resumes]):
        errors.append(f"duplicate job_id in resume usage: {duplicate}")
    for duplicate in duplicates([str(packet.get("job_id", "")) for packet in packets]):
        errors.append(f"duplicate job_id in packets: {duplicate}")

    tracker_ids = {row.get("job_id") for row in jobs}
    resume_ids = {row.get("job_id") for row in resumes}
    for row in jobs:
        if row.get("status") == "submitted" and not row.get("submission_date"):
            errors.append(f"submitted tracker row lacks date: {row.get('job_id')}")
    for row in resumes:
        if row.get("application_status") == "submitted" and not row.get("submission_date"):
            errors.append(f"submitted resume row lacks date: {row.get('job_id')}")
        if row.get("job_id") not in tracker_ids:
            errors.append(f"resume usage lacks tracker job: {row.get('job_id')}")

    for packet in packets:
        job_id = str(packet.get("job_id", ""))
        missing = sorted(PACKET_FIELDS - packet.keys())
        if missing:
            errors.append(f"packet {job_id or '<missing>'} lacks fields: {', '.join(missing)}")
        if packet.get("user_approval") not in APPROVAL_VALUES:
            errors.append(f"packet {job_id} has invalid approval value")
        if packet.get("submission_status") not in SUBMISSION_VALUES:
            errors.append(f"packet {job_id} has invalid submission value")
        if job_id not in tracker_ids:
            errors.append(f"packet lacks tracker job: {job_id}")
        if job_id not in resume_ids:
            errors.append(f"packet lacks resume-usage row: {job_id}")
        if packet.get("submission_status") == "submitted":
            if packet.get("user_approval") != "approved":
                errors.append(f"submitted packet is not approved: {job_id}")
            if not packet.get("submission_confirmation"):
                errors.append(f"submitted packet lacks confirmation: {job_id}")
            if not packet.get("submission_date"):
                errors.append(f"submitted packet lacks date: {job_id}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a local application workspace")
    init.add_argument("workspace", type=Path)

    job = sub.add_parser("upsert-job", help="insert or replace a tracker row")
    job.add_argument("--tracker", type=Path, required=True)
    job.add_argument("--record-json", type=Path, required=True)

    resume = sub.add_parser("upsert-resume", help="insert or replace a resume-usage row")
    resume.add_argument("--resume-usage", type=Path, required=True)
    resume.add_argument("--record-json", type=Path, required=True)

    approve = sub.add_parser("approve", help="record explicit user approval")
    approve.add_argument("--packets", type=Path, required=True)
    approve.add_argument("--job-id", required=True)

    submitted = sub.add_parser("mark-submitted", help="record a verified submission")
    submitted.add_argument("--tracker", type=Path, required=True)
    submitted.add_argument("--resume-usage", type=Path, required=True)
    submitted.add_argument("--packets", type=Path, required=True)
    submitted.add_argument("--job-id", required=True)
    submitted.add_argument("--confirmation", required=True)
    submitted.add_argument("--submission-date", default=date.today().isoformat())
    submitted.add_argument("--follow-up-days", type=int, default=7)

    validate = sub.add_parser("validate", help="audit tracker, resume, and packet consistency")
    validate.add_argument("--tracker", type=Path, required=True)
    validate.add_argument("--resume-usage", type=Path, required=True)
    validate.add_argument("--packets", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            init_workspace(args.workspace)
        elif args.command == "upsert-job":
            upsert_csv(args.tracker, JOB_FIELDS, load_json(args.record_json))
        elif args.command == "upsert-resume":
            upsert_csv(args.resume_usage, RESUME_FIELDS, load_json(args.record_json))
        elif args.command == "approve":
            approve_packet(args.packets, args.job_id)
        elif args.command == "mark-submitted":
            mark_submitted(
                args.tracker,
                args.resume_usage,
                args.packets,
                args.job_id,
                args.confirmation,
                args.submission_date,
                args.follow_up_days,
            )
        elif args.command == "validate":
            errors = validate_records(args.tracker, args.resume_usage, args.packets)
            if errors:
                print("Validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            print("Validation passed")
    except (OSError, ValueError, PermissionError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

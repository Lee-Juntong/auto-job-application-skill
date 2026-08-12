from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import application_records as records


class ApplicationRecordsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        records.init_workspace(self.workspace)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def seed(self, approval: str = "pending") -> None:
        job = {
            "job_id": "example-ai-engineer",
            "company": "Example",
            "title": "AI Engineer",
            "location": "Singapore",
            "employment_type": "Full-time",
            "source_url": "https://example.com/jobs/ai-engineer",
            "fit_score": 88,
            "status": "packet_prepared",
        }
        resume = {
            "job_id": job["job_id"],
            "company": job["company"],
            "title": job["title"],
            "resume_variant_id": "ai-engineer-v1",
            "internal_resume_pdf": "private/ai-engineer-v1.pdf",
            "submitted_filename": "Candidate Resume.pdf",
            "application_status": "prepared",
        }
        records.upsert_csv(self.workspace / "application_tracker.csv", records.JOB_FIELDS, job)
        records.upsert_csv(self.workspace / "resume_usage.csv", records.RESUME_FIELDS, resume)
        packets = [
            {
                "job_id": job["job_id"],
                "resume_variant": {
                    "variant_id": "ai-engineer-v1",
                    "internal_path": "private/ai-engineer-v1.pdf",
                    "submitted_filename": "Candidate Resume.pdf",
                },
                "cover_letter": "",
                "form_answers": {},
                "unresolved_questions": [],
                "user_approval": approval,
                "submission_status": "ready" if approval == "approved" else "not_submitted",
                "submission_confirmation": "",
                "submission_date": "",
            }
        ]
        records.save_json(self.workspace / "application_packets.json", packets)

    def test_init_is_non_destructive(self) -> None:
        profile = self.workspace / "candidate_profile.md"
        profile.write_text("custom\n", encoding="utf-8")
        records.init_workspace(self.workspace)
        self.assertEqual(profile.read_text(encoding="utf-8"), "custom\n")

    def test_approval_and_verified_submission(self) -> None:
        self.seed()
        records.approve_packet(self.workspace / "application_packets.json", "example-ai-engineer")
        records.mark_submitted(
            self.workspace / "application_tracker.csv",
            self.workspace / "resume_usage.csv",
            self.workspace / "application_packets.json",
            "example-ai-engineer",
            "Application received",
            "2026-08-11",
            7,
        )
        self.assertEqual(
            records.validate_records(
                self.workspace / "application_tracker.csv",
                self.workspace / "resume_usage.csv",
                self.workspace / "application_packets.json",
            ),
            [],
        )
        packet = json.loads((self.workspace / "application_packets.json").read_text(encoding="utf-8"))[0]
        self.assertEqual(packet["submission_status"], "submitted")
        self.assertEqual(packet["submission_confirmation"], "Application received")

    def test_unapproved_submission_is_blocked(self) -> None:
        self.seed()
        with self.assertRaises(PermissionError):
            records.mark_submitted(
                self.workspace / "application_tracker.csv",
                self.workspace / "resume_usage.csv",
                self.workspace / "application_packets.json",
                "example-ai-engineer",
                "Application received",
                "2026-08-11",
                7,
            )

    def test_unresolved_packet_cannot_be_approved(self) -> None:
        self.seed()
        path = self.workspace / "application_packets.json"
        packets = records.load_json(path)
        packets[0]["unresolved_questions"] = ["work authorization"]
        records.save_json(path, packets)
        with self.assertRaises(ValueError):
            records.approve_packet(path, "example-ai-engineer")


if __name__ == "__main__":
    unittest.main()

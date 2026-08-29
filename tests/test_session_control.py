import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/review-radius/scripts/session_control.py"
A = "a" * 40
B = "b" * 40
C = "c" * 40
D = "d" * 40


class SessionControlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.state = self.dir / "session.json"
        self.campaign_path = (
            ROOT / ".review-radius/campaigns/owner--repo-pr-79.json"
        )
        self.campaign_lock_path = self.campaign_path.with_suffix(".lock")
        self.campaign_path.unlink(missing_ok=True)
        self.campaign_lock_path.unlink(missing_ok=True)
        cutoff = datetime.now(timezone.utc)
        self.cutoff = cutoff.isoformat().replace("+00:00", "Z")
        self.deadline = (cutoff + timedelta(seconds=90)).isoformat().replace("+00:00", "Z")
        self.late_feedback_time = (
            cutoff + timedelta(seconds=1)
        ).isoformat().replace("+00:00", "Z")
        self.cli(
            "init", "--state", str(self.state), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", B,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1", check=0,
        )

    def tearDown(self):
        self.campaign_path.unlink(missing_ok=True)
        self.campaign_lock_path.unlink(missing_ok=True)
        self.tmp.cleanup()

    def cli(self, *args, check=None, cwd=ROOT):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            cwd=cwd,
        )
        if check is not None:
            self.assertEqual(result.returncode, check, result.stdout + result.stderr)
        payload = json.loads(result.stdout) if result.stdout else {}
        return result.returncode, payload

    def project(self, head, **overrides):
        return self.project_state(self.state, head, **overrides)

    def project_state(self, state, head, **overrides):
        signals = {
            "architecture_verdict": "LOCAL_SAFE", "boundary": "within",
            "premise": "valid", "semantic_delta": "expected",
            "frontier": "shrinking", "coverage": "sufficient",
            "risk": "same_or_lower", "patch_required": True,
            "obligations_complete": False, "obligations_blocked": False,
            "qa_acceptable": False,
        }
        signals.update(overrides)
        path = self.dir / f"{state.stem}-signals.json"
        path.write_text(json.dumps(signals))
        return self.cli(
            "project", "--state", str(state), "--signals", str(path), "--head", head,
        )

    def guard(self, action, head):
        return self.cli("guard", "--state", str(self.state), "--action", action, "--head", head)

    def guard_state(self, state, action, head):
        return self.cli(
            "guard", "--state", str(state), "--action", action, "--head", head,
        )

    def patch(self, from_head, to_head):
        code, guarded = self.guard("patch", from_head)
        self.assertEqual(code, 0, guarded)
        return self.cli(
            "record-patch", "--state", str(self.state),
            "--authorization", guarded["authorization"],
            "--from-head", from_head, "--to-head", to_head,
        )

    def test_default_state_denies_patch(self):
        code, payload = self.guard("patch", B)
        self.assertEqual(code, 3)
        self.assertFalse(payload["allowed"])

    def test_patch_authorization_is_head_bound_single_use_and_resets_evidence(self):
        self.assertEqual(self.project(B)[0], 0)
        code, guarded = self.guard("patch", B)
        self.assertEqual(code, 0)
        token = guarded["authorization"]
        code, recorded = self.cli(
            "record-patch", "--state", str(self.state), "--authorization", token,
            "--from-head", B, "--to-head", C,
        )
        self.assertEqual(code, 0)
        self.assertEqual(recorded["patch_rounds"], 1)
        self.assertEqual(self.cli(
            "record-patch", "--state", str(self.state), "--authorization", token,
            "--from-head", B, "--to-head", D,
        )[0], 2)
        code, inspected = self.cli("inspect", "--state", str(self.state))
        self.assertEqual(code, 0)
        self.assertEqual(inspected["decision"], "INSUFFICIENT_ARCHITECTURE_EVIDENCE")

    def test_stale_head_never_receives_authorization(self):
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.guard("patch", C)[0], 2)

    def test_two_round_fuse_cannot_be_reset_by_projected_signals(self):
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.patch(B, C)[0], 0)
        self.assertEqual(self.project(C)[0], 0)
        self.assertEqual(self.patch(C, D)[0], 0)
        code, payload = self.project(D)
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "AUTOMATION_FUSE_EXHAUSTED")
        code, denied = self.guard("patch", D)
        self.assertEqual(code, 3)
        self.assertEqual(denied["decision"], "AUTOMATION_FUSE_EXHAUSTED")
        spoof = {
            "architecture_verdict": "LOCAL_SAFE", "boundary": "within",
            "premise": "valid", "semantic_delta": "expected",
            "frontier": "shrinking", "coverage": "sufficient",
            "risk": "same_or_lower", "patch_rounds": 0,
            "patch_required": True, "obligations_complete": False,
            "obligations_blocked": False, "qa_acceptable": False,
        }
        path = self.dir / "spoof.json"
        path.write_text(json.dumps(spoof))
        self.assertEqual(self.cli(
            "project", "--state", str(self.state), "--signals", str(path), "--head", D,
        )[0], 2)
        code, extended = self.cli(
            "extend-fuse", "--state", str(self.state), "--head", D,
            "--additional-rounds", "1", "--direction", "Allow one bounded round",
        )
        self.assertEqual(code, 0)
        self.assertEqual(extended["decision"], "CONTINUE_LOCAL")

    def test_initial_patch_budget_cannot_exceed_two_round_fuse(self):
        state = self.dir / "over-budget.json"
        code, payload = self.cli(
            "init", "--state", str(state), "--repository", "owner/repo",
            "--pr", "80", "--base-sha", A, "--head-sha", B,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1", "--patch-budget", "3",
        )
        self.assertEqual(code, 2)
        self.assertIn("two rounds", payload["error"])

    def test_expired_initial_deadline_is_rejected(self):
        state = self.dir / "expired.json"
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5))
        deadline = cutoff + timedelta(seconds=90)
        code, payload = self.cli(
            "init", "--state", str(state), "--repository", "owner/repo",
            "--pr", "80", "--base-sha", A, "--head-sha", B,
            "--cutoff", cutoff.isoformat().replace("+00:00", "Z"),
            "--deadline", deadline.isoformat().replace("+00:00", "Z"),
            "--scope-fingerprint", "scope-v1",
        )
        self.assertEqual(code, 2)
        self.assertIn("future", payload["error"])

    def test_initial_cutoff_cannot_expand_the_frozen_batch(self):
        state = self.dir / "future-cutoff.json"
        cutoff = datetime.now(timezone.utc) + timedelta(seconds=6)
        deadline = cutoff + timedelta(seconds=90)
        code, payload = self.cli(
            "init", "--state", str(state), "--repository", "owner/repo",
            "--pr", "80", "--base-sha", A, "--head-sha", B,
            "--cutoff", cutoff.isoformat().replace("+00:00", "Z"),
            "--deadline", deadline.isoformat().replace("+00:00", "Z"),
            "--scope-fingerprint", "scope-v1",
        )
        self.assertEqual(code, 2)
        self.assertIn("cutoff", payload["error"])

    def test_successor_inherits_campaign_patch_rounds(self):
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.patch(B, C)[0], 0)
        self.assertEqual(self.project(C)[0], 0)
        self.assertEqual(self.patch(C, D)[0], 0)
        successor = self.dir / "successor.json"
        self.assertEqual(self.cli(
            "init", "--state", str(successor), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", D,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1",
        )[0], 0)
        state = json.loads(successor.read_text())
        self.assertEqual(state["session"]["patch_rounds"], 2)
        self.assertEqual(state["session"]["automatic_patch_budget"], 2)
        signals = {
            "architecture_verdict": "LOCAL_SAFE", "boundary": "within",
            "premise": "valid", "semantic_delta": "expected",
            "frontier": "shrinking", "coverage": "sufficient",
            "risk": "same_or_lower", "patch_required": True,
            "obligations_complete": False, "obligations_blocked": False,
            "qa_acceptable": False,
        }
        signal_path = self.dir / "successor-signals.json"
        signal_path.write_text(json.dumps(signals))
        code, projected = self.cli(
            "project", "--state", str(successor), "--signals", str(signal_path),
            "--head", D,
        )
        self.assertEqual(code, 0)
        self.assertEqual(projected["decision"], "AUTOMATION_FUSE_EXHAUSTED")
        self.assertEqual(self.cli(
            "guard", "--state", str(successor), "--action", "patch", "--head", D,
        )[0], 3)

    def test_successor_inherits_explicit_fuse_extension(self):
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.patch(B, C)[0], 0)
        self.assertEqual(self.project(C)[0], 0)
        self.assertEqual(self.patch(C, D)[0], 0)
        self.assertEqual(self.project(D)[1]["decision"], "AUTOMATION_FUSE_EXHAUSTED")
        self.assertEqual(self.cli(
            "extend-fuse", "--state", str(self.state), "--head", D,
            "--additional-rounds", "1", "--direction", "Allow one bounded round",
        )[0], 0)
        successor = self.dir / "extended-successor.json"
        self.assertEqual(self.cli(
            "init", "--state", str(successor), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", D,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1",
        )[0], 0)
        state = json.loads(successor.read_text())
        self.assertEqual(state["session"]["automatic_patch_budget"], 3)

    def test_successor_inherits_unresolved_pause(self):
        self.assertEqual(self.project(B, premise="invalid")[0], 0)
        successor = self.dir / "paused-successor.json"
        self.assertEqual(self.cli(
            "init", "--state", str(successor), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", B,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1",
        )[0], 0)
        state = json.loads(successor.read_text())
        self.assertEqual(state["session"]["state"], "PAUSED")
        self.assertEqual(
            state["session"]["pause_reasons"][0]["code"],
            "STRATEGY_RESET_REQUIRED",
        )

    def test_successor_preserves_review_request_history(self):
        self.assertEqual(self.project(
            B, frontier="empty", patch_required=False,
            obligations_complete=True, qa_acceptable=True,
        )[0], 0)
        code, guarded = self.guard("request-review", B)
        self.assertEqual(code, 0)
        self.assertEqual(self.cli(
            "record-review-request", "--state", str(self.state),
            "--authorization", guarded["authorization"], "--head", B,
        )[0], 0)
        successor = self.dir / "reviewed-successor.json"
        self.assertEqual(self.cli(
            "init", "--state", str(successor), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", B,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1",
        )[0], 0)
        self.assertIn(B, json.loads(successor.read_text())["session"]["review_requested_heads"])

    def test_stale_successor_cannot_record_another_patch(self):
        successor = self.dir / "concurrent-successor.json"
        self.assertEqual(self.cli(
            "init", "--state", str(successor), "--repository", "owner/repo",
            "--pr", "79", "--base-sha", A, "--head-sha", B,
            "--cutoff", self.cutoff, "--deadline", self.deadline,
            "--scope-fingerprint", "scope-v1",
        )[0], 0)
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.project_state(successor, B)[0], 0)
        first_code, first_guard = self.guard("patch", B)
        second_code, second_guard = self.guard_state(successor, "patch", B)
        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(self.cli(
            "record-patch", "--state", str(self.state),
            "--authorization", first_guard["authorization"],
            "--from-head", B, "--to-head", C,
        )[0], 0)
        self.assertEqual(self.cli(
            "record-patch", "--state", str(successor),
            "--authorization", second_guard["authorization"],
            "--from-head", B, "--to-head", C,
        )[0], 2)

    def test_campaign_ledger_uses_repository_root_from_subdirectory(self):
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.patch(B, C)[0], 0)
        successor = self.dir / "nested-successor.json"
        with tempfile.TemporaryDirectory(dir=ROOT) as nested:
            self.assertEqual(self.cli(
                "init", "--state", str(successor), "--repository", "owner/repo",
                "--pr", "79", "--base-sha", A, "--head-sha", C,
                "--cutoff", self.cutoff, "--deadline", self.deadline,
                "--scope-fingerprint", "scope-v1", cwd=nested,
            )[0], 0)
        self.assertEqual(json.loads(successor.read_text())["session"]["patch_rounds"], 1)

    def test_strategy_reset_creates_named_pause(self):
        code, payload = self.project(B, premise="invalid")
        self.assertEqual(code, 0)
        self.assertEqual(payload["decision"], "STRATEGY_RESET_REQUIRED")
        state = json.loads(self.state.read_text())
        self.assertEqual(state["session"]["state"], "PAUSED")
        self.assertEqual(
            state["session"]["pause_reasons"][0]["code"],
            "STRATEGY_RESET_REQUIRED",
        )
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.guard("patch", B)[0], 3)

    def test_post_cutoff_blocking_feedback_pauses_and_is_not_admitted(self):
        code, payload = self.cli(
            "defer-feedback", "--state", str(self.state), "--head", B,
            "--thread-id", "late-p1", "--created-at", self.late_feedback_time,
            "--classification", "post-cutoff-blocking", "--reason", "late blocker",
        )
        self.assertEqual(code, 0)
        self.assertFalse(payload["admitted_to_current_session"])
        self.assertEqual(payload["session_state"], "PAUSED")
        self.assertEqual(self.project(B)[0], 0)
        self.assertEqual(self.guard("patch", B)[0], 3)

    def test_later_nonblocking_feedback_is_deferred_not_consumed(self):
        code, payload = self.cli(
            "defer-feedback", "--state", str(self.state), "--head", B,
            "--thread-id", "late-note", "--created-at", self.late_feedback_time,
            "--classification", "later-nonblocking", "--reason", "future session",
        )
        self.assertEqual(code, 0)
        self.assertFalse(payload["admitted_to_current_session"])
        self.assertEqual(payload["session_state"], "OPEN")

    def test_blocking_reply_upgrades_deferred_thread_to_named_pause(self):
        self.assertEqual(self.cli(
            "defer-feedback", "--state", str(self.state), "--head", B,
            "--thread-id", "late-thread", "--created-at", self.late_feedback_time,
            "--classification", "later-nonblocking", "--reason", "future session",
        )[0], 0)
        code, payload = self.cli(
            "defer-feedback", "--state", str(self.state), "--head", B,
            "--thread-id", "late-thread", "--created-at", self.late_feedback_time,
            "--classification", "post-cutoff-blocking", "--reason", "late blocker",
        )
        self.assertEqual(code, 0)
        self.assertFalse(payload["admitted_to_current_session"])
        self.assertEqual(payload["session_state"], "PAUSED")

    def test_review_request_requires_convergence_and_is_once_per_head(self):
        self.assertEqual(self.guard("request-review", B)[0], 3)
        self.assertEqual(self.project(
            B, frontier="empty", patch_required=False,
            obligations_complete=True, qa_acceptable=True,
        )[0], 0)
        code, guarded = self.guard("request-review", B)
        self.assertEqual(code, 0)
        self.assertEqual(self.cli(
            "record-review-request", "--state", str(self.state),
            "--authorization", guarded["authorization"], "--head", B,
        )[0], 0)
        self.assertEqual(self.guard("request-review", B)[0], 3)

    def test_resume_requires_same_head_and_scope_and_records_direction(self):
        self.assertEqual(self.cli(
            "pause", "--state", str(self.state), "--head", B,
            "--pause-id", "strategy", "--code", "STRATEGY_RESET_REQUIRED",
            "--detail", "strategy choice required",
        )[0], 0)
        self.assertEqual(self.cli(
            "resume", "--state", str(self.state), "--head", B,
            "--pause-id", "strategy", "--scope-fingerprint", "changed",
            "--direction", "continue",
        )[0], 2)
        code, payload = self.cli(
            "resume", "--state", str(self.state), "--head", B,
            "--pause-id", "strategy", "--scope-fingerprint", "scope-v1",
            "--direction", "use approved replacement",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["session_state"], "OPEN")


if __name__ == "__main__":
    unittest.main()

"""Persistent state primitives for Review Radius session control."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from evaluate_governor import SignalValidationError, evaluate

SCHEMA_VERSION = 1
DEFAULT_PATCH_BUDGET = 2
MIN_RECHECK_DELAY = timedelta(seconds=90)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ACTIONS = {"patch", "request-review"}
STATES = {"OPEN", "PAUSED", "BLOCKED", "CONVERGED", "STOPPED"}


class StateError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(raw: str, field: str) -> datetime:
    if not raw:
        raise StateError(f"{field} must be a nonempty RFC3339 timestamp")
    value = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateError(f"{field} must be RFC3339: {raw!r}") from exc
    if parsed.tzinfo is None:
        raise StateError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def require_sha(value: str, field: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise StateError(f"{field} must be a 40-character lowercase Git SHA")
    return value


def default_signals(rounds: int, budget: int) -> dict[str, object]:
    return {
        "architecture_verdict": "NOT_ASSESSED",
        "boundary": "unknown",
        "premise": "unknown",
        "semantic_delta": "none",
        "frontier": "stable",
        "coverage": "unknown",
        "risk": "same_or_lower",
        "patch_rounds": rounds,
        "patch_required": False,
        "obligations_complete": False,
        "obligations_blocked": False,
        "qa_acceptable": False,
        "automatic_patch_budget": budget,
    }


def emit(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StateError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StateError(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_state(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA_VERSION:
        raise StateError("unsupported or malformed session state")
    session = raw.get("session")
    campaign = raw.get("campaign")
    if not isinstance(session, dict) or not isinstance(campaign, dict):
        raise StateError("session and campaign must be objects")
    if not isinstance(raw.get("revision"), int) or raw["revision"] < 0:
        raise StateError("revision must be a nonnegative integer")
    if REPO_RE.fullmatch(str(session.get("repository", ""))) is None:
        raise StateError("session.repository must be owner/name")
    if not isinstance(session.get("pr"), int) or session["pr"] <= 0:
        raise StateError("session.pr must be positive")
    for field in ("base_sha", "initial_head", "current_head"):
        require_sha(session.get(field), f"session.{field}")
    cutoff = parse_time(session.get("feedback_cutoff"), "session.feedback_cutoff")
    deadline = parse_time(session.get("recheck_deadline"), "session.recheck_deadline")
    if deadline - cutoff < MIN_RECHECK_DELAY:
        raise StateError("recheck deadline must be at least 90 seconds after cutoff")
    rounds = session.get("patch_rounds")
    budget = session.get("automatic_patch_budget")
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 0:
        raise StateError("patch_rounds must be nonnegative")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise StateError("automatic_patch_budget must be positive")
    if session.get("state") not in STATES or campaign.get("state") not in STATES:
        raise StateError("invalid session or campaign state")
    for field in ("pause_reasons", "deferred_feedback", "review_requested_heads"):
        if not isinstance(session.get(field), list):
            raise StateError(f"session.{field} must be a list")
    if not isinstance(raw.get("signals"), dict) or not isinstance(raw.get("governor"), dict):
        raise StateError("signals and governor must be objects")
    if not isinstance(raw.get("history"), list):
        raise StateError("history must be a list")
    return raw


def load(path: Path) -> dict[str, Any]:
    return validate_state(read_json(path))


def mutate(path: Path, state: dict[str, Any], event: str, **details: object) -> None:
    state["revision"] += 1
    state["session"]["pending_authorization"] = None
    state["history"].append({"at": now(), "event": event, **details})
    state["history"] = state["history"][-256:]
    validate_state(state)
    write_json(path, state)


def head_matches(state: dict[str, Any], observed: str) -> None:
    require_sha(observed, "observed head")
    current = state["session"]["current_head"]
    if observed != current:
        raise StateError(f"stale head: state={current}, observed={observed}")


def authoritative_signals(state: dict[str, Any], projected: object) -> dict[str, object]:
    if not isinstance(projected, dict):
        raise StateError("signals must be a JSON object")
    session = state["session"]
    result = dict(projected)
    for field, expected in (
        ("patch_rounds", session["patch_rounds"]),
        ("automatic_patch_budget", session["automatic_patch_budget"]),
    ):
        if field in result and result[field] != expected:
            raise StateError(f"{field} is controller-owned; expected {expected}")
        result[field] = expected
    try:
        evaluate(result)
    except (TypeError, SignalValidationError) as exc:
        raise StateError(str(exc)) from exc
    return result


def decision(state: dict[str, Any]) -> dict[str, str | None]:
    try:
        return evaluate(state["signals"])
    except (TypeError, SignalValidationError) as exc:
        raise StateError(str(exc)) from exc

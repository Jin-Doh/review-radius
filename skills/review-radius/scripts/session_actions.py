"""CLI actions for the Review Radius executable session controller."""

from __future__ import annotations

import argparse
import fcntl
import subprocess
import uuid
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

from evaluate_governor import evaluate
from session_state import (
    ACTIONS,
    DEFAULT_PATCH_BUDGET,
    MIN_RECHECK_DELAY,
    REPO_RE,
    SCHEMA_VERSION,
    StateError,
    authoritative_signals,
    decision,
    default_signals,
    emit,
    head_matches,
    load,
    mutate,
    now,
    parse_time,
    read_json,
    require_sha,
    validate_state,
    write_json,
)


MAX_CUTOFF_CLOCK_SKEW = timedelta(seconds=5)


def repository_root() -> Path:
    result = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise StateError("controller must run inside the target repository")
    return Path(result.stdout.strip()).resolve()


def campaign_ledger_path(repository: str, pr: int) -> Path:
    return repository_root() / ".review-radius" / "campaigns" / (
        f"{repository.replace('/', '--')}-pr-{pr}.json"
    )


@contextmanager
def campaign_lock(repository: str, pr: int):
    path = campaign_ledger_path(repository, pr).with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def campaign_lineage(
    repository: str,
    pr: int,
    initial_budget: int,
) -> dict[str, Any]:
    path = campaign_ledger_path(repository, pr)
    if not path.exists():
        return {
            "repository": repository,
            "pr": pr,
            "current_head": None,
            "patch_rounds": 0,
            "automatic_patch_budget": initial_budget,
            "pause_reasons": [],
            "review_requested_heads": [],
            "state": "OPEN",
            "pending_authorization": None,
        }
    campaign = read_json(path)
    if not isinstance(campaign, dict):
        raise StateError("campaign lineage must be an object")
    if campaign.get("repository") != repository or campaign.get("pr") != pr:
        raise StateError("campaign lineage does not match repository and PR")
    rounds = campaign.get("patch_rounds")
    budget = campaign.get("automatic_patch_budget")
    if not isinstance(rounds, int) or rounds < 0:
        raise StateError("campaign patch_rounds must be nonnegative")
    if not isinstance(budget, int) or budget <= 0:
        raise StateError("campaign automatic_patch_budget must be positive")
    if not isinstance(campaign.get("pause_reasons"), list):
        raise StateError("campaign pause_reasons must be a list")
    if not isinstance(campaign.get("review_requested_heads"), list):
        raise StateError("campaign review_requested_heads must be a list")
    if campaign.get("state") not in {"OPEN", "PAUSED"}:
        raise StateError("campaign state must be OPEN or PAUSED")
    if campaign.get("pending_authorization") is not None and not isinstance(
        campaign.get("pending_authorization"), dict
    ):
        raise StateError("campaign pending_authorization must be an object or null")
    return campaign


def write_campaign(state: dict[str, Any]) -> None:
    session = state["session"]
    write_json(campaign_ledger_path(session["repository"], session["pr"]), {
        "repository": session["repository"],
        "pr": session["pr"],
        "current_head": session["current_head"],
        "patch_rounds": session["patch_rounds"],
        "automatic_patch_budget": session["automatic_patch_budget"],
        "pause_reasons": session["pause_reasons"],
        "review_requested_heads": session["review_requested_heads"],
        "state": state["campaign"]["state"],
        "pending_authorization": session["pending_authorization"],
    })


def persist_campaign(state: dict[str, Any]) -> None:
    session = state["session"]
    with campaign_lock(session["repository"], session["pr"]):
        write_campaign(state)


def campaign_matches(state: dict[str, Any], campaign: dict[str, Any]) -> bool:
    session = state["session"]
    return (
        campaign["patch_rounds"] == session["patch_rounds"]
        and campaign["automatic_patch_budget"] == session["automatic_patch_budget"]
        and campaign["pause_reasons"] == session["pause_reasons"]
        and campaign["review_requested_heads"] == session["review_requested_heads"]
        and campaign["state"] == state["campaign"]["state"]
        and campaign["current_head"] == session["current_head"]
        and campaign["pending_authorization"] == session["pending_authorization"]
    )


def require_direction(value: str) -> str:
    if not value.strip():
        raise StateError("direction must be nonempty")
    return value


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.state)
    if path.exists():
        raise StateError(f"state already exists: {path}")
    if REPO_RE.fullmatch(args.repository) is None:
        raise StateError("repository must be owner/name")
    base = require_sha(args.base_sha, "base_sha")
    head = require_sha(args.head_sha, "head_sha")
    cutoff = parse_time(args.cutoff, "cutoff")
    deadline = parse_time(args.deadline, "deadline")
    if deadline - cutoff < MIN_RECHECK_DELAY:
        raise StateError("deadline must be at least 90 seconds after cutoff")
    initialized_at = parse_time(now(), "current time")
    if cutoff > initialized_at + MAX_CUTOFF_CLOCK_SKEW:
        raise StateError("cutoff must not be later than initialization")
    if deadline <= initialized_at:
        raise StateError("deadline must be in the future")
    if args.patch_budget <= 0:
        raise StateError("patch budget must be positive")
    if args.patch_budget > DEFAULT_PATCH_BUDGET:
        raise StateError("initial automatic patch budget cannot exceed two rounds")
    campaign = campaign_lineage(
        args.repository,
        args.pr,
        args.patch_budget,
    )
    state: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "session": {
            "id": args.session_id or f"rr-{uuid.uuid4().hex[:12]}",
            "repository": args.repository,
            "pr": args.pr,
            "base_sha": base,
            "initial_head": head,
            "current_head": head,
            "feedback_cutoff": args.cutoff,
            "recheck_deadline": args.deadline,
            "scope_fingerprint": args.scope_fingerprint,
            "initial_thread_ids": sorted(set(args.thread_id)),
            "patch_rounds": campaign["patch_rounds"],
            "automatic_patch_budget": campaign["automatic_patch_budget"],
            "state": campaign["state"],
            "pause_reasons": campaign["pause_reasons"],
            "deferred_feedback": [],
            "review_requested_heads": campaign["review_requested_heads"],
            "pending_authorization": None,
        },
        "campaign": {"state": campaign["state"]},
        "signals": default_signals(
            campaign["patch_rounds"],
            campaign["automatic_patch_budget"],
        ),
        "governor": {
            "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "architecture_verdict": "NOT_ASSESSED",
        },
        "history": [{"at": now(), "event": "initialized", "head": head}],
    }
    validate_state(state)
    write_json(path, state)
    persist_campaign(state)
    emit({"created": True, "session_id": state["session"]["id"], "state": str(path)})
    return 0


def cmd_project(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    session = state["session"]
    with campaign_lock(session["repository"], session["pr"]):
        campaign = campaign_lineage(
            session["repository"], session["pr"], session["automatic_patch_budget"]
        )
        if not campaign_matches(state, campaign):
            raise StateError("session campaign lineage is stale")
        projected = authoritative_signals(state, read_json(Path(args.signals)))
        result = evaluate(projected)
        state["signals"] = projected
        state["governor"] = result
        state["session"]["last_projected_at"] = now()
        if result["decision"] in {
            "STRATEGY_RESET_REQUIRED",
            "AUTOMATION_FUSE_EXHAUSTED",
        }:
            code = result["decision"]
            reasons = state["session"]["pause_reasons"]
            if not any(reason.get("code") == code for reason in reasons):
                reasons.append({
                    "id": code.lower().replace("_", "-"),
                    "code": code,
                    "detail": (
                        "A strategy decision requires recorded explicit direction."
                        if code == "STRATEGY_RESET_REQUIRED"
                        else "Fuse exhaustion requires an explicit extension."
                    ),
                })
            state["session"]["state"] = "PAUSED"
            state["campaign"]["state"] = "PAUSED"
        mutate(path, state, "evidence_projected", head=args.head, decision=result["decision"])
        write_campaign(state)
    emit({"projected": True, **result})
    return 0


def deny(action: str, why: list[str], state: dict[str, Any]) -> int:
    emit({
        "action": action,
        "allowed": False,
        "decision": decision(state)["decision"],
        "reasons": why,
    })
    return 3


def cmd_guard(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    result = decision(state)
    session = state["session"]
    reasons: list[str] = []
    campaign = campaign_lineage(
        session["repository"],
        session["pr"],
        session["automatic_patch_budget"],
    )
    if not campaign_matches(state, campaign):
        reasons.append("session campaign lineage is stale")
    if session["state"] != "OPEN":
        reasons.append(f"session state is {session['state']}")
    if state["campaign"]["state"] != "OPEN":
        reasons.append(f"campaign state is {state['campaign']['state']}")
    if session["pause_reasons"]:
        reasons.append("named pause reason remains")
    if args.action == "patch" and result["decision"] != "CONTINUE_LOCAL":
        reasons.append("patch requires CONTINUE_LOCAL")
    if args.action == "request-review":
        if result["decision"] != "CONVERGED":
            reasons.append("automated review request requires CONVERGED")
        if args.head in session["review_requested_heads"]:
            reasons.append("automated review already requested for this head")
        deadline = parse_time(session["recheck_deadline"], "recheck_deadline")
        current_time = parse_time(now(), "current time")
        projected_at = session.get("last_projected_at")
        if deadline > current_time:
            reasons.append("recheck deadline has not elapsed")
        elif (
            not isinstance(projected_at, str)
            or parse_time(projected_at, "last_projected_at") < deadline
        ):
            reasons.append("convergence must be projected after recheck deadline")
    if reasons:
        return deny(args.action, reasons, state)
    with campaign_lock(session["repository"], session["pr"]):
        campaign = campaign_lineage(
            session["repository"], session["pr"], session["automatic_patch_budget"]
        )
        if not campaign_matches(state, campaign):
            return deny(args.action, ["session campaign lineage is stale"], state)
        if campaign["pending_authorization"] is not None:
            return deny(args.action, ["another campaign action is pending"], state)
        state["revision"] += 1
        token = uuid.uuid4().hex
        session["pending_authorization"] = {
            "token": token,
            "action": args.action,
            "head": args.head,
            "decision": result["decision"],
            "revision": state["revision"],
            "issued_at": now(),
        }
        state["history"].append({
            "at": now(),
            "event": "authorization_issued",
            "action": args.action,
            "head": args.head,
        })
        write_json(path, state)
        write_campaign(state)
    emit({"action": args.action, "allowed": True, "authorization": token, **result})
    return 0


def consume(state: dict[str, Any], token: str, action: str, head: str) -> None:
    auth = state["session"].get("pending_authorization")
    if not isinstance(auth, dict):
        raise StateError("no pending authorization")
    expected = (token, action, head, state["revision"])
    actual = (auth.get("token"), auth.get("action"), auth.get("head"), auth.get("revision"))
    if actual != expected:
        raise StateError("authorization is stale, mismatched, or already consumed")


def cmd_record_patch(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.from_head)
    consume(state, args.authorization, "patch", args.from_head)
    to_head = require_sha(args.to_head, "to_head")
    if to_head == args.from_head:
        raise StateError("to_head must differ from from_head")
    session = state["session"]
    with campaign_lock(session["repository"], session["pr"]):
        campaign = campaign_lineage(
            session["repository"],
            session["pr"],
            session["automatic_patch_budget"],
        )
        if not campaign_matches(state, campaign):
            raise StateError("session campaign lineage is stale")
        session["patch_rounds"] += 1
        session["current_head"] = to_head
        state["signals"] = default_signals(
            session["patch_rounds"], session["automatic_patch_budget"]
        )
        state["governor"] = {
            "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "architecture_verdict": "NOT_ASSESSED",
        }
        mutate(
            path,
            state,
            "patch_recorded",
            from_head=args.from_head,
            to_head=to_head,
            patch_rounds=session["patch_rounds"],
        )
        write_campaign(state)
    emit({"recorded": True, "current_head": to_head, "patch_rounds": session["patch_rounds"]})
    return 0


def cmd_record_review(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    consume(state, args.authorization, "request-review", args.head)
    state["session"]["review_requested_heads"].append(args.head)
    mutate(path, state, "automated_review_requested", head=args.head)
    persist_campaign(state)
    emit({"recorded": True, "head": args.head})
    return 0


def cmd_defer(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    created = parse_time(args.created_at, "created_at")
    cutoff = parse_time(state["session"]["feedback_cutoff"], "feedback_cutoff")
    if created <= cutoff:
        raise StateError("deferred feedback must be created strictly after cutoff")
    deferred = state["session"]["deferred_feedback"]
    existing = next(
        (item for item in deferred if item.get("thread_id") == args.thread_id),
        None,
    )
    if existing is not None:
        if (
            args.classification != "post-cutoff-blocking"
            or existing.get("classification") == "post-cutoff-blocking"
        ):
            raise StateError("thread is already deferred")
        existing.update({
            "created_at": args.created_at,
            "classification": args.classification,
            "reason": args.reason,
        })
    else:
        deferred.append({
            "thread_id": args.thread_id,
            "created_at": args.created_at,
            "classification": args.classification,
            "reason": args.reason,
            "admitted_to_current_session": False,
        })
    if args.classification == "post-cutoff-blocking":
        pause_id = f"post-cutoff-{args.thread_id}"
        if not any(
            reason.get("id") == pause_id
            for reason in state["session"]["pause_reasons"]
        ):
            state["session"]["pause_reasons"].append({
                "id": pause_id,
                "code": "POST_CUTOFF_BLOCKING_FEEDBACK",
                "detail": args.reason,
            })
        state["session"]["state"] = "PAUSED"
        state["campaign"]["state"] = "PAUSED"
    mutate(
        path,
        state,
        "feedback_deferred",
        thread_id=args.thread_id,
        classification=args.classification,
    )
    persist_campaign(state)
    emit({
        "deferred": True,
        "admitted_to_current_session": False,
        "session_state": state["session"]["state"],
    })
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    reasons = state["session"]["pause_reasons"]
    if any(reason.get("id") == args.pause_id for reason in reasons):
        raise StateError("pause id already exists")
    reasons.append({"id": args.pause_id, "code": args.code, "detail": args.detail})
    state["session"]["state"] = "PAUSED"
    state["campaign"]["state"] = "PAUSED"
    mutate(path, state, "paused", pause_id=args.pause_id)
    persist_campaign(state)
    emit({"paused": True, "pause_id": args.pause_id})
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    direction = require_direction(args.direction)
    if args.scope_fingerprint != state["session"]["scope_fingerprint"]:
        raise StateError("scope fingerprint changed; open a successor session")
    reasons = state["session"]["pause_reasons"]
    remaining = [reason for reason in reasons if reason.get("id") != args.pause_id]
    if len(remaining) == len(reasons):
        raise StateError("pause id not found")
    state["session"]["pause_reasons"] = remaining
    if not remaining:
        state["session"]["state"] = "OPEN"
        state["campaign"]["state"] = "OPEN"
    mutate(
        path,
        state,
        "pause_resolved",
        pause_id=args.pause_id,
        direction=direction,
    )
    persist_campaign(state)
    emit({"resumed": True, "session_state": state["session"]["state"]})
    return 0


def cmd_extend(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    direction = require_direction(args.direction)
    if args.additional_rounds <= 0:
        raise StateError("additional_rounds must be positive")
    if decision(state)["decision"] != "AUTOMATION_FUSE_EXHAUSTED":
        raise StateError("fuse may be extended only after AUTOMATION_FUSE_EXHAUSTED")
    session = state["session"]
    session["automatic_patch_budget"] += args.additional_rounds
    state["session"]["pause_reasons"] = [
        reason
        for reason in state["session"]["pause_reasons"]
        if reason.get("code") != "AUTOMATION_FUSE_EXHAUSTED"
    ]
    if not state["session"]["pause_reasons"]:
        state["session"]["state"] = "OPEN"
        state["campaign"]["state"] = "OPEN"
    state["signals"]["automatic_patch_budget"] = session["automatic_patch_budget"]
    state["governor"] = evaluate(state["signals"])
    mutate(
        path,
        state,
        "fuse_extended",
        additional_rounds=args.additional_rounds,
        direction=direction,
    )
    persist_campaign(state)
    emit({
        "extended": True,
        "automatic_patch_budget": session["automatic_patch_budget"],
        **state["governor"],
    })
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    state = load(Path(args.state))
    if args.full:
        emit(state)
    else:
        emit({
            "revision": state["revision"],
            "session_id": state["session"]["id"],
            "current_head": state["session"]["current_head"],
            "patch_rounds": state["session"]["patch_rounds"],
            "automatic_patch_budget": state["session"]["automatic_patch_budget"],
            "session_state": state["session"]["state"],
            "campaign_state": state["campaign"]["state"],
            "pause_reasons": state["session"]["pause_reasons"],
            "deferred_feedback_count": len(state["session"]["deferred_feedback"]),
            **decision(state),
        })
    return 0


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Control a bounded Review Radius session")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--state", required=True)
    init.add_argument("--repository", required=True)
    init.add_argument("--pr", type=int, required=True)
    init.add_argument("--base-sha", required=True)
    init.add_argument("--head-sha", required=True)
    init.add_argument("--cutoff", required=True)
    init.add_argument("--deadline", required=True)
    init.add_argument("--scope-fingerprint", required=True)
    init.add_argument("--session-id")
    init.add_argument("--thread-id", action="append", default=[])
    init.add_argument("--patch-budget", type=int, default=DEFAULT_PATCH_BUDGET)
    init.set_defaults(handler=cmd_init)

    project = commands.add_parser("project")
    project.add_argument("--state", required=True)
    project.add_argument("--signals", required=True)
    project.add_argument("--head", required=True)
    project.set_defaults(handler=cmd_project)

    guard = commands.add_parser("guard")
    guard.add_argument("--state", required=True)
    guard.add_argument("--action", choices=sorted(ACTIONS), required=True)
    guard.add_argument("--head", required=True)
    guard.set_defaults(handler=cmd_guard)

    record_patch = commands.add_parser("record-patch")
    record_patch.add_argument("--state", required=True)
    record_patch.add_argument("--authorization", required=True)
    record_patch.add_argument("--from-head", required=True)
    record_patch.add_argument("--to-head", required=True)
    record_patch.set_defaults(handler=cmd_record_patch)

    record_review = commands.add_parser("record-review-request")
    record_review.add_argument("--state", required=True)
    record_review.add_argument("--authorization", required=True)
    record_review.add_argument("--head", required=True)
    record_review.set_defaults(handler=cmd_record_review)

    defer = commands.add_parser("defer-feedback")
    defer.add_argument("--state", required=True)
    defer.add_argument("--head", required=True)
    defer.add_argument("--thread-id", required=True)
    defer.add_argument("--created-at", required=True)
    defer.add_argument(
        "--classification",
        choices=("later-nonblocking", "post-cutoff-blocking"),
        required=True,
    )
    defer.add_argument("--reason", required=True)
    defer.set_defaults(handler=cmd_defer)

    pause = commands.add_parser("pause")
    pause.add_argument("--state", required=True)
    pause.add_argument("--head", required=True)
    pause.add_argument("--pause-id", required=True)
    pause.add_argument("--code", required=True)
    pause.add_argument("--detail", required=True)
    pause.set_defaults(handler=cmd_pause)

    resume = commands.add_parser("resume")
    resume.add_argument("--state", required=True)
    resume.add_argument("--head", required=True)
    resume.add_argument("--pause-id", required=True)
    resume.add_argument("--scope-fingerprint", required=True)
    resume.add_argument("--direction", required=True)
    resume.set_defaults(handler=cmd_resume)

    extend = commands.add_parser("extend-fuse")
    extend.add_argument("--state", required=True)
    extend.add_argument("--head", required=True)
    extend.add_argument("--additional-rounds", type=int, required=True)
    extend.add_argument("--direction", required=True)
    extend.set_defaults(handler=cmd_extend)

    inspect = commands.add_parser("inspect")
    inspect.add_argument("--state", required=True)
    inspect.add_argument("--full", action="store_true")
    inspect.set_defaults(handler=cmd_inspect)
    return root

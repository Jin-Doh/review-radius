"""CLI actions for the Review Radius executable session controller."""

from __future__ import annotations

import argparse
import uuid
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
    if args.patch_budget <= 0:
        raise StateError("patch budget must be positive")
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
            "patch_rounds": 0,
            "automatic_patch_budget": args.patch_budget,
            "state": "OPEN",
            "pause_reasons": [],
            "deferred_feedback": [],
            "review_requested_heads": [],
            "pending_authorization": None,
        },
        "campaign": {"state": "OPEN"},
        "signals": default_signals(0, args.patch_budget),
        "governor": {
            "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "architecture_verdict": "NOT_ASSESSED",
        },
        "history": [{"at": now(), "event": "initialized", "head": head}],
    }
    validate_state(state)
    write_json(path, state)
    emit({"created": True, "session_id": state["session"]["id"], "state": str(path)})
    return 0


def cmd_project(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    projected = authoritative_signals(state, read_json(Path(args.signals)))
    result = evaluate(projected)
    state["signals"] = projected
    state["governor"] = result
    mutate(path, state, "evidence_projected", head=args.head, decision=result["decision"])
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
    if reasons:
        return deny(args.action, reasons, state)
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
    emit({"recorded": True, "current_head": to_head, "patch_rounds": session["patch_rounds"]})
    return 0


def cmd_record_review(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    consume(state, args.authorization, "request-review", args.head)
    state["session"]["review_requested_heads"].append(args.head)
    mutate(path, state, "automated_review_requested", head=args.head)
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
    if any(item.get("thread_id") == args.thread_id for item in deferred):
        raise StateError("thread is already deferred")
    deferred.append({
        "thread_id": args.thread_id,
        "created_at": args.created_at,
        "classification": args.classification,
        "reason": args.reason,
        "admitted_to_current_session": False,
    })
    if args.classification == "post-cutoff-blocking":
        state["session"]["pause_reasons"].append({
            "id": f"post-cutoff-{args.thread_id}",
            "code": "POST_CUTOFF_BLOCKING_FEEDBACK",
            "detail": args.reason,
        })
        state["session"]["state"] = "PAUSED"
    mutate(
        path,
        state,
        "feedback_deferred",
        thread_id=args.thread_id,
        classification=args.classification,
    )
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
    mutate(path, state, "paused", pause_id=args.pause_id)
    emit({"paused": True, "pause_id": args.pause_id})
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    if args.scope_fingerprint != state["session"]["scope_fingerprint"]:
        raise StateError("scope fingerprint changed; open a successor session")
    reasons = state["session"]["pause_reasons"]
    remaining = [reason for reason in reasons if reason.get("id") != args.pause_id]
    if len(remaining) == len(reasons):
        raise StateError("pause id not found")
    state["session"]["pause_reasons"] = remaining
    if not remaining:
        state["session"]["state"] = "OPEN"
    mutate(
        path,
        state,
        "pause_resolved",
        pause_id=args.pause_id,
        direction=args.direction,
    )
    emit({"resumed": True, "session_state": state["session"]["state"]})
    return 0


def cmd_extend(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load(path)
    head_matches(state, args.head)
    if args.additional_rounds <= 0:
        raise StateError("additional_rounds must be positive")
    if decision(state)["decision"] != "AUTOMATION_FUSE_EXHAUSTED":
        raise StateError("fuse may be extended only after AUTOMATION_FUSE_EXHAUSTED")
    session = state["session"]
    session["automatic_patch_budget"] += args.additional_rounds
    state["signals"]["automatic_patch_budget"] = session["automatic_patch_budget"]
    state["governor"] = evaluate(state["signals"])
    mutate(
        path,
        state,
        "fuse_extended",
        additional_rounds=args.additional_rounds,
        direction=args.direction,
    )
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

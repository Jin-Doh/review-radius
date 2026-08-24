#!/usr/bin/env python3
"""Evaluate an architecture-aware review-radius governor decision.

The evaluator intentionally has no repository or service dependencies. It
accepts the compact, independently projected signal packet used by the review
governor and returns the next decision together with that architecture verdict.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final


_DECISIONS: Final[tuple[str, ...]] = (
    "CONTINUE_LOCAL",
    "IMPACT_REVIEW_REQUIRED",
    "STRATEGY_RESET_REQUIRED",
    "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
    "AUTOMATION_FUSE_EXHAUSTED",
    "CONVERGED",
)
_ARCHITECTURE_VERDICTS: Final[tuple[str, ...]] = (
    "NOT_ASSESSED",
    "LOCAL_SAFE",
    "APPROVED_EXPANSION",
    "STRATEGY_REVIEW_REQUIRED",
    "BLOCKED",
)
_ACCEPTABLE_BOUNDARIES: Final[dict[str, str]] = {
    "LOCAL_SAFE": "within",
    "APPROVED_EXPANSION": "approved_expansion",
}


_ENUMS: Final[dict[str, tuple[str, ...]]] = {
    "architecture_verdict": _ARCHITECTURE_VERDICTS,
    "boundary": ("within", "approved_expansion", "expanded", "unknown"),
    "premise": ("valid", "invalid", "unknown"),
    "semantic_delta": ("none", "expected", "new_dimension"),
    "frontier": ("empty", "shrinking", "stable", "expanding", "regressing"),
    "coverage": ("sufficient", "low_risk_gap", "high_risk_gap"),
    "risk": ("same_or_lower", "higher"),
}
_REQUIRED: Final[tuple[str, ...]] = (
    "architecture_verdict",
    "boundary",
    "premise",
    "semantic_delta",
    "frontier",
    "coverage",
    "risk",
    "patch_rounds",
    "patch_required",
    "obligations_complete",
    "obligations_blocked",
    "qa_acceptable",
)
_ALLOWED: Final[frozenset[str]] = frozenset((*_REQUIRED, "automatic_patch_budget"))


class SignalValidationError(ValueError):
    """Raised when a governor signal packet is malformed."""


def _validate_signals(signals: dict[str, object]) -> dict[str, object]:
    if not isinstance(signals, dict):
        raise TypeError("signals must be a dictionary")

    missing = [name for name in _REQUIRED if name not in signals]
    if missing:
        raise SignalValidationError(
            "missing required signal(s): " + ", ".join(missing)
        )

    unknown = sorted(set(signals) - _ALLOWED)
    if unknown:
        raise SignalValidationError(
            "unknown signal(s): " + ", ".join(unknown)
        )

    for name, allowed in _ENUMS.items():
        value = signals[name]
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
        if value not in allowed:
            choices = ", ".join(allowed)
            raise SignalValidationError(
                f"{name} must be one of {choices}; got {value!r}"
            )

    patch_rounds = signals["patch_rounds"]
    if isinstance(patch_rounds, bool) or not isinstance(patch_rounds, int):
        raise TypeError("patch_rounds must be a nonnegative integer")
    if patch_rounds < 0:
        raise SignalValidationError("patch_rounds must be nonnegative")

    budget = signals.get("automatic_patch_budget", 2)
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("automatic_patch_budget must be a positive integer")
    if budget <= 0:
        raise SignalValidationError("automatic_patch_budget must be positive")

    for name in (
        "obligations_complete",
        "obligations_blocked",
        "patch_required",
        "qa_acceptable",
    ):
        value = signals[name]
        if not isinstance(value, bool):
            raise TypeError(f"{name} must be a boolean")

    normalized = dict(signals)
    normalized["automatic_patch_budget"] = budget
    return normalized


def _strategy_signal(signals: dict[str, object]) -> bool:
    return (
        signals["architecture_verdict"] == "STRATEGY_REVIEW_REQUIRED"
        or signals["premise"] == "invalid"
        or signals["boundary"] == "expanded"
        or signals["semantic_delta"] == "new_dimension"
        or signals["risk"] == "higher"
    )


def _acceptable_verdict_boundary_mismatch(signals: dict[str, object]) -> bool:
    expected_boundary = _ACCEPTABLE_BOUNDARIES.get(signals["architecture_verdict"])
    return expected_boundary is not None and signals["boundary"] != expected_boundary



def _insufficient_evidence(signals: dict[str, object]) -> bool:
    return (
        signals["obligations_blocked"]
        or signals["architecture_verdict"] in {"NOT_ASSESSED", "BLOCKED"}
        or _acceptable_verdict_boundary_mismatch(signals)
        or signals["coverage"] != "sufficient"
        or signals["boundary"] == "unknown"
        or signals["premise"] == "unknown"
        or (
            signals["frontier"] == "empty"
            and (
                not signals["obligations_complete"]
                or not signals["qa_acceptable"]
            )
        )
        or (
            not signals["patch_required"]
            and signals["frontier"] != "empty"
        )
    )


def _impact_review_required(signals: dict[str, object]) -> bool:
    return signals["frontier"] in {"stable", "expanding", "regressing"}


def _architecture_verdict(signals: dict[str, object]) -> str:
    """Return the independently projected architecture assessment."""
    return signals["architecture_verdict"]


def evaluate(signals: dict[str, object]) -> dict[str, str | None]:
    """Evaluate one governor signal packet.

    Decision precedence is deliberately explicit and mirrors the policy:
    strategy reset, insufficient evidence (including blocked mandatory
    obligations), impact review, convergence, the automatic fuse, then local
    continuation. The fuse only limits further automatic patch rounds; it is
    never used as evidence that the review has converged or that a strategy
    has failed.
    """
    values = _validate_signals(signals)
    architecture_verdict = _architecture_verdict(values)

    strategy_signal = _strategy_signal(values)
    insufficient_evidence = _insufficient_evidence(values)
    impact_required = _impact_review_required(values)
    acceptable_architecture = architecture_verdict in {
        "LOCAL_SAFE",
        "APPROVED_EXPANSION",
    }
    locally_actionable = (
        values["patch_required"]
        and values["frontier"] == "shrinking"
        and acceptable_architecture
    )

    if strategy_signal:
        decision = "STRATEGY_RESET_REQUIRED"
    elif insufficient_evidence:
        decision = "INSUFFICIENT_ARCHITECTURE_EVIDENCE"
    elif impact_required:
        decision = "IMPACT_REVIEW_REQUIRED"
    elif (
        values["frontier"] == "empty"
        and values["obligations_complete"]
        and values["qa_acceptable"]
        and acceptable_architecture
        and not values["patch_required"]
    ):
        decision = "CONVERGED"
    elif locally_actionable and values["patch_rounds"] >= values["automatic_patch_budget"]:
        decision = "AUTOMATION_FUSE_EXHAUSTED"
    elif locally_actionable:
        decision = "CONTINUE_LOCAL"
    else:
        decision = "INSUFFICIENT_ARCHITECTURE_EVIDENCE"

    return {
        "decision": decision,
        "architecture_verdict": architecture_verdict,
    }


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <signals.json>", file=sys.stderr)
        return 2

    try:
        with Path(argv[1]).open(encoding="utf-8") as stream:
            signals = json.load(stream)
        result = evaluate(signals)
    except (OSError, json.JSONDecodeError, TypeError, SignalValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))

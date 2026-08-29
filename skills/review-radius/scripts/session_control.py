#!/usr/bin/env python3
"""Persist Review Radius state and gate patch/reviewer side effects.

The model projects evidence. The controller owns head identity, cutoff,
deadline, patch rounds, deferred feedback, pauses, and single-use action
authorizations. Exit codes: 0 success/allowed, 2 invalid/stale, 3 denied.
"""

from __future__ import annotations

import sys

from session_actions import build_parser
from session_state import StateError, emit


def main(argv: list[str]) -> int:
    try:
        args = build_parser().parse_args(argv[1:])
        return args.handler(args)
    except StateError as exc:
        emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

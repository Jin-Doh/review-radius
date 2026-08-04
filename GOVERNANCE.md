# Governance

## Maintainer

Review Radius is currently maintained by [@Jin-Doh](https://github.com/Jin-Doh).
The maintainer owns roadmap, release, security, and merge decisions.

## Decision process

Changes are evaluated against the documented product boundary: a review comment
starts a bounded audit of the defect class it reveals. Decisions prioritize
evidence, the canonical `review-radius` install and invocation contract, and a
reviewable scope.

## Review model

The repository intentionally requires zero approving reviews while there is
only one human maintainer. Requiring one human approval would make every
maintainer-authored pull request impossible to merge.

This does not permit unreviewed direct pushes. Pull requests, the required
`quality` check, resolved review conversations, and squash-only merging remain
mandatory. Automated Codex review supplies another inspection signal but does
not hold decision authority and is not counted as a human approval.

The maintainer has a pull-request-only ruleset bypass for recovery when a broken
required check would otherwise prevent repairing the check itself. The bypass
must not be used for convenience, and the reason must be recorded in the pull
request.

## Future maintainers

When at least two active human maintainers can review each other's work, the
approval count may be raised to one after confirming that emergency and absence
coverage remain workable. The policy change must update the repository ruleset,
the checked-in ruleset source, and this document together.

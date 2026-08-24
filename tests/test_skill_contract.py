"""Run the complete skill contract against the progressive-disclosure surface."""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_SKILL = ROOT / "skills/review-radius/SKILL.md"
OPERATIONAL_POLICY = ROOT / "skills/review-radius/operational-policy.md"
SUITE = ROOT / "tests/skill_contract_suite.py"
OPENAI = ROOT / "skills/review-radius/agents/openai.yaml"


class CompositePolicySurface:
    """Path-like view used by semantic tests after policy decomposition.

    Runtime agents receive only the compact SKILL.md automatically. The detailed
    operational contract remains available on demand. Existing semantic tests
    intentionally evaluate both files as one policy surface so progressive
    disclosure cannot weaken the behavior contract.
    """

    def __init__(self, core: Path, detail: Path) -> None:
        self.core = core
        self.detail = detail

    @property
    def name(self) -> str:
        return self.core.name

    def read_text(self, encoding: str | None = None, errors: str | None = None) -> str:
        kwargs = {"encoding": encoding or "utf-8"}
        if errors is not None:
            kwargs["errors"] = errors
        core = self.core.read_text(**kwargs).rstrip()
        detail = self.detail.read_text(**kwargs).rstrip()
        # Keep the lossless pre-refactor policy first for legacy section-anchor
        # tests, then append the compact routing surface. Runtime loading remains
        # unchanged: agents receive CORE_SKILL first and load detail on demand.
        return f"{detail}\n\n{core}"

    def read_bytes(self) -> bytes:
        return self.read_text().encode("utf-8")

    def is_file(self) -> bool:
        return self.core.is_file() and self.detail.is_file()

    def exists(self) -> bool:
        return self.is_file()

    def __fspath__(self) -> str:
        return os.fspath(self.core)

    def __str__(self) -> str:
        return str(self.core)

    def __truediv__(self, other: object) -> Path:
        return self.core / other  # type: ignore[arg-type]

    def __getattr__(self, name: str):
        return getattr(self.core, name)


spec = importlib.util.spec_from_file_location("review_radius_skill_contract_suite", SUITE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load contract suite: {SUITE}")
_suite = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = _suite
spec.loader.exec_module(_suite)
_suite.SKILL = CompositePolicySurface(CORE_SKILL, OPERATIONAL_POLICY)


class SkillContractTest(_suite.SkillContractTest):
    def test_review_churn_frontmatter_and_openai_prompt_share_session_contract(self):
        core = CORE_SKILL.read_text()
        frontmatter = re.match(r"^---\n(.*?)\n---\n", core, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        assert frontmatter is not None
        description = frontmatter.group(1)
        for pattern in (
            r"(?i)repeated\s+github\s+pr\s+review/fix\s+cycles",
            r"(?i)github\s+pr\s+review\s+churn",
            r"(?i)non-converging\s+github\s+pr\s+feedback",
        ):
            self.assertRegex(description, pattern)

        self.assertNotRegex(
            description,
            r"(?i)\b(?:general|broad|repository-wide)\s+"
            r"(?:code|repository)\s+review\b",
        )
        self.assertNotRegex(
            core,
            r"(?i)\b(?:always|automatically)\s+(?:run|invoke)\s+"
            r"\$?review-radius\b",
        )
        self.assertRegex(
            core,
            r"(?is)skill cannot.{0,80}(?:monitor|dispatch|call|invoke)"
            r".{0,80}itself.{0,80}not\s+selected",
        )

        openai = OPENAI.read_text()
        prompt_match = re.search(
            r'(?m)^  default_prompt:\s*"([^"]+)"\s*$',
            openai,
        )
        self.assertIsNotNone(prompt_match)
        assert prompt_match is not None
        prompt = prompt_match.group(1).lower()
        for term in (
            "$review-radius",
            "pr review",
            "persisted session state",
            "head-bound guard",
            "patch",
            "automated review request",
            "post-cutoff feedback",
            "current session",
        ):
            with self.subTest(term=term):
                self.assertIn(term, prompt)

        self.assertLessEqual(len(prompt), 280)
        self.assertEqual(prompt.count("."), 1)
        self.assertNotIn("architecture context packet", prompt)
        self.assertNotIn("obligations_blocked", prompt)

    def test_progressive_disclosure_keeps_core_compact_and_policy_complete(self):
        core = CORE_SKILL.read_text()
        detail = OPERATIONAL_POLICY.read_text()
        combined = _suite.SKILL.read_text()

        self.assertLess(len(core.splitlines()), 500)
        self.assertLess(len(core.encode("utf-8")), 18_000)
        self.assertGreater(len(detail.encode("utf-8")), len(core.encode("utf-8")))

        for link in (
            "operational-policy.md",
            "references/executable-session-control.md",
            "references/review-governor.md",
            "references/review-campaign.md",
            "references/code-navigation.md",
        ):
            with self.subTest(link=link):
                self.assertIn(link, core)

        for detailed_heading in (
            "## Review Session",
            "## Workflow",
            "## Completion contract",
        ):
            with self.subTest(heading=detailed_heading):
                self.assertNotIn(detailed_heading, core)
                self.assertIn(detailed_heading, detail)
                self.assertIn(detailed_heading, combined)

        self.assertIn("Do not load every detailed policy file by default", core)
        self.assertIn("read only the relevant section", core.lower())
        self.assertIn("complete pre-refactor contract", core)

    def test_composite_contract_surface_uses_real_files(self):
        surface = _suite.SKILL
        self.assertTrue(surface.is_file())
        self.assertEqual(surface.name, "SKILL.md")
        self.assertTrue(CORE_SKILL.is_file())
        self.assertTrue(OPERATIONAL_POLICY.is_file())
        self.assertIn(CORE_SKILL.read_text(), surface.read_text())
        self.assertIn(OPERATIONAL_POLICY.read_text(), surface.read_text())

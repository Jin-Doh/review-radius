import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/review-radius/SKILL.md"
CAMPAIGN = ROOT / "skills/review-radius/references/review-campaign.md"
GOVERNOR = ROOT / "skills/review-radius/references/review-governor.md"
DESIGN = ROOT / "docs/design.md"


class ReviewCampaignContractTest(unittest.TestCase):
    def test_skill_preserves_campaign_history_across_sessions(self):
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        campaign = re.sub(r"\s+", " ", CAMPAIGN.read_text().lower())

        self.assertIn("## review campaign", skill)
        self.assertRegex(
            skill,
            r"starting a new session never resets campaign",
        )
        self.assertIn("references/review-campaign.md", skill)
        self.assertRegex(
            skill,
            r"new session is not a fuse reset|fresh session id.{0,80}"
            r"(?:not|never).{0,40}automatic authorization",
        )

        # A campaign may call this a "successor session" or a "successor
        # Review Session"; neither terminology change may drop lineage.
        self.assertRegex(
            campaign,
            r"\bsuccessor(?:\s+review)?\s+session\b",
        )
        self.assertRegex(
            campaign,
            r"(?:preserve|preserves|inherit|inherits).{0,220}"
            r"(?:prior|immutable|historical)|"
            r"(?:prior|immutable|historical).{0,220}"
            r"(?:preserve|preserves|inherit|inherits)",
        )
        self.assertRegex(
            campaign,
            r"without\s+rewriting|unchanged|immutable",
        )

        for field in (
            r"(?:prior|immutable)\s+(?:immutable\s+)?session\s+id",
            r"frozen[-\s]+(?:head(?:\s*/\s*snapshot)?|snapshot)",
            r"(?:cutoff\s*(?:and|/)\s*cursor|"
            r"cursor\s*(?:and|/)\s*cutoff)\s+evidence",
            r"qa\s+verdict",
            r"delivery\s+state",
        ):
            with self.subTest(preserved_field=field):
                self.assertRegex(campaign, field)

        # The successor owns current fields; it must not overwrite the
        # historical outcome it inherited.
        self.assertRegex(campaign, r"(?:own|its own)\s+current")
        self.assertRegex(campaign, r"separately|separate\s+fields")

    def test_finding_origin_taxonomy_is_complete(self):
        text = SKILL.read_text() + CAMPAIGN.read_text()

        for origin in (
            "ORIGINAL_DEFECT",
            "SAME_INVARIANT",
            "REMEDIATION_REGRESSION",
            "MECHANISM_DEFECT",
            "INDEPENDENT",
        ):
            with self.subTest(origin=origin):
                self.assertIn(origin, text)

    def test_governor_is_normative_ssot_and_linked_from_policy_surfaces(self):
        governor = GOVERNOR.read_text()
        skill = SKILL.read_text()
        design = DESIGN.read_text()

        self.assertRegex(
            skill.lower(),
            r"single\s+normative\s+(?:human/agent\s+)?policy",
        )
        self.assertIn("references/review-governor.md", skill)
        self.assertIn("references/review-governor.md", design)
        self.assertIn("normative", governor.lower())
        for text in (skill, design):
            self.assertIn("Architecture Context Packet", text)
        self.assertIn("Architecture Context Packet", governor)

    def test_governor_exposes_decisions_and_architecture_verdicts(self):
        governor = GOVERNOR.read_text()

        for decision in (
            "CONTINUE_LOCAL",
            "IMPACT_REVIEW_REQUIRED",
            "STRATEGY_RESET_REQUIRED",
            "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "AUTOMATION_FUSE_EXHAUSTED",
            "CONVERGED",
        ):
            with self.subTest(decision=decision):
                self.assertIn(decision, governor)

        for verdict in (
            "NOT_ASSESSED",
            "LOCAL_SAFE",
            "APPROVED_EXPANSION",
            "STRATEGY_REVIEW_REQUIRED",
            "BLOCKED",
        ):
            with self.subTest(verdict=verdict):
                self.assertIn(verdict, governor)

    def test_fuse_exhaustion_is_not_strategy_failure(self):
        text = " ".join(
            (GOVERNOR.read_text() + SKILL.read_text() + CAMPAIGN.read_text()).split()
        ).lower()

        self.assertRegex(
            text,
            r"automation_fuse_exhausted.{0,1200}"
            r"non_converging_remediation_strategy",
        )
        self.assertRegex(
            text,
            r"(?is)automation_fuse_exhausted.{0,500}"
            r"(?:not|never).{0,100}(?:convergence|strategy)",
        )

    def test_removed_numeric_mechanism_thresholds_are_not_normative(self):
        for path in (SKILL, CAMPAIGN):
            text = path.read_text().lower()
            self.assertNotIn("after three automatic patch rounds", text)
            self.assertNotIn(
                "across at least two patch-producing review sessions",
                text,
            )
    def test_governor_pauses_on_evidence_not_comment_counts(self):
        text = re.sub(
            r"\s+",
            " ",
            (GOVERNOR.read_text() + CAMPAIGN.read_text()).lower(),
        )

        # Keep comment-count context and its non-decisional meaning separate:
        # either clause may be rewrapped or moved by the policy editors.
        self.assertRegex(text, r"\bcomment\s+count\b")
        self.assertRegex(
            text,
            r"\b(?:not|never)\s+(?:a\s+)?(?:defect\s+unit|decision)|"
            r"\b(?:cannot|never)\s+(?:replace|decide)\b",
        )
        self.assertRegex(text, r"\bhistorical\s+count/churn\b")
        self.assertRegex(text, r"\bdescriptive(?:\s+trend)?\b")

    def test_session_pauses_do_not_hide_campaign_convergence_state(self):
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        campaign = re.sub(r"\s+", " ", CAMPAIGN.read_text().lower())

        self.assertRegex(skill, r"paused\s+session")
        self.assertRegex(
            skill,
            r"(?:cannot|must not|not).{0,100}`?converged`?",
        )
        self.assertRegex(skill, r"qa\s+verdict")
        self.assertRegex(
            skill,
            r"qa\s+verdict\s+does\s+not\s+(?:create|resolve)",
        )
        self.assertRegex(skill, r"review-convergence\s+pause")
        self.assertRegex(campaign, r"session-level")
        self.assertRegex(campaign, r"campaign\s+`?open`?")
        self.assertIn("Review-campaign model", DESIGN.read_text())

    def test_paused_campaign_forbids_patch_and_reviewer_retrigger(self):
        text = re.sub(
            r"\s+",
            " ",
            (SKILL.read_text() + CAMPAIGN.read_text()).lower(),
        )

        # These are independent prohibitions. Avoid coupling them to the
        # paragraph order used by the campaign reference.
        self.assertRegex(text, r"(?:strategy\s+pause|non_converging_remediation_strategy)")
        self.assertRegex(
            text,
            r"(?:do not|must not|never)\s+(?:modify|patch)\s+code|"
            r"(?:do not|must not|never)\s+patch",
        )
        self.assertRegex(
            text,
            r"(?:do not|must not|never)\s+trigger.{0,100}"
            r"(?:@codex\s+review|automated\s+reviewer)",
        )
        self.assertRegex(
            text,
            r"(?:fresh|new)\s+review\s+session.{0,100}"
            r"(?:budget\s+reset|reset.*budget)|"
            r"(?:budget\s+reset|reset.*budget).{0,100}"
            r"(?:fresh|new)\s+review\s+session",
        )
    def test_independent_and_duplicate_findings_do_not_inflate_churn(self):
        campaign = re.sub(r"\s+", " ", CAMPAIGN.read_text())
        self.assertIn("keep `INDEPENDENT` findings separate", campaign)
        self.assertRegex(
            campaign,
            r"(?is)duplicate.{0,160}(?:not|without).{0,120}"
            r"(?:frontier identity|decision)",
        )

if __name__ == "__main__":
    unittest.main()

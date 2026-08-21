import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/review-radius/SKILL.md"
CAMPAIGN = ROOT / "skills/review-radius/references/review-campaign.md"
DESIGN = ROOT / "docs/design.md"


class ReviewCampaignContractTest(unittest.TestCase):
    def test_skill_preserves_campaign_history_across_sessions(self):
        skill = SKILL.read_text()

        self.assertIn("## Review Campaign", skill)
        self.assertIn("Starting a new session never resets campaign", skill)
        self.assertIn("references/review-campaign.md", skill)
        self.assertIn("A new session is not a budget reset", skill)

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

    def test_governor_pauses_non_converging_mechanisms(self):
        skill = SKILL.read_text()
        campaign = CAMPAIGN.read_text()

        self.assertIn("NON_CONVERGING_REMEDIATION_STRATEGY", skill)
        self.assertIn("Three fresh `MECHANISM_DEFECT` findings", campaign)
        self.assertIn("Two consecutive patch-producing Review Sessions", campaign)
        self.assertIn("material strategy premise is disproved", campaign)
        self.assertIn("Repeated `MECHANISM_DEFECT` evidence", skill)

    def test_session_pauses_do_not_hide_campaign_convergence_state(self):
        skill = SKILL.read_text()
        campaign = CAMPAIGN.read_text()
        design = DESIGN.read_text()

        self.assertIn("Ordinary feedback that needs user direction pauses only the active Review", skill)
        self.assertIn("Ordinary Review Session pauses do not mutate the campaign state", campaign)
        self.assertIn("`CONVERGED`", campaign)
        self.assertIn("original PR goal and safe boundary are complete", campaign)
        self.assertIn("Review-campaign model", design)

    def test_three_mechanism_findings_require_multiple_patch_sessions(self):
        campaign = CAMPAIGN.read_text()

        self.assertIn("across at least two patch-producing Review Sessions", campaign)
        self.assertIn("do not count three findings first observed in one patch-producing Review", campaign)
        self.assertIn("one incomplete patch", campaign)

    def test_paused_campaign_forbids_patch_and_reviewer_retrigger(self):
        text = SKILL.read_text() + CAMPAIGN.read_text()

        self.assertIn("do not patch", text)
        self.assertIn("`@codex review`", text)
        self.assertIn("zero unresolved threads", text)
        self.assertIn("Further patch authorized: no", text)
        self.assertIn("Automated reviewer trigger authorized: no", text)

    def test_independent_and_duplicate_findings_do_not_inflate_churn(self):
        campaign = CAMPAIGN.read_text()

        self.assertIn("Independent defects and duplicate comments", SKILL.read_text())
        self.assertIn("One hundred duplicate comments", campaign)
        self.assertIn("keep `INDEPENDENT` findings separate", campaign)


if __name__ == "__main__":
    unittest.main()

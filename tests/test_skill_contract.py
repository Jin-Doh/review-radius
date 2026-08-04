import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/review-response/SKILL.md"
NAVIGATION = ROOT / "skills/review-response/references/code-navigation.md"
EXPERIMENT = ROOT / "docs/experiments/2026-08-04-code-navigation-tool-routing.md"
RESULTS = ROOT / "experiments/tool-routing/results/latest.json"
sys.path.insert(0, str(ROOT / "experiments/tool-routing"))
from run_benchmark import normalize_rg_output  # noqa: E402


class SkillContractTest(unittest.TestCase):
    def test_ripgrep_proxy_normalization_removes_timing_variance(self):
        first = (
            '{"type":"summary","data":{"elapsed_total":{"nanos":1},'
            '"stats":{"elapsed":{"nanos":1},"bytes_printed":99,'
            '"matches":2}}}\n'
        )
        second = (
            '{"data":{"stats":{"matches":2,"bytes_printed":101,'
            '"elapsed":{"nanos":900}},"elapsed_total":{"nanos":900}},'
            '"type":"summary"}\n'
        )
        self.assertEqual(normalize_rg_output(first), normalize_rg_output(second))

    def test_skill_frontmatter_and_progressive_reference(self):
        text = SKILL.read_text()
        frontmatter = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        self.assertRegex(frontmatter.group(1), r"(?m)^name: review-response$")
        self.assertRegex(frontmatter.group(1), r"(?m)^description: .+$")
        self.assertIn("references/code-navigation.md", text)
        self.assertTrue(NAVIGATION.is_file())

    def test_navigation_contract_covers_routing_and_trust_boundaries(self):
        text = NAVIGATION.read_text()
        for capability in ("`rg`", "AST", "LSP", "Graphify", "runtime"):
            self.assertIn(capability, text)
        for provenance in (
            "text-matched",
            "AST-matched",
            "graph-extracted",
            "graph-inferred",
            "LSP-resolved",
            "runtime-proven",
        ):
            self.assertIn(provenance, text)
        for boundary in ("fresh", "stale", "fallback", "coverage gap"):
            self.assertIn(boundary, text.lower())
        for ledger_field in (
            "Candidate",
            "Anchor",
            "Relation",
            "Provenance",
            "Freshness or confidence",
            "Disposition",
        ):
            self.assertIn(ledger_field, text)

    def test_recorded_experiment_supports_only_the_declared_mechanism(self):
        data = json.loads(RESULTS.read_text())
        methods = {method["name"]: method for method in data["methods"]}
        compact = methods["routed-compact"]
        raw = methods["rg+raw"]
        graph = methods["graphify-query"]
        self.assertEqual((compact["recall"], compact["precision"]), (1.0, 1.0))
        self.assertLess(compact["estimated_tokens"], raw["estimated_tokens"])
        self.assertIn("rotateCredential", graph["missed"])

        report = EXPERIMENT.read_text()
        reduction = (1 - compact["estimated_tokens"] / raw["estimated_tokens"]) * 100
        self.assertIn("synthetic", report.lower())
        self.assertIn("does not establish", report)
        self.assertIn(f"{reduction:.2f}%", report)
        self.assertIn("nondeterministic fields", report)
        self.assertIn("interpreted directionally", report)
        self.assertIn("agent-level scenario", report)


if __name__ == "__main__":
    unittest.main()

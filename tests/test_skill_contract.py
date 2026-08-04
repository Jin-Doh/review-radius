import json
import re
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/review-response/SKILL.md"
NAVIGATION = ROOT / "skills/review-response/references/code-navigation.md"
EXPERIMENT = ROOT / "docs/experiments/2026-08-04-code-navigation-tool-routing.md"
RESULTS = ROOT / "experiments/tool-routing/results/latest.json"
README = ROOT / "README.md"
README_KO = ROOT / "README.ko.md"
README_ZH_CN = ROOT / "README.zh-CN.md"
BRAND = ROOT / "BRAND.md"
BRAND_KO = ROOT / "BRAND.ko.md"
BRAND_ZH_CN = ROOT / "BRAND.zh-CN.md"
BRAND_MESSAGES = ROOT / "brand/messages.json"
BRAND_VALIDATION = ROOT / "docs/brand/name-and-language-validation.md"
MARK = ROOT / "assets/review-radius-mark.svg"
HERO = ROOT / "assets/readme/review-radius-hero.png"
WORKFLOW_VISUAL = ROOT / "assets/readme/review-radius-workflow.png"
OPENAI = ROOT / "skills/review-response/agents/openai.yaml"
LICENSE = ROOT / "LICENSE"
sys.path.insert(0, str(ROOT / "experiments/tool-routing"))
from run_benchmark import normalize_rg_output  # noqa: E402


class SkillContractTest(unittest.TestCase):
    def test_brand_contract_preserves_the_stable_skill_identity(self):
        skill = SKILL.read_text()
        readme = README.read_text()
        brand = BRAND.read_text()
        openai = OPENAI.read_text()

        self.assertIn("# Review Radius", skill)
        self.assertIn("Fix the pattern behind the comment.", readme)
        self.assertIn("`review-response`", brand)
        self.assertIn("name: review-response", skill)
        self.assertIn("Review Radius", openai)
        self.assertTrue(README_KO.is_file())

    def test_brand_locales_are_complete_and_match_the_message_registry(self):
        messages = json.loads(BRAND_MESSAGES.read_text())
        self.assertEqual(set(messages["locales"]), {"en", "ko", "zh-CN"})
        self.assertEqual(messages["skillId"], "review-response")

        for locale, config in messages["locales"].items():
            with self.subTest(locale=locale):
                readme = ROOT / config["readme"]
                brand_guide = ROOT / config["brandGuide"]
                self.assertTrue(readme.is_file())
                self.assertTrue(brand_guide.is_file())
                self.assertIn(config["primaryLine"], readme.read_text())
                self.assertIn(config["primaryLine"], brand_guide.read_text())

        self.assertEqual(messages["locales"]["zh-CN"]["script"], "Hans")
        self.assertEqual(messages["locales"]["zh-CN"]["region"], "CN")

    def test_language_navigation_and_validation_boundaries_are_visible(self):
        for path in (README, README_KO, README_ZH_CN):
            text = path.read_text()
            for target in ("README.md", "README.ko.md", "README.zh-CN.md"):
                if path.name != target:
                    self.assertIn(target, text)

        validation = BRAND_VALIDATION.read_text()
        self.assertIn("reviewradius.com", validation)
        self.assertIn("Trademark availability is unresolved", validation)
        self.assertIn("`zh-CN`, not `Zn`", validation)

    def test_mit_license_is_canonical_and_visible_in_every_locale(self):
        license_text = LICENSE.read_text()
        self.assertTrue(license_text.startswith("MIT License\n\n"))
        self.assertIn("Copyright (c) 2026 KyungHo Kim", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        self.assertIn(
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND',
            license_text,
        )
        self.assertTrue(license_text.endswith("SOFTWARE.\n"))

        for readme in (README, README_KO, README_ZH_CN):
            with self.subTest(readme=readme.name):
                self.assertIn("[MIT License](LICENSE)", readme.read_text())

        self.assertNotIn("currently has no license file", BRAND.read_text())

    def test_brand_mark_is_valid_accessible_svg(self):
        root = ET.parse(MARK).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertEqual(root.tag, f"{namespace}svg")
        self.assertEqual(root.attrib.get("role"), "img")
        self.assertIsNotNone(root.find(f"{namespace}title"))
        self.assertIsNotNone(root.find(f"{namespace}desc"))

    def test_readme_visuals_are_valid_shared_png_assets(self):
        expected_dimensions = {
            HERO: (1600, 640),
            WORKFLOW_VISUAL: (1400, 788),
        }
        for path, expected in expected_dimensions.items():
            with self.subTest(path=path.name):
                data = path.read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), expected)
                self.assertLess(len(data), 1_100_000)

        for readme in (README, README_KO, README_ZH_CN):
            with self.subTest(readme=readme.name):
                text = readme.read_text()
                self.assertIn("assets/readme/review-radius-hero.png", text)
                self.assertIn("assets/readme/review-radius-workflow.png", text)

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

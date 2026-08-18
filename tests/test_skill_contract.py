import json
import re
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/review-radius/SKILL.md"
DESIGN = ROOT / "docs/design.md"
NAVIGATION = ROOT / "skills/review-radius/references/code-navigation.md"
EXPERIMENT = ROOT / "docs/experiments/2026-08-04-code-navigation-tool-routing.md"
RESULTS = ROOT / "experiments/tool-routing/results/latest.json"
README = ROOT / "README.md"
README_KO = ROOT / "README.ko.md"
README_ZH_CN = ROOT / "README.zh-CN.md"
BRAND = ROOT / "BRAND.md"
BRAND_KO = ROOT / "BRAND.ko.md"
BRAND_ZH_CN = ROOT / "BRAND.zh-CN.md"
BRAND_MESSAGES = ROOT / "brand/messages.json"
BRAND_NAMING = ROOT / "docs/brand/naming-and-language.md"
BRAND_RESEARCH_STATE = (
    ROOT / "RESEARCH/review_radius_brand_validation_20260804_044208/state.json"
)
RULESET = ROOT / ".github/rulesets/main.json"
QUALITY_WORKFLOW = ROOT / ".github/workflows/quality.yml"
CODEOWNERS = ROOT / ".github/CODEOWNERS"
MARK = ROOT / "assets/review-radius-mark.svg"
HERO = ROOT / "assets/readme/review-radius-hero.png"
WORKFLOW_VISUAL = ROOT / "assets/readme/review-radius-workflow.png"
OPENAI = ROOT / "skills/review-radius/agents/openai.yaml"
LICENSE = ROOT / "LICENSE"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
sys.path.insert(0, str(ROOT / "experiments/tool-routing"))
from run_benchmark import normalize_rg_output  # noqa: E402


class SkillContractTest(unittest.TestCase):
    def test_brand_contract_uses_one_canonical_skill_identity(self):
        skill = SKILL.read_text()
        readme = README.read_text()
        brand = BRAND.read_text()
        openai = OPENAI.read_text()

        self.assertIn("# Review Radius", skill)
        self.assertIn("Fix the pattern behind the comment.", readme)
        self.assertIn("`review-radius`", brand)
        self.assertIn("name: review-radius", skill)
        self.assertIn("Review Radius", openai)
        self.assertTrue(README_KO.is_file())

    def test_brand_locales_are_complete_and_match_the_message_registry(self):
        messages = json.loads(BRAND_MESSAGES.read_text())
        self.assertEqual(set(messages["locales"]), {"en", "ko", "zh-CN"})
        self.assertEqual(messages["skillId"], "review-radius")

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

    def test_language_navigation_and_naming_boundaries_are_visible(self):
        for path in (README, README_KO, README_ZH_CN):
            text = path.read_text()
            for target in ("README.md", "README.ko.md", "README.zh-CN.md"):
                if path.name != target:
                    self.assertIn(target, text)

        naming = BRAND_NAMING.read_text()
        self.assertIn("`zh-CN`, not `Zn`", naming)
        self.assertIn("Skill folder and frontmatter", naming)
        self.assertIn("working records", naming)
        self.assertIn("product introduction", naming)

        prohibited_product_copy = (
            "reviewradius.com",
            "public collision screen",
            "공개 충돌 점검",
            "公开冲突检查",
            "trademark clearance remains unresolved",
        )
        for path in (
            README,
            README_KO,
            README_ZH_CN,
            BRAND,
            BRAND_KO,
            BRAND_ZH_CN,
        ):
            with self.subTest(path=path.name):
                text = path.read_text()
                for phrase in prohibited_product_copy:
                    self.assertNotIn(phrase, text)

    def test_active_surfaces_do_not_expose_a_legacy_skill_alias(self):
        legacy_id = "review" + "-response"
        active_paths = (
            README,
            README_KO,
            README_ZH_CN,
            BRAND,
            BRAND_KO,
            BRAND_ZH_CN,
            BRAND_MESSAGES,
            SKILL,
            OPENAI,
            ROOT / ".github/ISSUE_TEMPLATE/feature_request.yml",
        )
        for path in active_paths:
            with self.subTest(path=path):
                self.assertNotIn(legacy_id, path.read_text())

        self.assertFalse((ROOT / "skills" / legacy_id).exists())

    def test_historical_brand_validation_remains_bound_to_its_snapshot(self):
        state = json.loads(BRAND_RESEARCH_STATE.read_text())
        artifact_path = ROOT / state["artifacts"]["repository_validation"]
        artifact = artifact_path.read_text()

        self.assertTrue(artifact_path.is_file())
        self.assertIn("Observed: 2026-08-04", artifact)
        self.assertIn("preserve\n`review-response`", artifact)
        self.assertIn("## Collision screen", artifact)
        self.assertNotEqual(artifact_path, BRAND_NAMING)

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

    def test_graphify_use_has_versioned_third_party_attribution(self):
        notice = THIRD_PARTY_NOTICES.read_text()
        self.assertIn("https://github.com/Graphify-Labs/graphify", notice)
        self.assertIn("graphifyy==0.9.32", notice)
        self.assertIn("v0.9.32/LICENSE", notice)
        self.assertIn("v0.9.32/NOTICE", notice)
        self.assertIn("Apache License 2.0", notice)
        self.assertIn("not vendored", notice)
        self.assertNotIn("Graphify", LICENSE.read_text())

        for readme in (README, README_KO, README_ZH_CN):
            with self.subTest(readme=readme.name):
                text = readme.read_text()
                self.assertIn("graphifyy==0.9.32", text)
                self.assertIn("(THIRD_PARTY_NOTICES.md)", text)

        for path in (
            ROOT / "experiments/tool-routing/README.md",
            EXPERIMENT,
        ):
            with self.subTest(path=path):
                self.assertIn("../../THIRD_PARTY_NOTICES.md", path.read_text())

    def test_public_repository_policy_avoids_single_maintainer_deadlock(self):
        ruleset = json.loads(RULESET.read_text())
        rules = {rule["type"]: rule for rule in ruleset["rules"]}
        pull_request = rules["pull_request"]["parameters"]
        checks = rules["required_status_checks"]["parameters"]

        self.assertEqual(pull_request["required_approving_review_count"], 0)
        self.assertFalse(pull_request["require_code_owner_review"])
        self.assertFalse(pull_request["require_last_push_approval"])
        self.assertTrue(pull_request["required_review_thread_resolution"])
        self.assertEqual(pull_request["allowed_merge_methods"], ["squash"])
        self.assertEqual(
            {item["context"] for item in checks["required_status_checks"]},
            {"quality"},
        )
        self.assertTrue(checks["strict_required_status_checks_policy"])
        self.assertEqual(
            {rule_type for rule_type in rules},
            {
                "deletion",
                "non_fast_forward",
                "required_linear_history",
                "pull_request",
                "required_status_checks",
            },
        )
        self.assertEqual(ruleset["bypass_actors"][0]["bypass_mode"], "pull_request")

    def test_public_repository_community_and_ci_contract(self):
        workflow = QUALITY_WORKFLOW.read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("name: quality", workflow)
        self.assertIn(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            workflow,
        )
        self.assertIn("fetch-depth: 2", workflow)
        self.assertIn("python3 -m unittest discover -s tests -v", workflow)
        self.assertIn("markdownlint-cli2@0.23.2", workflow)
        self.assertIn("skills@1.5.21", workflow)
        self.assertEqual(CODEOWNERS.read_text().strip(), "* @Jin-Doh")

        for path in (
            ROOT / "CONTRIBUTING.md",
            ROOT / "SECURITY.md",
            ROOT / "GOVERNANCE.md",
            ROOT / ".github/PULL_REQUEST_TEMPLATE.md",
            ROOT / ".github/dependabot.yml",
        ):
            self.assertTrue(path.is_file(), path)

        for readme in (README, README_KO, README_ZH_CN):
            text = readme.read_text()
            self.assertIn("https://github.com/Jin-Doh/review-radius", text)
            self.assertNotIn("<repository-url>", text)

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
        self.assertRegex(frontmatter.group(1), r"(?m)^name: review-radius$")
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


    def test_design_and_skill_bind_review_sessions_to_a_frozen_snapshot(self):
        design = DESIGN.read_text().lower()
        skill = SKILL.read_text().lower()

        for term in (
            "review session",
            "initial thread cursor",
            "queued",
            "current head",
        ):
            with self.subTest(term=term):
                self.assertIn(term, design)
                self.assertIn(term, skill)

        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?is)new head.{0,180}(?:evidence|snapshot)",
            )

        for text in (design, skill):
            for term in (
                "server-comparable cutoff",
                "createdat",
                "high-water",
                "closed-set reconciliation",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, text)
        self.assertGreaterEqual(skill.count("headrefoid"), 4)
        self.assertRegex(
            skill,
            r"(?is)headrefoid.{0,180}(?:verification|delivery|write)",
        )

    def test_design_and_skill_bound_rounds_and_do_not_count_churn_as_work(self):
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?i)\btwo\s+(?:automatic\s+)?(?:patch\s+)?rounds?\b",
            )
            self.assertRegex(text, r"(?i)two[- ]pass")
            self.assertRegex(
                text,
                r"(?is)(?:duplicate|reply-only).{0,220}"
                r"(?:does not|do not|without).{0,100}"
                r"(?:consume|count).{0,80}round",
            )

    def test_design_and_skill_pause_expansion_and_keep_the_deadline_bounded(self):
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?is)new defect class.{0,160}\bpaus",
            )
            self.assertRegex(
                text,
                r"(?i)(?:fixed|bounded)\s+observation\s+deadline",
            )
            self.assertIn("deadline", text.lower())
            self.assertRegex(
                text,
                r"(?is)(?:does not|do not|not).{0,80}reset",
            )

        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?is)transition\s+`PAUSED\s*->\s*OPEN`\s+only\s+while"
                r".{0,120}head,\s+cutoff,\s+and\s+scope\s+assumptions"
                r".{0,80}remain\s+valid.{0,80}otherwise\s+start\s+a\s+new"
                r"\s+session",
            )
            lowered = text.lower()
            self.assertRegex(lowered, r"paused\s+session")
            self.assertIn("cannot", lowered)
            self.assertIn("converged", lowered)
            self.assertRegex(
                text,
                r"(?is)budget exhaustion pauses only when.{0,80}patch",
            )
            self.assertRegex(
                text,
                r"(?is)(?:duplicate|reply-only).{0,160}"
                r"(?:no-code|budget-exhaustion pause)",
            )

    def test_design_and_skill_keep_convergence_qa_and_delivery_independent(self):
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        for text in (design, skill):
            lowered = text.lower()
            for category in (
                "review convergence",
                "qa verdict",
                "delivery state",
            ):
                with self.subTest(category=category):
                    self.assertIn(category, lowered)
            self.assertRegex(
                text,
                r"(?is)(?:three\s+independent|independent).{0,120}"
                r"(?:outcomes|states|review convergence|qa verdict)",
            )
            self.assertRegex(
                text,
                r"(?is)(?:fail|blocked|incomplete).{0,120}"
                r"(?:never|cannot|does not).{0,100}"
                r"(?:success|complete)",
            )
            self.assertRegex(
                text,
                r"(?is)qa verdict does not.{0,80}(?:create|resolve)"
                r".{0,80}review-convergence pause",
            )
            self.assertNotRegex(
                text,
                r"(?is)mandatory qa.{0,120}pauses? (?:the )?(?:review )?session",
            )

    def test_strategy_gate_and_optional_traceknot_semantics_are_explicit(self):
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        for text in (design, skill):
            lowered = text.lower()
            for term in (
                "build-versus-buy",
                "direct implementation",
                "follow-up",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, lowered)
            self.assertRegex(lowered, r"existing\s+(?:project\s+)?dependency")
            self.assertRegex(lowered, r"new\s+open-source")
            self.assertRegex(
                text,
                r"(?is)explicit\s+user\s+approval.{0,140}"
                r"production\s+dependenc",
            )

        self.assertRegex(
            skill,
            r"(?is)(?:optional|not an unconditional dependency).{0,160}"
            r"traceknot|traceknot.{0,160}(?:optional|unconditional)",
        )
        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?is)(?:required qa handoff.{0,120}`?R2`?/`?R3`?|"
                r"`?R2`?/`?R3`?.{0,120}required qa handoff)"
                r".{0,180}recurring.{0,80}review loop",
            )
        for text in (design, skill):
            lowered = text.lower()
            self.assertIn("selected or required", lowered)
            self.assertRegex(
                text,
                r"(?is)unavailable\s+required\s+capability.{0,100}`BLOCKED`",
            )
            self.assertRegex(
                text,
                r"(?is)(?:available\s+capability|capability\s+exists).{0,180}"
                r"(?:unfinished|does\s+not\s+reach).{0,120}`INCOMPLETE`",
            )
        self.assertNotRegex(
            skill,
            r"(?i)\b(?:always|automatically)\s+(?:run|invoke|use)\s+traceknot\b",
        )

        for text in (design, skill):
            lowered = text.lower()
            self.assertIn("material comparison premise", lowered)
            reopen = re.search(
                r"(?is)reopen\s+(?:the\s+)?decision\s+when"
                r"(?P<premises>.*?)materially\s+change",
                text,
            )
            self.assertIsNotNone(reopen)
            invalidation_premises = reopen.group("premises").lower()
            for premise in (
                "implementation size",
                "requirement",
                "maintenance",
                "security",
                "license",
                "dependency",
                "performance",
                "integration",
                "replacement",
            ):
                with self.subTest(premise=premise):
                    self.assertIn(premise, invalidation_premises)
            self.assertRegex(
                text,
                r"(?is)reuse it only while.{0,120}premises remain valid",
            )
        self.assertRegex(
            skill,
            r"(?is)neither selected nor required.{0,180}"
            r"traceknot absence alone does not block",
        )

    def test_pushed_head_verification_precedes_review_writes(self):
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        for text in (design, skill):
            lowered = text.lower()
            for term in (
                "pre-push",
                "after push",
                "candidate evidence",
                "cannot satisfy",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, lowered)
            self.assertRegex(lowered, r"pushed\s+sha")
        self.assertRegex(
            skill,
            r"(?is)after push.{0,700}(?:rerun|verify).{0,180}"
            r"(?:focused|canonical)",
        )
        self.assertRegex(
            skill,
            r"(?is)re-read\s+`?headrefoid`?.{0,120}"
            r"before any github write, including reactions",
        )
        intake = re.search(
            r"(?is)10\. validate reaction dispositions.*?(?=\n11\.)",
            skill,
        )
        response = re.search(
            r"(?is)13\. push, rebind, and verify.*?(?=\n14\.)",
            skill,
        )
        self.assertIsNotNone(intake)
        self.assertIsNotNone(response)
        self.assertNotRegex(
            intake.group(0),
            r"(?im)^\s*-\s*(?:add|write|react)\b",
        )
        response_text = response.group(0)
        normalized_response = re.sub(r"\s+", " ", response_text)
        self.assertLess(
            response_text.index("After push, read the remote head"),
            response_text.index("Add the recorded reactions"),
        )
        self.assertIn(
            "immediately before any GitHub write, including reactions",
            normalized_response,
        )
        self.assertIn(
            "Add the recorded reactions only after that final head reread and "
            "the pushed-head verification",
            normalized_response,
        )
        self.assertIn(
            "require it to equal the recorded pushed commit SHA",
            normalized_response,
        )
        self.assertRegex(
            normalized_response,
            r"(?is)if it differs.{0,180}"
            r"invalidate delivery and qa readiness.{0,120}"
            r"(?:rebind|verification)",
        )
        self.assertIn("Reactions are dispositions during intake", design)

    def test_pushed_head_verification_is_snapshot_bound(self):
        design = re.sub(r"\s+", " ", DESIGN.read_text().lower())
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        for text in (design, skill):
            for term in (
                "unrelated uncommitted edits",
                "clean detached or temporary worktree",
                "recorded sha",
                "preserve the source worktree",
                "not snapshot-bound",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, text)

    def test_risk_levels_define_traceknot_selection(self):
        design = DESIGN.read_text().lower()
        skill = SKILL.read_text().lower()
        for text in (design, skill):
            for level in ("r0", "r1", "r2", "r3"):
                with self.subTest(level=level):
                    self.assertIn(f"`{level}`", text)
            self.assertRegex(
                text,
                r"(?is)r3.{0,240}(?:supersedes|higher level).{0,120}"
                r"r2",
            )
            self.assertRegex(
                text,
                r"(?is)traceknot.{0,120}(?:mandatory|required).{0,120}"
                r"r2",
            )
            for term in (
                "release, migration, destructive operation",
                "production infrastructure",
                "unknown material scope",
                "public-contract",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, text)
            self.assertRegex(
                text,
                r"(?is)(?:post-cutoff|same-class blocking).{0,160}"
                r"(?:after the cutoff|pause|follow-up)",
            )

    def test_late_replies_use_their_own_cutoff_timestamp(self):
        design = DESIGN.read_text().lower()
        skill = SKILL.read_text().lower()
        for text in (design, skill):
            normalized = re.sub(r"\s+", " ", text)
            for term in (
                "each newly observed comment or reply",
                "frozen parent thread does not make a late reply current",
                "same-class blocking comment or reply",
                "after the cutoff",
                "non-blocking comments and replies",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, normalized)
            self.assertRegex(
                normalized,
                r"(?is)same-class blocking comment or reply.{0,180}"
                r"(?:named `?paused|named pause|follow-up)",
            )

    def test_openai_short_description_matches_distribution_length_contract(self):
        openai = OPENAI.read_text()
        match = re.search(r'(?m)^  short_description: "([^"]+)"$', openai)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(len(match.group(1)), 25)
        self.assertLessEqual(len(match.group(1)), 64)

    def test_review_churn_frontmatter_and_openai_prompt_share_session_contract(self):
        skill = SKILL.read_text()
        frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(frontmatter)
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
            skill,
            r"(?i)\b(?:always|automatically)\s+(?:run|invoke)\s+"
            r"\$?review-radius\b",
        )
        self.assertRegex(
            skill,
            r"(?is)skill cannot.{0,80}(?:monitor|dispatch|call|invoke)"
            r".{0,80}itself.{0,80}not\s+selected",
        )

        openai = OPENAI.read_text()
        prompt_match = re.search(
            r'(?m)^  default_prompt:\s*"([^"]+)"\s*$',
            openai,
        )
        self.assertIsNotNone(prompt_match)
        prompt = prompt_match.group(1).lower()
        for term in (
            "$review-radius",
            "repo",
            "pr",
            "head",
            "initial thread cursor",
            "non-blocking",
            "queue",
            "new defect class",
            "strategy decision",
            "duplicate",
            "round",
            "new head",
            "new evidence",
            "qa verdict",
            "delivery",
            "independent",
        ):
            with self.subTest(term=term):
                self.assertIn(term, prompt)

    def test_locale_summaries_expose_the_bounded_session_contract(self):
        markers = {
            README: (
                "## Bounded review sessions",
                "default automatic patch budget is **two rounds**",
                "Traceknot",
                "QA handoff",
                "Review convergence and",
                "QA verdict remain separate",
                "Explicitly invoking `$review-radius` is the most reliable",
            ),
            README_KO: (
                "## 제한된 리뷰 세션",
                "기본 자동 패치 예산은 **두 라운드**",
                "Traceknot",
                "QA 핸드오프",
                "리뷰 수렴과 QA 판정은 서로",
                "별개입니다",
                "$review-radius",
                "명시적으로 호출",
            ),
            README_ZH_CN: (
                "## 有边界的审查会话",
                "默认自动补丁预算为 **两轮**",
                "Traceknot",
                "QA 交接",
                "审查收敛和 QA 判定彼此独立",
                "明确调用 `$review-radius` 是",
            ),
        }
        for path, phrases in markers.items():
            text = path.read_text()
            with self.subTest(locale=path.name):
                for phrase in phrases:
                    self.assertIn(phrase, text)
                self.assertNotRegex(
                    text,
                    r"(?i)\b(?:always|automatically)\s+"
                    r"(?:invoke|call|run)\s+\$?review-radius\b",
                )
if __name__ == "__main__":
    unittest.main()

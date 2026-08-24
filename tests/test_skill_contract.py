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
GOVERNOR = ROOT / "skills/review-radius/references/review-governor.md"
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

    def test_skills_sh_publication_and_install_contract(self):
        for readme in (README, README_KO, README_ZH_CN):
            text = readme.read_text()
            with self.subTest(readme=readme.name):
                self.assertIn(
                    "https://skills.sh/Jin-Doh/review-radius/review-radius",
                    text,
                )
                self.assertIn(
                    "https://skills.sh/b/Jin-Doh/review-radius",
                    text,
                )
                self.assertRegex(
                    text,
                    r"npx skills add Jin-Doh/review-radius\b",
                )
                self.assertIn("--skill review-radius", text)

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
        surfaces = {
            "design": DESIGN.read_text().lower(),
            "skill": SKILL.read_text().lower(),
        }

        for name, text in surfaces.items():
            normalized = re.sub(r"\s+", " ", text)
            with self.subTest(surface=name):
                for term in (
                    "review session",
                    "initial thread cursor",
                    "queued",
                    "current head",
                ):
                    with self.subTest(term=term):
                        self.assertIn(term, normalized)

                # Keep this as intent-level coverage: wording and line wrapping
                # may move the snapshot binding details around.
                self.assertRegex(
                    normalized,
                    r"(?:new|current)\s+head",
                )
                self.assertRegex(normalized, r"\b(?:frozen|snapshot)\b")
                self.assertRegex(
                    normalized,
                    r"(?:bind|bound|freeze|frozen).{0,180}"
                    r"(?:head|snapshot)|"
                    r"(?:head|snapshot).{0,180}"
                    r"(?:bind|bound|freeze|frozen)",
                )

                for term in (
                    "server-comparable cutoff",
                    "createdat",
                    "high-water",
                    "closed-set reconciliation",
                ):
                    with self.subTest(term=term):
                        self.assertIn(term, normalized)

                # Both policy surfaces describe the pushed-head evidence and
                # its QA/delivery consequence.  The per-write guard itself is
                # an operational instruction and is checked only on SKILL.
                self.assertRegex(normalized, r"\bafter\s+push\b")
                self.assertRegex(normalized, r"\bremote\s+head\b")
                self.assertRegex(
                    normalized,
                    r"(?:recorded|pushed|commit)\s+(?:commit\s+)?sha|"
                    r"(?:commit\s+)?sha.{0,100}pushed",
                )
                self.assertRegex(
                    normalized,
                    r"(?:equal|equality).{0,180}"
                    r"(?:recorded|pushed).{0,100}sha|"
                    r"(?:recorded|pushed).{0,100}sha.{0,180}"
                    r"(?:equal|equality)",
                )
                self.assertRegex(
                    normalized,
                    r"(?:pre-push evidence|pre-push results).{0,180}"
                    r"(?:cannot satisfy|insufficient).{0,100}"
                    r"(?:pushed-head|pushed head|qa|verification)",
                )
                self.assertRegex(
                    normalized,
                    r"(?:delivery|qa).{0,220}"
                    r"(?:pushed[- ]head|pushed sha)|"
                    r"(?:pushed[- ]head|pushed sha).{0,220}"
                    r"(?:delivery|qa)",
                )


        skill = re.sub(r"\s+", " ", surfaces["skill"])
        self.assertRegex(
            skill,
            r"before\s+every\s+github\s+write.{0,180}"
            r"(?:re-?read|read).{0,140}"
            r"(?:headref(?:oid)?|remote\s+head)",
        )
        self.assertRegex(
            skill,
            r"(?:each\s+reaction|reaction).{0,100}"
            r"(?:each\s+reply|reply).{0,100}"
            r"(?:resolution|write)",
        )
        self.assertRegex(
            skill,
            r"(?:do not reuse one reread as the guard|"
            r"do not reuse one head reread|"
            r"own immediate remote-head reread)",
        )
    def test_architecture_context_packet_is_governor_ssot_and_linked(self):
        governor = re.sub(r"\s+", " ", GOVERNOR.read_text().lower())
        design = DESIGN.read_text()
        skill = SKILL.read_text()

        self.assertIn("architecture context packet", governor)
        for pattern in (
            r"base.{0,40}head.{0,40}sha",
            r"original goal.{0,80}non-goal",
            "approved boundary",
            "architecture baseline",
            "components",
            "dependencies",
            "public contract",
            "persistence",
            "ownership",
            "runtime flow",
            "dynamic gap",
            "mechanism",
            "strategy premises",
            "impact delta",
            "defect frontier",
            "verification obligations",
        ):
                self.assertRegex(governor, pattern)

        self.assertIn(
            "(invariant_id, mechanism_id, boundary_id, obligation_id)",
            GOVERNOR.read_text(),
        )
        for trend in ("empty", "shrinking", "stable", "expanding", "regressing"):
            with self.subTest(trend=trend):
                self.assertIn(f"`{trend}`", governor)
        for text in (design, skill):
            self.assertIn("Architecture Context Packet", text)
            self.assertIn("references/review-governor.md", text)
            self.assertIn("impact delta", text.lower())
            self.assertIn("defect frontier", text.lower())
            self.assertIn("verification obligations", text.lower())

    def test_obligations_blocked_is_required_boolean_and_not_incomplete(self):
        surfaces = {
            "skill": SKILL.read_text(),
            "design": DESIGN.read_text(),
            "governor": GOVERNOR.read_text(),
        }
        for name, text in surfaces.items():
            lowered = re.sub(r"\s+", " ", text.lower())
            with self.subTest(surface=name):
                self.assertRegex(lowered, r"\bobligations_blocked\b")
                self.assertRegex(
                    lowered,
                    r"obligations_blocked.{0,220}"
                    r"(?:required|independent).{0,100}boolean",
                )
                self.assertRegex(
                    lowered,
                    r"obligations_blocked.{0,240}\btrue\b.{0,240}\bfalse\b",
                )
                self.assertRegex(
                    lowered,
                    r"obligations_blocked.{0,420}"
                    r"(?:distinct|separate|independent).{0,180}"
                    r"(?:incomplete|obligations_complete)",
                )
                self.assertRegex(
                    lowered,
                    r"obligations_blocked.{0,1200}"
                    r"insufficient_architecture_evidence",
                )

        precedence = re.sub(
            r"\s+",
            " ",
            self._markdown_section(
                surfaces["governor"],
                "Precedence-ordered decision table",
            ).lower(),
        )
        markers = {
            marker: precedence.find(marker)
            for marker in (
                "strategy_reset_required",
                "obligations_blocked",
                "insufficient_architecture_evidence",
                "impact_review_required",
                "converged",
                "automation_fuse_exhausted",
                "continue_local",
            )
        }
        self.assertTrue(all(position >= 0 for position in markers.values()))
        self.assertLess(
            markers["strategy_reset_required"],
            markers["obligations_blocked"],
        )
        for later in (
            "insufficient_architecture_evidence",
            "impact_review_required",
            "converged",
            "automation_fuse_exhausted",
            "continue_local",
        ):
            with self.subTest(precedence=later):
                self.assertLess(markers["obligations_blocked"], markers[later])

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
            normalized = re.sub(r"\s+", " ", text.lower())
            self.assertRegex(
                normalized,
                r"(?is)transition\s+`PAUSED\s*->\s*OPEN`\s+only\s+while"
                r".{0,160}head,\s+cutoff,\s+and\s+scope\s+assumptions"
                r"\s+remain\s+valid.{0,220}"
                r"\bremain\s+[`']?PAUSED[`']?.{0,220}"
                r"\brecorded\s+explicit\s+user\s+direction\s+selects\s+a\s+"
                r"successor\s+(?:review\s+)?session\b.{0,160}"
                r"\breview\s+campaign\s+independently\s+permits\b",
            )
            lowered = text.lower()
            self.assertRegex(lowered, r"paused\s+session")
            self.assertIn("cannot", lowered)
            self.assertIn("converged", lowered)
            self.assertIn("AUTOMATION_FUSE_EXHAUSTED", text)
            self.assertIn("NON_CONVERGING_REMEDIATION_STRATEGY", text)
            budget_to_fuse = re.search(
                r"(?is)(?:two|2).{0,80}(?:round|patch).{0,120}"
                r"(?:fuse|circuit breaker)",
                normalized,
            )
            fuse_to_budget = re.search(
                r"(?is)(?:fuse|circuit breaker).{0,120}"
                r"(?:two|2).{0,80}(?:round|patch)",
                normalized,
            )
            self.assertTrue(
                budget_to_fuse or fuse_to_budget,
                "two-round/budget exhaustion must be an automatic fuse or circuit breaker",
            )
            self.assertRegex(
                normalized,
                r"(?is)(?:(?:automatic|automation).{0,80}"
                r"(?:authority|(?:safety\s+)?fuse|circuit breaker)|"
                r"(?:authority|(?:safety\s+)?fuse|circuit breaker).{0,80}"
                r"(?:automatic|automation))",
            )
            fuse_marker = re.search(r"automation_fuse_exhausted", normalized)
            strategy_marker = re.search(
                r"non_converging_remediation_strategy",
                normalized,
            )
            self.assertIsNotNone(fuse_marker)
            self.assertIsNotNone(strategy_marker)
            assert fuse_marker is not None
            assert strategy_marker is not None
            distinction_window = normalized[
                min(fuse_marker.start(), strategy_marker.start()) : max(
                    fuse_marker.end(), strategy_marker.end()
                )
            ]
            self.assertRegex(
                distinction_window,
                r"(?is)(?:not|distinct|separate|different|rather than|"
                r"instead of|independent|while|whereas|versus)",
            )
            self.assertRegex(
                text,
                r"(?is)(?:duplicate|reply-only).{0,160}"
                r"(?:no-code|budget-exhaustion pause)",
            )

    @staticmethod
    def _markdown_section(text, heading):
        lines = text.splitlines()
        heading_pattern = re.compile(
            rf"^(?P<level>#+)\s+{re.escape(heading)}\s*$",
            re.IGNORECASE,
        )
        for index, line in enumerate(lines):
            match = heading_pattern.match(line)
            if match is None:
                continue

            level = len(match.group("level"))
            end = len(lines)
            for candidate_index in range(index + 1, len(lines)):
                next_heading = re.match(r"^(#+)\s+\S", lines[candidate_index])
                if next_heading and len(next_heading.group(1)) <= level:
                    end = candidate_index
                    break
            return "\n".join(lines[index + 1 : end])

        raise AssertionError(f"missing markdown section: {heading}")

    @classmethod
    def _completion_outcome_bullets(cls, text):
        section = cls._markdown_section(text, "Completion contract")
        bullets = []
        current = []
        for line in section.splitlines():
            if re.match(r"^-\s+\S", line):
                if current:
                    bullets.append(current)
                current = [line]
            elif current:
                current.append(line)
        if current:
            bullets.append(current)

        normalized = [
            re.sub(
                r"^-\s+",
                "",
                re.sub(
                    r"\s+",
                    " ",
                    re.sub(r"[`*~]", "", " ".join(lines).lower()),
                ).strip(),
            )
            for lines in bullets
        ]
        return section, normalized

    @staticmethod
    def _completion_bullet(bullets, label):
        matches = [bullet for bullet in bullets if re.match(label, bullet)]
        if len(matches) != 1:
            raise AssertionError(
                f"expected one completion bullet matching {label!r}, "
                f"found {len(matches)}"
            )
        return matches[0]


    def test_design_skill_and_governor_keep_patch_axis_and_outcomes_independent(self):
        surfaces = {
            "design": DESIGN.read_text(),
            "skill": SKILL.read_text(),
            "governor": GOVERNOR.read_text(),
        }

        for name, text in surfaces.items():
            semantic = re.sub(r"[`*~]", "", text.lower())
            lowered = re.sub(r"\s+", " ", semantic)
            with self.subTest(surface=name):
                self.assertIn("patch_required", lowered)
                self.assertRegex(
                    lowered,
                    r"(?:required|explicit|independent)\s+boolean|"
                    r"true\s*(?:\||or)\s*false",
                )
                self.assertRegex(
                    lowered,
                    r"patch_required.{0,220}independent|"
                    r"independent.{0,220}patch_required",
                )
                self.assertRegex(
                    lowered,
                    r"(?:no|never|not).{0,100}"
                    r"architecture\s+verdict.{0,120}"
                    r"(?:determin|set|decid|infer).{0,120}"
                    r"patch_required|"
                    r"patch_required.{0,220}"
                    r"(?:independent|patch[- ]plane)",
                )
                self.assertRegex(lowered, r"patch_required\s*:\s*false")
                false_alone_insufficiency = (
                    r"patch_required\s*:\s*false\s+alone\s+"
                    r"(?:is\s+not\s+proof|"
                    r"does\s+not\s+prove|"
                    r"must\s+not(?:\s+\w+){0,5}\s+proof)"
                )
                self.assertRegex(lowered, false_alone_insufficiency)
                for outcome in (
                    r"review\s+convergence",
                    r"\bqa\b",
                    r"delivery",
                ):
                    with self.subTest(surface=name, outcome=outcome):
                        self.assertRegex(
                            lowered,
                            false_alone_insufficiency + rf".{{0,180}}{outcome}",
                        )

        # Design and governor both carry the explicit false-axis convergence
        # gate. Check every condition independently so prose order and table
        # layout can change without weakening the semantic contract.
        for name in ("design", "governor"):
            lowered = re.sub(r"\s+", " ", surfaces[name].lower())
            convergence_gate = None
            for occurrence in re.finditer(r"\bconverg(?:ed|ence)\b", lowered):
                window = lowered[
                    max(0, occurrence.start() - 260) : occurrence.end() + 700
                ]
                if (
                    re.search(r"patch_required.{0,180}false", window)
                    and re.search(r"frontier.{0,100}\bempty\b", window)
                    and re.search(
                        r"verification\s+obligations?.{0,100}"
                        r"(?:complete|satisfied)",
                        window,
                    )
                    and re.search(r"qa.{0,100}acceptable", window)
                    and re.search(
                        r"architecture\s+verdict.{0,140}"
                        r"(?:acceptable|local[_ ]safe|approved[_ ]expansion)",
                        window,
                    )
                ):
                    convergence_gate = window
                    break
            self.assertIsNotNone(
                convergence_gate,
                f"{name} must expose the multi-condition CONVERGED gate",
            )
            assert convergence_gate is not None
            for condition in (
                r"patch_required.{0,180}false",
                r"frontier.{0,100}\bempty\b",
                r"verification\s+obligations?.{0,100}"
                r"(?:complete|satisfied)",
                r"qa.{0,100}acceptable",
                r"architecture\s+verdict.{0,140}"
                r"(?:acceptable|local[_ ]safe|approved[_ ]expansion)",
            ):
                with self.subTest(surface=name, condition=condition):
                    self.assertRegex(convergence_gate, condition)

        for text in (surfaces["design"], surfaces["skill"]):
            lowered = re.sub(r"\s+", " ", text.lower())
            for category in (
                "review convergence",
                "qa verdict",
                "delivery state",
                "architecture verdict",
            ):
                with self.subTest(category=category):
                    self.assertIn(category, lowered)
            self.assertRegex(
                lowered,
                r"independent.{0,160}"
                r"(?:outcomes|states|review convergence|qa verdict|delivery)",
            )
            self.assertRegex(
                lowered,
                r"(?:fail|blocked|incomplete).{0,120}"
                r"(?:never|cannot|does not).{0,100}"
                r"(?:success|complete)",
            )
            self.assertRegex(
                lowered,
                r"qa verdict does not.{0,100}(?:create|resolve)"
                r".{0,100}review-convergence pause",
            )
            self.assertNotRegex(
                lowered,
                r"mandatory qa.{0,120}pauses? (?:the )?(?:review )?session",
            )

    def test_completion_outcome_bullets_are_independent_and_overall_is_strict(self):
        for path in (SKILL, DESIGN):
            text = path.read_text()
            section, bullets = self._completion_outcome_bullets(text)
            review = self._completion_bullet(
                bullets, r"review\s+convergence\b"
            )
            architecture = self._completion_bullet(
                bullets, r"architecture\s+outcome\b"
            )
            qa = self._completion_bullet(
                bullets, r"(?:the\s+)?qa\s+verdict\b"
            )
            delivery = self._completion_bullet(bullets, r"delivery\b")
            delivery_contract = re.split(
                r"\boverall\s+completion\s+requires\b", delivery, maxsplit=1
            )[0]


            with self.subTest(surface=path.name, outcome="review"):
                self.assertRegex(
                    review,
                    r"\breview\s+convergence\b.*\bconverg(?:ed|ence)\b",
                )
                for prohibited in (
                    r"\bqa(?:\s+verdict)?\b",
                    r"\barchitecture\s+(?:outcome|verdict)\b",
                    r"\b(?:evidence\s+)?governor(?:\s+decision)?\b",
                ):
                    self.assertNotRegex(review, prohibited)

            with self.subTest(surface=path.name, outcome="architecture"):
                self.assertRegex(architecture, r"\bcurrent\s+head\b")
                self.assertRegex(
                    architecture,
                    r"\b(?:independent\s+)?architecture\s+post[- ]review\b",
                )
                self.assertRegex(architecture, r"\bobligations?\b")
                self.assertRegex(architecture, r"\bimpact\s+delta\b")
                self.assertRegex(
                    architecture,
                    r"\barchitecture\s+verdict\b.{0,180}"
                    r"\b(?:acceptable|local[_ ]safe|approved[_ ]expansion)\b",
                )
                self.assertNotRegex(architecture, r"\bqa(?:\s+verdict)?\b")
                self.assertNotRegex(
                    architecture,
                    r"\b(?:evidence\s+)?governor(?:\s+decision)?\b"
                    r"[^.!?;]{0,180}\bconverg(?:ed|ence)\b|"
                    r"\bconverg(?:ed|ence)\b[^.!?;]{0,180}"
                    r"\b(?:evidence\s+)?governor(?:\s+decision)?\b",
                )

            with self.subTest(surface=path.name, outcome="qa"):
                self.assertRegex(qa, r"\bcurrent\s+head\b")
                self.assertRegex(
                    qa,
                    r"\bmandatory\s+verification\s+obligations?\b.{0,160}"
                    r"\bpass(?:es)?\b",
                )
                self.assertRegex(
                    qa,
                    r"\buser\s+explicitly\s+accepts?\s+every\s+remaining"
                    r"\s+material\s+risk\b",
                )
                for prohibited in (
                    r"\breview\s+convergence\b",
                    r"\barchitecture\s+(?:outcome|verdict)\b",
                    r"\bdelivery(?:\s+state)?\b",
                ):
                    self.assertNotRegex(qa, prohibited)

            with self.subTest(surface=path.name, outcome="delivery"):
                self.assertRegex(
                    delivery_contract,
                    r"\bauthorized\s+implementation\s+state\b",
                )
                for action in (
                    "replies",
                    "reactions",
                    "resolution",
                    "commits",
                    "pushes",
                ):
                    with self.subTest(action=action):
                        self.assertRegex(delivery_contract, rf"\b{action}\b")
                for prohibited in (
                    r"\bqa(?:\s+verdict)?\b",
                    r"\breview\s+convergence\b",
                    r"\barchitecture\s+(?:outcome|verdict)\b",
                ):
                    self.assertNotRegex(delivery_contract, prohibited)

            normalized_section = re.sub(r"\s+", " ", section.lower())
            self.assertRegex(
                normalized_section,
                r"\bevaluate\s+four\s+independent\s+outcomes\b",
            )
            overall = re.search(
                r"\boverall completion requires\b.*",
                normalized_section,
            )
            self.assertIsNotNone(
                overall,
                f"{path.name} must state an overall completion contract",
            )
            assert overall is not None
            overall_clause = overall.group(0)
            for outcome in (
                r"review convergence",
                r"architecture\s+(?:outcome(?:\s+and)?\s+verdict|verdict)",
                r"qa verdict",
                r"delivery state",
                r"(?:evidence\s+)?governor(?:\s+decision)?"
                r".{0,120}\bconverg(?:ed|ence)\b|"
                r"\bconverg(?:ed|ence)\b.{0,120}"
                r"(?:evidence\s+)?governor(?:\s+decision)?",
            ):
                with self.subTest(surface=path.name, overall_outcome=outcome):
                    self.assertRegex(overall_clause, outcome)

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
            r"(?is)before every github write.{0,120}"
            r"each reaction.{0,80}each reply.{0,80}resolution",
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
            normalized_response.index("Only after the equality check passes"),
            normalized_response.index("clean detached or temporary worktree"),
        )
        self.assertLess(
            normalized_response.index("clean detached or temporary worktree"),
            normalized_response.index("Rerun the required focused verification"),
        )
        self.assertLess(
            response_text.index("After push, read the remote head"),
            response_text.index("Add the recorded reactions"),
        )
        self.assertIn("Before every GitHub write", normalized_response)
        self.assertIn(
            "each reaction, each reply, and each resolution",
            normalized_response,
        )
        self.assertIn(
            "Do not reuse one head reread as the guard for a later mutation",
            normalized_response,
        )
        self.assertIn(
            "Add the recorded reactions only after the per-write head reread and "
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
                "any uncommitted edits",
                "related, generated",
                "clean detached or temporary worktree",
                "recorded",
                "sha",
                "preserve the source worktree",
                "not snapshot-bound",
            ):
                with self.subTest(term=term):
                    self.assertIn(term, text)

    def test_initial_admission_and_later_queue_are_explicit(self):
        contracts = (
            (
                DESIGN,
                (
                    "all actionable threads in the initial frozen batch",
                    "initial non-blocking feedback",
                    "created after the cutoff",
                    "named pause",
                    "navigation boundaries, not admission proof",
                    "later-timestamped item fetched during the initial read",
                ),
            ),
            (
                SKILL,
                (
                    "every actionable thread in the frozen batch",
                    "initial non-blocking feedback",
                    "`queued`: later non-blocking",
                    "pause",
                    "cursor membership as admission",
                    "fetched during the initial read",
                ),
            ),
        )
        for path, terms in contracts:
            text = re.sub(r"\s+", " ", path.read_text().lower())
            for term in terms:
                with self.subTest(path=path.name, term=term):
                    self.assertIn(term, text)
        design = re.sub(r"\s+", " ", DESIGN.read_text().lower())
        self.assertRegex(
            design,
            r"later non-blocking comments and replies "
            r"(?:are queued|remain queued)(?: by default)?",
        )
        self.assertRegex(
            design,
            r"(?is)initial frozen batch only when its immutable `createdat` "
            r"is at or before the cutoff.{0,180}"
            r"later-timestamped item fetched during the initial read remains "
            r"post-cutoff feedback",
        )
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        self.assertRegex(
            skill,
            r"(?is)initial batch only when its own `createdat` is at or before "
            r"the cutoff.{0,180}later timestamp is classified as post-cutoff",
        )

    def test_recheck_deadline_has_a_future_minimum(self):
        design = re.sub(r"\s+", " ", DESIGN.read_text().lower())
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        for text in (design, skill):
            self.assertRegex(
                text,
                r"(?is)deadline.{0,120}at least one minute and thirty seconds "
                r"in the future",
            )
            self.assertRegex(
                text,
                r"(?is)deadline.{0,100}non[- ]resetting",
            )

    def test_no_code_delivery_covers_all_explanation_writes(self):
        for path in (SKILL, DESIGN):
            text = re.sub(r"\s+", " ", path.read_text().lower())
            for term in (
                "explanation",
                "resolution",
            ):
                with self.subTest(path=path.name, term=term):
                    self.assertIn(term, text)
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        self.assertRegex(
            skill,
            r"(?is)no-code disposition.{0,180}"
            r"(?:reaction, reply, or resolution|explanation-only response)",
        )
        self.assertRegex(
            skill,
            r"(?is)no-code disposition.{0,180}fresh `headrefoid` read "
            r"confirms that no patch is required.{0,180}"
            r"current-head no-code verification path is complete",
        )
        self.assertIn(
            "cite the post-push gate for a patch, or the current-head no-code "
            "verification for an explanation-only response",
            skill,
        )
        design = re.sub(r"\s+", " ", DESIGN.read_text().lower())
        self.assertIn(
            "no-code dispositions use a fresh current-head verification path "
            "for reactions, explanation replies, and resolutions",
            design,
        )
        self.assertIn(
            "patch replies cite the post-push gate; explanation-only replies "
            "cite the current-head no-code verification",
            design,
        )

    def test_locale_summaries_match_initial_and_post_cutoff_admission(self):
        summaries = (
            (README, ("initial frozen batch", "same-class", "after the cutoff")),
            (README_KO, ("초기 동결 묶음", "컷오프 이후", "일시 중지")),
            (README_ZH_CN, ("初始冻结批次", "截止时间后", "暂停会话")),
        )
        for path, terms in summaries:
            text = re.sub(r"\s+", " ", path.read_text().lower())
            for term in terms:
                with self.subTest(path=path.name, term=term):
                    self.assertIn(term.lower(), text)

    @staticmethod
    def _post_cutoff_blocking_passage(text):
        normalized = re.sub(r"\s+", " ", text.lower())
        anchor_pattern = re.compile(
            r"\bsame-class blocking comments?\s+or\s+repl(?:y|ies)\b"
            r".{0,120}\bcreated after the cutoff\b"
        )
        anchors = list(anchor_pattern.finditer(normalized))
        if not anchors:
            raise AssertionError(
                "missing anchored same-class blocking post-cutoff clause"
            )

        boundary_pattern = re.compile(
            r"\b(?:"
            r"a new head is not proof"
            r"|non-blocking comments and replies "
            r"(?:are queued|remain queued(?: by default)?)"
            r")\b"
        )
        passages = []
        for index, anchor in enumerate(anchors, start=1):
            boundary = boundary_pattern.search(normalized, anchor.end())
            if boundary is None:
                raise AssertionError(
                    "missing next-rule boundary after same-class blocking "
                    f"post-cutoff clause {index}"
                )
            passages.append(
                normalized[anchor.start() : boundary.start()]
            )
        return passages

    def test_post_cutoff_blocking_passage_stops_before_adjacent_queue_rule(self):
        text = (
            "Same-class blocking comments or replies created after the cutoff "
            "are recorded as a named pause awaiting explicit user direction. "
            "Non-blocking comments and replies remain queued by default. "
            "This sentence is adjacent-rule spillover."
        )
        passages = self._post_cutoff_blocking_passage(text)
        self.assertEqual(len(passages), 1)

        normalized = re.sub(r"\s+", " ", text.lower())
        queue_rule = "non-blocking comments and replies remain queued by default"
        expected = normalized[
            normalized.index("same-class blocking") : normalized.index(queue_rule)
        ]
        self.assertEqual(passages[0], expected)
        self.assertNotIn(queue_rule, passages[0])
        self.assertNotIn("adjacent-rule spillover", passages[0])




    def test_risk_levels_define_traceknot_selection(self):
        design = re.sub(r"\s+", " ", DESIGN.read_text().lower())
        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
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
            passages = self._post_cutoff_blocking_passage(text)
            self.assertTrue(
                passages,
                "missing same-class blocking post-cutoff passages",
            )
            for index, passage in enumerate(passages, start=1):
                with self.subTest(passage=index):
                    self.assertRegex(
                        passage,
                        r"\bnamed\s+(?:`paused`\s+reason|(?:review\s+)?pause)\b",
                    )
                    self.assertRegex(
                        passage,
                        r"\brecorded explicit user direction\b",
                    )
                    self.assertRegex(
                        passage,
                        r"(?:\breview campaign\b.{0,120}\bindependently permits\b|"
                        r"\bindependently permits\b.{0,120}\breview campaign\b)",
                    )


        self.assertRegex(
            skill,
            r"(?is)(?:new session|follow-up).{0,320}"
            r"review campaign.{0,120}independently permits",
        )
        self.assertIn(
            "do not create or assign an explicit follow-up automatically",
            skill,
        )
        self.assertIn(
            "record an `out-of-scope` follow-up only after recorded explicit user "
            "direction",
            skill,
        )

    @classmethod
    def _out_of_scope_operational_sections(cls, path):
        text = path.read_text()
        if path == SKILL:
            matches = list(
                re.finditer(
                    r"(?ms)^(?:7|8)\.\s+.*?(?=^\d+\.\s|\Z)",
                    text,
                )
            )
            return [match.group(0) for match in matches]
        if path == DESIGN:
            section = cls._markdown_section(text, "Candidate disposition")
            return [section]
        raise AssertionError(f"unsupported operational surface: {path}")

    def test_out_of_scope_reporting_is_immediate_paused_and_not_authority(self):
        direction_pattern = r"\b(?:recorded\s+)?explicit\s+user\s+direction\b"
        campaign_pattern = (
            r"(?:\breview\s+campaign\b.{0,180}\bindependently\s+permits\b|"
            r"\bindependently\s+permits\b.{0,180}\breview\s+campaign\b)"
        )
        assignment_pattern = (
            r"\b(?:assign\w*|follow[- ]?up\w*|new[- ]session|"
            r"successor(?:\s+review)?\s+session)\b"
        )
        blocked_projection_pattern = r"\bobligations_blocked\s*:\s*true\b"
        reporting_does_not_clear_pattern = (
            r"\breport\w*\b.{0,320}"
            r"(?:\b(?:does not|never|cannot)\s+"
            r"(?:clear|reset|remove|resolve)\b|"
            r"\b(?:alone|only|by itself)\b.{0,120}"
            r"\b(?:does not|never|cannot)\b)"
            r".{0,180}\b(?:blocked|obligations_blocked)\b"
        )
        blocked_persistence_pattern = (
            r"\b(?:obligations_blocked|blocked)\b.{0,320}"
            r"\b(?:remain\w*|stay\w*)\s+`?(?:blocked|true)`?(?!\w)"
        )
        blocked_authorization_boundary_pattern = (
            r"\b(?:blocked|obligations_blocked)\b.{0,500}"
            r"(?:"
            + direction_pattern
            + r".{0,240}"
            + campaign_pattern
            + r"|"
            + campaign_pattern
            + r".{0,240}"
            + direction_pattern
            + r")"
        )
        for path in (SKILL, DESIGN):
            sections = self._out_of_scope_operational_sections(path)
            normalized_sections = [
                re.sub(r"\s+", " ", section).lower()
                for section in sections
            ]
            self.assertTrue(
                all(
                    re.search(blocked_projection_pattern, section)
                    for section in normalized_sections
                ),
                "each operational out-of-scope passage must project "
                "`obligations_blocked: true`",
            )
            self.assertTrue(
                any(
                    re.search(reporting_does_not_clear_pattern, section)
                    for section in normalized_sections
                ),
                "reporting alone must not clear the blocked obligation",
            )
            self.assertTrue(
                any(
                    re.search(blocked_persistence_pattern, section)
                    for section in normalized_sections
                ),
                "the blocked obligation must remain blocked until disposition "
                "is resolved",
            )
            self.assertTrue(
                any(
                    re.search(blocked_authorization_boundary_pattern, section)
                    for section in normalized_sections
                ),
                "blocked status must remain behind the explicit-direction and "
                "independent Review Campaign gates",
            )
            with self.subTest(path=path.name):
                self.assertTrue(
                    sections,
                    "missing an out-of-scope operational section",
                )
                self.assertFalse(
                    any("acceptance scenarios" in section.lower() for section in sections),
                    "acceptance scenarios must not satisfy operational reporting",
                )
                self.assertTrue(
                    any(
                        all(
                            re.search(pattern, section)
                            for pattern in (
                                r"\b(?:record\w*|ledger)\b",
                                r"\breport\w*\b",
                                r"\bimmediately\b",
                                r"\bpaused\b",
                            )
                        )
                        for section in normalized_sections
                    ),
                    "confirmed out-of-scope defects must be recorded and "
                    "reported immediately while paused",
                )
                for action, action_pattern in (
                    ("edit", r"\bedit\w*\b"),
                    ("follow-up", r"\bfollow[- ]?up\w*\b"),
                ):
                    self.assertTrue(
                        any(
                            re.search(
                                r"\breport\w*\b.{0,220}"
                                r"\b(?:does not|never|cannot)\s+"
                                r"authori[sz]\w*.{0,120}"
                                + action_pattern,
                                section,
                                re.IGNORECASE,
                            )
                            or re.search(
                                r"\breport\w*\b.{0,180}"
                                r"\b(?:evidence[- ]only|no)\b.{0,140}"
                                + action_pattern
                                + r".{0,100}\b(?:authori\w*|authority)\b",
                                section,
                                re.IGNORECASE,
                            )
                            for section in normalized_sections
                        ),
                        f"reporting must not authorize {action}",
                    )
                self.assertTrue(
                    any(
                        all(
                            re.search(pattern, section)
                            for pattern in (
                                direction_pattern,
                                campaign_pattern,
                                assignment_pattern,
                            )
                        )
                        for section in normalized_sections
                    ),
                    "out-of-scope assignment must retain explicit direction "
                    "and independent Review Campaign gates",
                )

    def test_acceptance_scenarios_are_sequentially_numbered(self):
        source = DESIGN.read_text()
        section_match = re.search(
            r"(?ms)^## Acceptance scenarios\s*$\n(.*?)(?=^## |\Z)",
            source,
        )
        self.assertIsNotNone(section_match, "missing acceptance scenarios section")
        assert section_match is not None
        section = section_match.group(1)
        starts = list(
            re.finditer(r"(?m)^[ \t]*(\d+)\.[ \t]+", section)
        )
        numbers = [int(match.group(1)) for match in starts]
        self.assertTrue(numbers, "acceptance scenarios must be numbered")
        self.assertEqual(
            numbers,
            list(range(1, len(numbers) + 1)),
            "acceptance scenarios must use consecutive numbering",
        )

        reporting_lines = [
            line
            for line in section.splitlines()
            if re.search(
                r"(?:out[- ]of[- ]scope|outside the safe PR boundary)",
                line,
                re.IGNORECASE,
            )
            and re.search(r"\b(?:immediately|recorded|reported)\b", line)
        ]
        self.assertTrue(
            reporting_lines,
            "missing the immediate out-of-scope reporting acceptance scenario",
        )
        self.assertTrue(
            any(re.match(r"^[ \t]*\d+\.[ \t]+", line) for line in reporting_lines),
            "the immediate out-of-scope reporting rule must be a numbered "
            "acceptance scenario, not an unnumbered paragraph",
        )


    def test_skill_completion_gate_covers_follow_up_and_session_dispositions(self):
        normalized = re.sub(r"\s+", " ", SKILL.read_text().lower())
        completion = re.search(
            r"(?is)review convergence is `converged` only when.*?"
            r"(?=\bclassification alone cannot satisfy convergence\b)",
            normalized,
        )
        self.assertIsNotNone(
            completion,
            "missing Review convergence completion rule",
        )
        assert completion is not None
        completion_rule = completion.group(0)

        findings = self._new_session_assignment_clauses(completion_rule)
        positive_findings = [
            finding for finding in findings if not finding["prohibited"]
        ]
        self.assertEqual(
            len(positive_findings),
            1,
            "current completion clause must contain one actual disposition operation",
        )
        queue_pattern = (
            r"\blater\s+non[- ]blocking\s+feedback\s+remains\s+queued\b"
        )
        follow_up_pattern = r"\bexplicit\s+follow[- ]?up\b"
        session_pattern = (
            r"\b(?:new[- ]session|successor(?:\s+review)?\s+session|"
            r"new\s*/\s*successor\s+session)\b"
        )
        direction_pattern = r"\brecorded\s+explicit\s+user\s+direction\b"
        campaign_permission_pattern = (
            r"\b(?:the\s+)?review\s+campaign\s+independently\s+permits?\b"
        )
        pause_pattern = r"\bno\s+unresolved\s+session\s+pause\s+reason\s+remains\b"

        for marker, message in (
            (
                queue_pattern,
                "completion rule must retain the queued default for "
                "later non-blocking feedback",
            ),
            (
                follow_up_pattern,
                "completion rule must retain the explicit follow-up "
                "disposition",
            ),
            (
                session_pattern,
                "completion rule must retain the new/successor session "
                "disposition",
            ),
            (
                direction_pattern,
                "completion rule must retain recorded explicit user "
                "direction",
            ),
            (
                campaign_permission_pattern,
                "completion rule must retain independent Review Campaign "
                "permission",
            ),
            (
                pause_pattern,
                "completion rule must retain the unresolved-pause gate",
            ),
        ):
            with self.subTest(marker=message):
                self.assertRegex(completion_rule, marker, message)

        self.assertRegex(
            completion_rule,
            r"\bassign(?:ed|s|ing)?\b",
            "completion rule must retain a disposition assignment",
        )

        gated_findings = [
            finding
            for finding in findings
            if (
                not finding["prohibited"]
                and finding["direction_gate"]
                and finding["campaign_permission"]
            )
        ]
        for disposition, pattern in (
            ("session", session_pattern),
            ("explicit follow-up", follow_up_pattern),
        ):
            with self.subTest(disposition=disposition):
                self.assertTrue(
                    any(
                        re.search(pattern, finding["clause"])
                        for finding in gated_findings
                    ),
                    f"{disposition} disposition must share the recorded "
                    "direction and independent campaign gates",
                )

    @staticmethod
    def _new_session_assignment_clauses(text):
        normalized = re.sub(r"\s+", " ", text.lower())
        clauses = [
            clause.strip()
            for clause in re.split(r"(?<=[.!?;])\s+", normalized)
            if clause.strip()
        ]
        target_pattern = re.compile(
            r"\b(?:new[- ]session|successor(?:\s+review)?\s+session|"
            r"follow[- ]?up)\b"
        )
        disposition_pattern = re.compile(
            r"\b(?:assign(?:ed|s|ing)?|move(?:d|s|ing)?|"
            r"hand(?:ed|s|ing)?[- ]off)\b"
        )
        fallback_trigger_pattern = (
            r"(?:\botherwise\b[^.!?;]{0,180}?"
            r"\b(?:start|open|create)(?:s|ed|ing)?\b"
            r"|\bautomatically\s+"
            r"(?:start|open|create)(?:s|ed|ing)?\b"
            r"|\bdefault\s+to\b)"
        )
        fallback_pattern = re.compile(fallback_trigger_pattern)
        direction_pattern = re.compile(
            r"\b(?:recorded\s+)?explicit\s+user\s+direction\b"
        )
        negation_pattern = (
            r"\b(?:never|cannot|can['’]t|does\s+not|do\s+not|"
            r"should\s+not|must\s+not|not)\b"
        )
        permission_pattern = r"(?:permit\w*|permission\w*|authori[sz]\w*)"
        campaign_marker = r"(?:review\s+campaign|campaign(?:['’]s)?)"
        fallback_verb_pattern = r"\b(?:start|open|create)(?:s|ed|ing)?\b"

        def associated_targets(
            clause,
            operation,
            lower_bound=0,
            upper_bound=None,
        ):
            upper_bound = len(clause) if upper_bound is None else upper_bound
            after_matches = list(
                target_pattern.finditer(
                    clause,
                    operation.end(),
                    min(upper_bound, operation.end() + 180),
                )
            )
            before_matches = list(
                target_pattern.finditer(
                    clause,
                    max(lower_bound, operation.start() - 180),
                    operation.start(),
                )
            )
            if after_matches:
                return after_matches
            if before_matches:
                return before_matches
            return []


        findings = []
        for clause in clauses:
            operation_matches = [
                {
                    "match": operation,
                    "automatic_fallback": False,
                }
                for operation in disposition_pattern.finditer(clause)
            ]
            operation_matches.extend(
                {
                    "match": fallback,
                    "automatic_fallback": True,
                }
                for fallback in fallback_pattern.finditer(clause)
            )
            operation_matches.sort(
                key=lambda item: (item["match"].start(), item["match"].end())
            )

            operations = []
            for index, operation_info in enumerate(operation_matches):
                operation = operation_info["match"]
                previous_end = (
                    operation_matches[index - 1]["match"].end()
                    if index
                    else 0
                )
                next_start = (
                    operation_matches[index + 1]["match"].start()
                    if index + 1 < len(operation_matches)
                    else len(clause)
                )
                targets = associated_targets(
                    clause,
                    operation,
                    lower_bound=previous_end,
                    upper_bound=next_start,
                )
                if not targets:
                    continue
                operations.append(
                    {
                        "start": min(operation.start(), targets[0].start()),
                        "end": max(operation.end(), targets[-1].end()),
                        "targets": [target.group(0) for target in targets],
                        "automatic_fallback": operation_info["automatic_fallback"],
                    }
                )

            unique_operations = []
            for operation in sorted(
                operations,
                key=lambda item: (item["start"], item["end"]),
            ):
                if any(
                    operation["start"] == existing["start"]
                    and operation["end"] == existing["end"]
                    for existing in unique_operations
                ):
                    continue
                unique_operations.append(operation)

            for operation in unique_operations:
                start = operation["start"]
                end = operation["end"]
                occurrence = clause[start:end]
                context = clause[max(0, start - 120) : min(len(clause), end + 120)]
                operation_pattern = (
                    fallback_verb_pattern
                    if operation["automatic_fallback"]
                    else disposition_pattern.pattern
                )
                prohibited = bool(
                    re.search(
                        negation_pattern
                        + r"(?:\s+\S+){0,8}\s+"
                        + operation_pattern,
                        context,
                    )
                    or re.search(
                        operation_pattern
                        + r"(?:\s+\S+){0,8}\s+"
                        + negation_pattern,
                        context,
                    )
                )
                campaign_permission = bool(
                    re.search(
                        r"\b"
                        + campaign_marker
                        + r"\b.*\b"
                        + permission_pattern
                        + r"\b",
                        clause,
                    )
                    or re.search(
                        r"\b"
                        + permission_pattern
                        + r"\b.*\b"
                        + campaign_marker
                        + r"\b",
                        clause,
                    )
                )
                findings.append(
                    {
                        "clause": clause,
                        "occurrence": occurrence,
                        "targets": operation["targets"],
                        "segment": clause,
                        "direction_gate": bool(direction_pattern.search(clause)),
                        "prohibited": prohibited,
                        "campaign_permission": campaign_permission,
                        "automatic_fallback": operation["automatic_fallback"],
                    }
                )
        return findings

    def test_new_session_assignments_require_direction_and_campaign_gate(self):
        for path in (SKILL, DESIGN):
            findings = self._new_session_assignment_clauses(path.read_text())
            self.assertTrue(findings, f"{path} has no assignment clauses to inspect")
            clauses = {}
            for finding in findings:
                clauses.setdefault(finding["clause"], []).append(finding)
            for clause, clause_findings in clauses.items():
                positive = [
                    finding
                    for finding in clause_findings
                    if not finding["prohibited"]
                ]
                with self.subTest(path=path.name, clause=clause):
                    self.assertLessEqual(
                        len(positive),
                        1,
                        "one semantic clause must not authorize multiple "
                        "disposition operations",
                    )
                    if not positive:
                        continue
                    finding = positive[0]
                    self.assertFalse(
                        finding["automatic_fallback"],
                        "otherwise start/open/create fallbacks must not "
                        "automatically open a session",
                    )
                    self.assertTrue(
                        finding["direction_gate"],
                        "session/follow-up disposition lacks a "
                        "recorded/explicit user-direction gate",
                    )
                    self.assertTrue(
                        finding["campaign_permission"],
                        "session/follow-up disposition lacks independent "
                        "Review Campaign permission",
                    )

        self.assertEqual(
            self._new_session_assignment_clauses(
                "Recorded explicit user direction selects a successor Review "
                "Session and the Review Campaign independently permits it."
            ),
            [],
            "select is a gate, not a disposition operation",
        )
        noun_only = self._new_session_assignment_clauses(
            "Recorded explicit user direction selects that assignment for a new "
            "session and the Review Campaign independently permits it."
        )
        self.assertEqual(
            noun_only,
            [],
            "a noun naming the selected assignment is not a disposition operation",
        )
        ambiguous = self._new_session_assignment_clauses(
            "Recorded explicit user direction and Review Campaign permission "
            "permit it: assign the item to a new session and move another "
            "item to a follow-up."
        )
        self.assertEqual(
            len([finding for finding in ambiguous if not finding["prohibited"]]),
            2,
            "independent assignments in one clause must both be detected",
        )
        two_assign_verbs = self._new_session_assignment_clauses(
            "Recorded explicit user direction and Review Campaign permission "
            "permit it: assign the item to a new session and assigned another "
            "item to a follow-up."
        )
        self.assertEqual(
            len(
                [
                    finding
                    for finding in two_assign_verbs
                    if not finding["prohibited"]
                ]
            ),
            2,
            "two actual assignment verbs must remain two operations",
        )
        coordinated = self._new_session_assignment_clauses(
            "Recorded explicit user direction and Review Campaign permission "
            "permit it: assign the item to an explicit follow-up and a new "
            "session."
        )
        positive = [
            finding for finding in coordinated if not finding["prohibited"]
        ]
        self.assertEqual(
            len(positive),
            1,
            "one assign verb governing two targets must produce one finding",
        )
        self.assertEqual(
            positive[0]["targets"],
            ["follow-up", "new session"],
            "coordinated finding must retain both disposition targets",
        )
        self.assertTrue(
            positive[0]["direction_gate"],
            "coordinated disposition must retain the direction gate",
        )
        self.assertTrue(
            positive[0]["campaign_permission"],
            "coordinated disposition must retain campaign permission",
        )

        skill = re.sub(r"\s+", " ", SKILL.read_text().lower())
        self.assertNotRegex(
            skill,
            r"(?is)\b(?:moved|assigned)\s+to\s+a\s+new[- ]session\s+"
            r"(?:permitted|allowed|authorized)\s+by\s+"
            r"(?:the\s+)?review campaign\b",
        )



    def test_named_pause_convergence_covers_session_and_follow_up(self):
        convergence_anchor = (
            r"\bpaused\s+session\s+cannot\s+be\s+`?converged`?\b"
        )
        session_pattern = (
            r"\b(?:new[- ]session|successor(?:\s+review)?\s+session)\b|"
            r"\bnew\s*/\s*successor\s+session\b"
        )
        follow_up_pattern = r"\bexplicit\s+follow[- ]?up\b"
        direction_pattern = r"\brecorded\s+explicit\s+user\s+direction\b"
        campaign_permission_pattern = (
            r"\b(?:the\s+)?review\s+campaign\s+independently\s+permits?\b"
        )
        pause_pattern = re.compile(
            convergence_anchor
            + r".*?(?=\bthe\s+qa\s+verdict\b)"
        )

        for path in (SKILL, DESIGN):
            normalized = re.sub(r"\s+", " ", path.read_text().lower())
            pause_match = pause_pattern.search(normalized)
            with self.subTest(path=path.name):
                self.assertIsNotNone(
                    pause_match,
                    "missing general named-pause convergence rule",
                )
                assert pause_match is not None
                pause_rule = pause_match.group(0)
                first_sentence = re.search(
                    convergence_anchor + r".*?(?=[.!?;])",
                    pause_rule,
                )
                self.assertIsNotNone(
                    first_sentence,
                    "missing opening sentence of named-pause rule",
                )
                assert first_sentence is not None
                self.assertRegex(
                    first_sentence.group(0),
                    follow_up_pattern,
                    "the general pause-clear sentence must retain the "
                    "explicit follow-up disposition",
                )
                self.assertRegex(
                    first_sentence.group(0),
                    session_pattern,
                    "the general pause-clear sentence must retain the "
                    "new/successor session disposition",
                )
                self.assertRegex(
                    first_sentence.group(0),
                    direction_pattern,
                    "the general pause-clear sentence must retain recorded "
                    "explicit user direction",
                )
                self.assertRegex(
                    first_sentence.group(0),
                    campaign_permission_pattern,
                    "the general pause-clear sentence must retain independent "
                    "Review Campaign permission",
                )

                gated_findings = [
                    finding
                    for finding in self._new_session_assignment_clauses(
                        pause_rule
                    )
                    if (
                        not finding["prohibited"]
                        and finding["direction_gate"]
                        and finding["campaign_permission"]
                    )
                ]
                for disposition, pattern in (
                    ("session", session_pattern),
                    ("explicit follow-up", follow_up_pattern),
                ):
                    with self.subTest(
                        path=path.name,
                        disposition=disposition,
                    ):
                        self.assertTrue(
                            any(
                                re.search(pattern, finding["clause"])
                                for finding in gated_findings
                            ),
                            f"{disposition} disposition must share the "
                            "direction and independent campaign gates",
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
            passages = self._post_cutoff_blocking_passage(normalized)
            self.assertTrue(
                passages,
                "missing same-class blocking post-cutoff passages",
            )
            for index, passage in enumerate(passages, start=1):
                with self.subTest(passage=index):
                    self.assertRegex(
                        passage,
                        r"\bnamed\s+(?:`paused`\s+reason|(?:review\s+)?pause)\b",
                    )
                    self.assertRegex(
                        passage,
                        r"\brecorded explicit user direction\b",
                    )
                    self.assertRegex(
                        passage,
                        r"(?:\breview campaign\b.{0,120}\bindependently permits\b|"
                        r"\bindependently permits\b.{0,120}\breview campaign\b)",
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
            "architecture context packet",
            "approved boundary",
            "architecture baseline",
            "impact delta",
            "defect frontier",
            "verification obligations",
            "evidence governor",
            "architecture verdict",
            "two-round automatic fuse",
            "never as evidence of convergence or strategy failure",
            "every actionable thread",
            "initial non-blocking feedback",
            "queue only later non-blocking feedback",
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
                "architecture context",
                "impact delta",
                "safety fuse",
                "Explicitly invoking `$review-radius` is the most reliable",
            ),
            README_KO: (
                "## 제한된 리뷰 세션",
                "기본 자동 패치 예산은 **두 라운드**",
                "Traceknot",
                "QA 핸드오프",
                "리뷰 수렴과 QA 판정은 서로",
                "별개입니다",
                "아키텍처 컨텍스트",
                "영향 델타",
                "안전 퓨즈",
                "$review-radius",
                "명시적으로 호출",
            ),
            README_ZH_CN: (
                "## 有边界的审查会话",
                "默认自动补丁预算为 **两轮**",
                "Traceknot",
                "QA 交接",
                "审查收敛和 QA 判定彼此独立",
                "架构上下文",
                "影响增量",
                "安全熔断器",
                "明确调用 `$review-radius` 是",
            ),
        }
        for path, phrases in markers.items():
            text = re.sub(r"\s+", " ", path.read_text())
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

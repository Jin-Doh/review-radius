import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/review-radius/scripts/evaluate_governor.py"
SCENARIOS = ROOT / "skills/review-radius/references/governor-scenarios.json"


_spec = importlib.util.spec_from_file_location("evaluate_governor", SCRIPT)
if _spec is None or _spec.loader is None:
    raise ImportError(f"could not load {SCRIPT}")
governor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(governor)


class ReviewGovernorDecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        payload = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        cls.scenarios = payload["scenarios"]
        cls.by_name = {scenario["name"]: scenario for scenario in cls.scenarios}

    def scenario(self, name):
        return dict(self.by_name[name]["signals"])

    def test_import_api_evaluates_a_signal_packet(self):
        self.assertTrue(callable(governor.evaluate))
        signals = self.scenario("high-risk coverage gap blocks evidence")
        self.assertEqual(
            governor.evaluate(signals),
            {
                "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_scenario_packets_match_expected_decisions(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.assertEqual(
                    governor.evaluate(scenario["signals"]), scenario["expected"]
                )

    def test_pairwise_strategy_signal_precedes_insufficient_evidence(self):
        valid = self.scenario("acceptable convergence")
        for packet in (
            {**valid, "boundary": "unknown", "premise": "invalid"},
            {
                **valid,
                "coverage": "high_risk_gap",
                "semantic_delta": "new_dimension",
            },
            {**valid, "architecture_verdict": "STRATEGY_REVIEW_REQUIRED"},
            {**valid, "architecture_verdict": "LOCAL_SAFE", "boundary": "expanded"},
        ):
            with self.subTest(packet=packet):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "STRATEGY_RESET_REQUIRED",
                        "architecture_verdict": packet["architecture_verdict"],
                    },
                )
    def test_strategy_signal_precedes_blocked_obligation(self):
        packet = {
            **self.scenario("duplicate comments share one shrinking frontier"),
            "premise": "invalid",
            "obligations_blocked": True,
        }
        self.assertEqual(
            governor.evaluate(packet),
            {
                "decision": "STRATEGY_RESET_REQUIRED",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_blocked_obligation_precedes_impact_fuse_and_local_authority(self):
        valid = self.scenario("duplicate comments share one shrinking frontier")
        packets = (
            {**valid, "frontier": "stable", "obligations_blocked": True},
            {
                **valid,
                "frontier": "shrinking",
                "patch_rounds": valid["automatic_patch_budget"],
                "obligations_blocked": True,
            },
            {**valid, "obligations_blocked": True},
            {
                **valid,
                "frontier": "empty",
                "patch_required": False,
                "obligations_complete": True,
                "obligations_blocked": True,
            },
        )
        for packet in packets:
            with self.subTest(
                frontier=packet["frontier"],
                patch_required=packet["patch_required"],
                patch_rounds=packet["patch_rounds"],
            ):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                        "architecture_verdict": "LOCAL_SAFE",
                    },
                )


    def test_acceptable_verdict_and_boundary_pairs_are_consistent(self):
        valid = self.scenario("acceptable convergence")
        local_safe = {
            **valid,
            "architecture_verdict": "LOCAL_SAFE",
            "boundary": "within",
        }
        approved_expansion = {
            **valid,
            "architecture_verdict": "APPROVED_EXPANSION",
            "boundary": "approved_expansion",
        }

        for packet in (
            {**local_safe, "boundary": "approved_expansion"},
            {**approved_expansion, "boundary": "within"},
        ):
            with self.subTest(
                architecture_verdict=packet["architecture_verdict"],
                boundary=packet["boundary"],
            ):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                        "architecture_verdict": packet["architecture_verdict"],
                    },
                )

        for packet in (local_safe, approved_expansion):
            with self.subTest(
                architecture_verdict=packet["architecture_verdict"],
                boundary=packet["boundary"],
            ):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "CONVERGED",
                        "architecture_verdict": packet["architecture_verdict"],
                    },
                )


    def test_pairwise_blocking_verdict_precedes_impact_and_convergence(self):
        valid = self.scenario("acceptable convergence")
        for verdict in ("NOT_ASSESSED", "BLOCKED"):
            for frontier in ("empty", "stable"):
                packet = {
                    **valid,
                    "architecture_verdict": verdict,
                    "frontier": frontier,
                    "patch_required": True,
                }
                with self.subTest(verdict=verdict, frontier=frontier):
                    self.assertEqual(
                        governor.evaluate(packet),
                        {
                            "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                            "architecture_verdict": verdict,
                        },
                    )

    def test_pairwise_coverage_and_empty_completion_gaps_precede_impact(self):
        valid = self.scenario("duplicate comments share one shrinking frontier")
        for coverage in ("low_risk_gap", "high_risk_gap"):
            packet = {**valid, "coverage": coverage, "frontier": "stable"}
            with self.subTest(coverage=coverage):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                        "architecture_verdict": "LOCAL_SAFE",
                    },
                )

        for obligation, qa in ((False, True), (True, False), (False, False)):
            packet = {
                **valid,
                "frontier": "empty",
                "patch_required": True,
                "obligations_complete": obligation,
                "qa_acceptable": qa,
            }
            with self.subTest(obligation=obligation, qa=qa):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                        "architecture_verdict": "LOCAL_SAFE",
                    },
                )

    def test_pairwise_impact_is_limited_to_material_frontier_trends(self):
        valid = self.scenario("duplicate comments share one shrinking frontier")
        for frontier in ("stable", "expanding", "regressing"):
            packet = {**valid, "frontier": frontier}
            with self.subTest(frontier=frontier):
                self.assertEqual(
                    governor.evaluate(packet),
                    {
                        "decision": "IMPACT_REVIEW_REQUIRED",
                        "architecture_verdict": "LOCAL_SAFE",
                    },
                )

        no_code = {
            **valid,
            "frontier": "shrinking",
            "patch_required": False,
        }
        self.assertEqual(
            governor.evaluate(no_code),
            {
                "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_convergence_precedes_exhausted_fuse_when_patch_not_required(self):
        packet = {
            **self.scenario("acceptable convergence"),
            "patch_rounds": 2,
            "automatic_patch_budget": 2,
            "patch_required": False,
        }
        self.assertEqual(
            governor.evaluate(packet),
            {
                "decision": "CONVERGED",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

        approved = {
            **packet,
            "architecture_verdict": "APPROVED_EXPANSION",
            "boundary": "approved_expansion",
        }
        self.assertEqual(
            governor.evaluate(approved),
            {
                "decision": "CONVERGED",
                "architecture_verdict": "APPROVED_EXPANSION",
            },
        )

    def test_fuse_and_continue_require_patch_required_and_actionable_frontier(self):
        shrinking = self.scenario("duplicate comments share one shrinking frontier")
        available = {**shrinking, "patch_rounds": 1}
        self.assertEqual(
            governor.evaluate(available),
            {
                "decision": "CONTINUE_LOCAL",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

        exhausted = {**shrinking, "patch_rounds": 2}
        self.assertEqual(
            governor.evaluate(exhausted),
            {
                "decision": "AUTOMATION_FUSE_EXHAUSTED",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

        no_patch = {**exhausted, "patch_required": False}
        self.assertEqual(
            governor.evaluate(no_patch),
            {
                "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

        empty = {
            **shrinking,
            "frontier": "empty",
            "patch_rounds": 2,
            "patch_required": True,
        }
        self.assertEqual(
            governor.evaluate(empty),
            {
                "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_no_code_unresolved_work_after_fuse_exhaustion_never_gets_edit_authority(self):
        packet = {
            **self.scenario("automatic fuse pauses without convergence evidence"),
            "patch_required": False,
        }
        self.assertEqual(
            governor.evaluate(packet),
            {
                "decision": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_incomplete_shrinking_frontier_continues_until_fuse(self):
        packet = {
            **self.scenario("duplicate comments share one shrinking frontier"),
            "patch_rounds": 0,
            "automatic_patch_budget": 2,
            "patch_required": True,
            "obligations_complete": False,
            "obligations_blocked": False,
            "qa_acceptable": False,
        }
        self.assertEqual(
            governor.evaluate(packet),
            {
                "decision": "CONTINUE_LOCAL",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

        exhausted = {**packet, "patch_rounds": packet["automatic_patch_budget"]}
        self.assertEqual(
            governor.evaluate(exhausted),
            {
                "decision": "AUTOMATION_FUSE_EXHAUSTED",
                "architecture_verdict": "LOCAL_SAFE",
            },
        )

    def test_independent_architecture_verdict_is_validated_and_returned(self):
        valid = self.scenario("acceptable convergence")
        expected = {
            "LOCAL_SAFE": "CONVERGED",
            "APPROVED_EXPANSION": "CONVERGED",
            "NOT_ASSESSED": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "BLOCKED": "INSUFFICIENT_ARCHITECTURE_EVIDENCE",
            "STRATEGY_REVIEW_REQUIRED": "STRATEGY_RESET_REQUIRED",
        }
        for verdict, decision in expected.items():
            packet = {
                **valid,
                "architecture_verdict": verdict,
                "boundary": (
                    "approved_expansion"
                    if verdict == "APPROVED_EXPANSION"
                    else valid["boundary"]
                ),
            }
            with self.subTest(verdict=verdict):
                self.assertEqual(
                    governor.evaluate(packet),
                    {"decision": decision, "architecture_verdict": verdict},
                )

    def test_invalid_signal_packets_are_rejected(self):
        valid = self.scenario("acceptable convergence")
        invalid_packets = (
            {**valid, "architecture_verdict": "UNKNOWN"},
            {**valid, "boundary": "outside"},
            {**valid, "patch_rounds": -1},
            {**valid, "patch_rounds": True},
            {**valid, "automatic_patch_budget": 0},
            {**valid, "patch_required": "yes"},
            {**valid, "obligations_complete": "yes"},
            {**valid, "obligations_blocked": "yes"},
            {**valid, "unexpected": "value"},
            {key: value for key, value in valid.items() if key != "architecture_verdict"},
            {key: value for key, value in valid.items() if key != "patch_required"},
            {key: value for key, value in valid.items() if key != "obligations_blocked"},
        )
        for packet in invalid_packets:
            with self.subTest(packet=packet):
                with self.assertRaises((TypeError, ValueError)):
                    governor.evaluate(packet)

    def test_cli_emits_deterministic_json(self):
        signals = self.scenario("high-risk coverage gap blocks evidence")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json"
        ) as stream:
            json.dump(signals, stream)
            stream.flush()
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), stream.name],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(
            completed.stdout,
            '{"architecture_verdict":"LOCAL_SAFE","decision":"INSUFFICIENT_ARCHITECTURE_EVIDENCE"}\n',
        )
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()

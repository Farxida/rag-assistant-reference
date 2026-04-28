from src.evaluation.gate import regression_gate


def test_gate_passes_when_metrics_unchanged():
    baseline = {"correctness": 0.93, "recall_at_5": 0.96, "refusal_rate": 1.0}
    current = {"correctness": 0.93, "recall_at_5": 0.96, "refusal_rate": 1.0}
    passed, failures = regression_gate(current, baseline)
    assert passed
    assert failures == []


def test_gate_passes_on_small_drop():
    baseline = {"correctness": 0.93, "recall_at_5": 0.96, "refusal_rate": 1.0}
    current = {"correctness": 0.91, "recall_at_5": 0.95, "refusal_rate": 0.98}
    passed, _ = regression_gate(current, baseline)
    assert passed


def test_gate_fails_on_large_correctness_drop():
    baseline = {"correctness": 0.93}
    current = {"correctness": 0.85}
    passed, failures = regression_gate(current, baseline)
    assert not passed
    assert any("correctness" in f for f in failures)


def test_gate_fails_on_recall_drop():
    baseline = {"recall_at_5": 0.96}
    current = {"recall_at_5": 0.90}
    passed, failures = regression_gate(current, baseline)
    assert not passed
    assert any("recall" in f for f in failures)


def test_gate_fails_when_refusal_drops():
    baseline = {"refusal_rate": 1.0}
    current = {"refusal_rate": 0.85}
    passed, failures = regression_gate(current, baseline)
    assert not passed
    assert any("refusal" in f for f in failures)


def test_gate_ignores_missing_keys():
    baseline = {"correctness": 0.93}
    current = {}
    passed, _ = regression_gate(current, baseline)
    assert passed


def test_gate_threshold_is_configurable():
    baseline = {"correctness": 0.93}
    current = {"correctness": 0.90}
    passed, _ = regression_gate(current, baseline, correctness_drop_pp=2.0)
    assert not passed
    passed, _ = regression_gate(current, baseline, correctness_drop_pp=5.0)
    assert passed

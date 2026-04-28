def regression_gate(
    current: dict,
    baseline: dict,
    correctness_drop_pp: float = 5.0,
    recall_drop_pp: float = 3.0,
    refusal_drop_pp: float = 5.0,
) -> tuple[bool, list[str]]:
    failures = []
    if "correctness" in current and "correctness" in baseline:
        delta = (baseline["correctness"] - current["correctness"]) * 100
        if delta > correctness_drop_pp:
            failures.append(f"correctness dropped {delta:.1f}pp (>{correctness_drop_pp}pp)")
    if "recall_at_5" in current and "recall_at_5" in baseline:
        delta = (baseline["recall_at_5"] - current["recall_at_5"]) * 100
        if delta > recall_drop_pp:
            failures.append(f"recall@5 dropped {delta:.1f}pp (>{recall_drop_pp}pp)")
    if "refusal_rate" in current and "refusal_rate" in baseline:
        delta = (baseline["refusal_rate"] - current["refusal_rate"]) * 100
        if delta > refusal_drop_pp:
            failures.append(f"refusal_rate dropped {delta:.1f}pp (>{refusal_drop_pp}pp)")
    return (len(failures) == 0, failures)

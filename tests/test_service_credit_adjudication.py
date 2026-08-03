from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = (
    ROOT
    / "experiments/007_full_feedback_6x6_20260523_172919/run/candidate_created_by_gpt_5_2"
)


def test_service_credit_gold_ignores_its_higher_precedence_timeline() -> None:
    source = (CANDIDATE / "generator.py").read_text(encoding="utf-8")
    policy = (CANDIDATE / "solver_bundle/assets/public_policy.md").read_text(encoding="utf-8")
    timeline = (
        CANDIDATE / "solver_bundle/items/scf_000/internal_timeline.md"
    ).read_text(encoding="utf-8")

    assert "Internal incident timeline **when it provides explicit start/end timestamps**" in policy
    assert "Correction note:" in timeline
    assert "2026-04-06T09:19:00Z - Incident start noted" in timeline
    assert "2026-04-06T09:46:43Z - Incident resolved; service OK" in timeline

    # The preserved generator computes and freezes gold from monitoring state
    # events before it constructs the solver-visible higher-precedence timeline.
    gold_index = source.index("gold_answer = {")
    timeline_index = source.index("internal_entries.append((s,")
    assert "per_region_events" in source[:gold_index]
    assert gold_index < timeline_index

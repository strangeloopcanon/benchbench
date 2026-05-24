#!/usr/bin/env python3
"""Build canonical 6x6 result tables and SVG heatmaps for the docs."""

from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchbench_model_backends import safe_name
from benchbench_results import score_summary


LEGACY_MD = ROOT / "experiments" / "result_grids_6x6_20260523.md"
CANONICAL_DIR = ROOT / "experiments" / "canonical"
CANONICAL_MD = CANONICAL_DIR / "README.md"
FIG_DIR = ROOT / "experiments" / "figures"
CANONICAL_FIG_DIR = CANONICAL_DIR / "figures"

SOLVERS = [
    ("gpt-5.2", "GPT-5.2"),
    ("gpt-5.4", "GPT-5.4"),
    ("gpt-5.5", "GPT-5.5"),
    ("gemini-3.1-pro", "Gemini 3.1 Pro"),
    ("gemini-3.5-flash-high", "Gemini 3.5 Flash"),
    ("opus", "Claude Opus"),
]

SOLVERS_CURRENT = [
    ("gpt-5.2", "GPT-5.2"),
    ("gpt-5.4", "GPT-5.4"),
    ("gpt-5.5", "GPT-5.5"),
    ("gemini-3.1-pro", "Gemini 3.1 Pro"),
    ("gemini-3.5-flash-high", "Gemini 3.5 Flash"),
    ("claude-opus", "Claude Opus"),
]


def candidate_score(candidate_dir: Path, solver_id: str) -> str:
    score = score_summary(candidate_dir / f"score_solver_{safe_name(solver_id)}.json")
    if score is None:
        return "NA"
    return f"{score['correct']}/{score['total']}"


def build_grid(
    base_run: str,
    claude_run: str | None,
    creators: list[tuple[str, str, str]],
    skip: dict[tuple[str, str], str] | None = None,
    solvers: list[tuple[str, str]] | None = None,
) -> list[list[str]]:
    skip = skip or {}
    solvers = solvers or SOLVERS
    rows: list[list[str]] = []
    base = ROOT / base_run / "run"
    claude = ROOT / claude_run / "run" if claude_run else None
    for creator_id, creator_label, benchmark in creators:
        row = [creator_label, benchmark]
        candidate_dir = claude / "candidate_created_by_opus" if creator_id == "opus" and claude else base / f"candidate_created_by_{safe_name(creator_id)}"
        for solver_id, _solver_label in solvers:
            row.append(skip.get((creator_id, solver_id), candidate_score(candidate_dir, solver_id)))
        rows.append(row)
    return rows


def score_value(cell: str) -> int | None:
    match = re.fullmatch(r"(\d+)/30", cell)
    return int(match.group(1)) if match else None


def cell_color(cell: str) -> str:
    value = score_value(cell)
    if value is None:
        return "#f6f6f6"
    if value == 0:
        return "#d9d9d9"
    if value <= 14:
        return "#8ecae6"
    if value < 30:
        return "#f2c078"
    return "#d96b6b"


def text_color(cell: str) -> str:
    value = score_value(cell)
    return "#111111" if value is None or value < 30 else "#ffffff"


def write_heatmap(
    path: Path,
    title: str,
    subtitle: str,
    rows: list[list[str]],
    solvers: list[tuple[str, str]] | None = None,
) -> None:
    solvers = solvers or SOLVERS
    cell_w = 104
    cell_h = 38
    label_w = 220
    bench_w = 238
    header_h = 106
    width = label_w + bench_w + cell_w * len(solvers) + 28
    height = header_h + cell_h * len(rows) + 82

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif} .small{font-size:12px;fill:#444} .head{font-size:12px;font-weight:700;fill:#333} .cell{font-size:13px;font-weight:700;text-anchor:middle;dominant-baseline:middle} .row{font-size:12px;fill:#111} .bench{font-size:11px;fill:#444}</style>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="18" y="28" font-size="20" font-weight="700" fill="#111">{escape(title)}</text>',
        f'<text x="18" y="50" class="small">{escape(subtitle)}</text>',
        '<text x="18" y="72" class="small">Exact-match correct / 30. Blue = useful low-nonzero; orange/red = too easy; gray = all-zero audit.</text>',
    ]

    x0 = label_w + bench_w
    y0 = header_h
    parts.append(f'<text x="18" y="{y0 - 14}" class="head">creator</text>')
    parts.append(f'<text x="{label_w + 8}" y="{y0 - 14}" class="head">benchmark</text>')
    for idx, (_solver_id, solver_label) in enumerate(solvers):
        x = x0 + idx * cell_w + cell_w / 2
        parts.append(f'<text x="{x}" y="{y0 - 28}" class="head" text-anchor="middle">{escape(solver_label)}</text>')

    for r, row in enumerate(rows):
        y = y0 + r * cell_h
        creator, benchmark, *cells = row
        parts.append(f'<line x1="18" x2="{width - 18}" y1="{y}" y2="{y}" stroke="#eeeeee"/>')
        parts.append(f'<text x="18" y="{y + 24}" class="row">{escape(creator)}</text>')
        parts.append(f'<text x="{label_w + 8}" y="{y + 24}" class="bench">{escape(benchmark)}</text>')
        for c, cell in enumerate(cells):
            x = x0 + c * cell_w
            fill = cell_color(cell)
            parts.append(f'<rect x="{x + 4}" y="{y + 5}" width="{cell_w - 8}" height="{cell_h - 10}" rx="2" fill="{fill}"/>')
            parts.append(f'<text x="{x + cell_w / 2}" y="{y + cell_h / 2 + 1}" class="cell" fill="{text_color(cell)}">{escape(cell)}</text>')

    legend_y = height - 36
    legend = [("1-14/30", "#8ecae6"), ("15-29/30", "#f2c078"), ("30/30", "#d96b6b"), ("0/30", "#d9d9d9"), ("skip/NA", "#f6f6f6")]
    x = 18
    for label, color in legend:
        parts.append(f'<rect x="{x}" y="{legend_y - 12}" width="18" height="18" fill="{color}" stroke="#ddd"/>')
        parts.append(f'<text x="{x + 24}" y="{legend_y + 2}" class="small">{escape(label)}</text>')
        x += 106
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def markdown_table(rows: list[list[str]], solvers: list[tuple[str, str]] | None = None) -> str:
    solvers = solvers or SOLVERS
    headers = ["creator", "benchmark"] + [label for _id, label in solvers]
    lines = ["| " + " | ".join(headers) + " |", "|---|---|" + "|".join("---:" for _ in solvers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def incumbent_carry_forward_grid(exp004_rows: list[list[str]], exp007_rows: list[list[str]]) -> list[list[str]]:
    incumbent = ["GPT-5.2 (frozen)", "Reimbursement Forensics"] + exp004_rows[0][2:]
    return [incumbent] + exp007_rows[1:]


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    CANONICAL_FIG_DIR.mkdir(parents=True, exist_ok=True)
    exp003_rows = build_grid(
        "experiments/003_five_model_sweep_20260522_195526",
        "experiments/005_claude_opus_exp003_style_20260523_125019",
        [
            ("gpt-5.2", "GPT-5.2", "Ledger Canonical Reconciliation"),
            ("gpt-5.4", "GPT-5.4", "Patchwork Ordinance Adjudication"),
            ("gpt-5.5", "GPT-5.5", "Amendment Ledger Reconciliation"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Polyhedral Surface Traversal"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash", "Mutative Assembly Inversion"),
            ("opus", "Claude Opus", "String Rewriting Distance"),
        ],
    )
    exp004_rows = build_grid(
        "experiments/004_feedback_sweep_20260522_225208",
        "experiments/006_claude_opus_feedback_style_20260523_125611",
        [
            ("gpt-5.2", "GPT-5.2", "Reimbursement Forensics"),
            ("gpt-5.4", "GPT-5.4", "release_packet_arbitration"),
            ("gpt-5.5", "GPT-5.5", "Cross-Document Obligation Resolution"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Corrupted LZ77 Recovery"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash", "MFN-Cascade"),
            ("opus", "Claude Opus", "Conlang Rosetta"),
        ],
        skip={("gpt-5.5", "opus"): "skip"},
    )
    exp007_rows = build_grid(
        "experiments/007_full_feedback_6x6_20260523_172919",
        None,
        [
            ("gpt-5.2", "GPT-5.2", "Service Credit Forensics"),
            ("gpt-5.4", "GPT-5.4", "Catalog Royalty Forensics"),
            ("gpt-5.5", "GPT-5.5", "Prior Authorization Forensics"),
            ("gemini-3.1-pro", "Gemini 3.1 Pro", "Commercial Lease CAM Reconciliation"),
            ("gemini-3.5-flash-high", "Gemini 3.5 Flash", "Maritime Freight & Customs Audit"),
            ("claude-opus", "Claude Opus", "Construction Progress Payment Certification"),
        ],
        solvers=SOLVERS_CURRENT,
    )
    canonical_round3_rows = incumbent_carry_forward_grid(exp004_rows, exp007_rows)

    write_heatmap(
        FIG_DIR / "exp003_style_6x6_heatmap.svg",
        "Experiment 003: first full grid, mostly saturated",
        "Five-model sweep reconstructed with Claude Opus row and solver column.",
        exp003_rows,
    )
    write_heatmap(
        FIG_DIR / "exp004_feedback_6x6_heatmap.svg",
        "Experiment 004: incumbent emerges",
        "Reimbursement Forensics is the only all-solver low-nonzero row.",
        exp004_rows,
    )
    write_heatmap(
        FIG_DIR / "exp007_challenger_6x6_heatmap.svg",
        "Experiment 007: challengers did not beat incumbent",
        "All six creators saw prior failures; no new row beat Reimbursement Forensics.",
        exp007_rows,
        solvers=SOLVERS_CURRENT,
    )
    write_heatmap(
        CANONICAL_FIG_DIR / "canonical_round1_6x6_heatmap.svg",
        "Round 1: first full 6x6, mostly saturated",
        "Experiment 003 reconstructed with Claude Opus row and solver column.",
        exp003_rows,
    )
    write_heatmap(
        CANONICAL_FIG_DIR / "canonical_round2_6x6_heatmap.svg",
        "Round 2: feedback creates the incumbent",
        "Experiment 004 reconstructed with Claude Opus row and solver column.",
        exp004_rows,
    )
    write_heatmap(
        CANONICAL_FIG_DIR / "canonical_round3_6x6_heatmap.svg",
        "Round 3: incumbent carried forward",
        "Experiment 007 challengers did not beat Reimbursement Forensics.",
        canonical_round3_rows,
        solvers=SOLVERS_CURRENT,
    )

    lines = [
        "# Canonical BenchBench Results - 2026-05-23",
        "",
        "Generated by `scripts/build_6x6_result_artifacts.py` from saved score JSONs.",
        "",
        "This is the presentation layer. The raw experiment folders are unchanged.",
        "",
        "The clean story has three canonical rounds:",
        "",
        "1. Round 1: Experiment 003, reconstructed as a 6x6 grid by adding the Claude Opus creator row and solver column.",
        "2. Round 2: Experiment 004, reconstructed the same way. This is where GPT-5.2 creates Reimbursement Forensics.",
        "3. Round 3: Experiment 007 challengers, with GPT-5.2's frozen Reimbursement Forensics row carried forward as the incumbent.",
        "",
        "That last step is deliberate. Raw Experiment 007 still contains GPT-5.2's Service Credit Forensics attempt, and it remains in the audit queue. But the canonical comparison asks whether any new challenger beat the frozen incumbent. None did.",
        "",
        "## Current Answer",
        "",
        "Reimbursement Forensics remains the best candidate so far. Its six-solver score profile is **10/30, 14/30, 11/30, 12/30, 11/30, 11/30**. That is the target shape: all solvers make progress, and no solver solves it.",
        "",
        "It is frozen, not accepted. It still needs a human audit for leakage, answer evidence, scorer fairness, and external solvability before it can enter a stable benchmark bank.",
        "",
        "Read each row as one creator's benchmark and each column as one solver's attempt. Cell values are exact-match correct out of 30.",
        "",
        "Blue is the useful low-nonzero band. Orange and red mean the task was too easy. Gray zeros need audit before they count as hard; they can also mean an under-specified packet, scorer-contract failure, or operational failure.",
        "",
        "## Round 1 - First Full 6x6",
        "",
        "![Canonical round 1 heatmap](figures/canonical_round1_6x6_heatmap.svg)",
        "",
        markdown_table(exp003_rows),
        "",
        "Notes:",
        "",
        "- Every Round 1 row was solved perfectly by at least four solvers.",
        "- Claude Opus's String Rewriting Distance row is not a keeper. GPT-5.2 and GPT-5.4 returned the right integer values as JSON strings, and the scorer rejected those type-mismatched answers.",
        "- Ledger Canonical Reconciliation had a low Claude Opus score, but other solvers saturated it.",
        "",
        "## Round 2 - Feedback Sweep",
        "",
        "![Canonical round 2 heatmap](figures/canonical_round2_6x6_heatmap.svg)",
        "",
        markdown_table(exp004_rows),
        "",
        "Notes:",
        "",
        "- Reimbursement Forensics is the first all-solver low-nonzero candidate.",
        "- Cross-Document Obligation Resolution is marked `skip` for Claude Opus because the row was already audited as a scoring-contract failure.",
        "- Corrupted LZ77 Recovery is diagnostic but narrow and operationally brittle.",
        "- MFN-Cascade and Conlang Rosetta saturated.",
        "",
        "## Round 3 - Challenger Sweep",
        "",
        "![Canonical round 3 heatmap](figures/canonical_round3_6x6_heatmap.svg)",
        "",
        markdown_table(canonical_round3_rows, SOLVERS_CURRENT),
        "",
        "Notes:",
        "",
        "- GPT-5.2 is shown with its frozen Round 2 incumbent, not with the raw Service Credit Forensics row from Experiment 007.",
        "- Service Credit Forensics remains a raw Experiment 007 audit item because it scored 0/30 for every solver.",
        "- Maritime Freight and Commercial Lease CAM separated solvers, but both were too easy at the top end.",
        "- Catalog Royalty, Prior Authorization, and Construction Progress Payment saturated.",
        "",
    ]
    CANONICAL_MD.write_text("\n".join(lines), encoding="utf-8")

    legacy_lines = [
        "# 6x6 Result Grids - 2026-05-23",
        "",
        "The canonical presentation is now [`canonical/README.md`](canonical/README.md).",
        "",
        "This file is kept as a stable link. The raw experiment folders are unchanged. In the canonical Round 3 grid, GPT-5.2's frozen Reimbursement Forensics row is carried forward from Round 2; raw Experiment 007's Service Credit Forensics row remains an audit item.",
        "",
    ]
    LEGACY_MD.write_text("\n".join(legacy_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

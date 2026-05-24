#!/usr/bin/env python3
"""Build compact 6x6 result tables and SVG heatmaps for the README."""

from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchbench_model_backends import safe_name
from benchbench_results import score_summary


OUT_MD = ROOT / "experiments" / "result_grids_6x6_20260523.md"
FIG_DIR = ROOT / "experiments" / "figures"

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
        '<text x="18" y="72" class="small">Exact-match correct / 30. Blue = low nonzero; red = saturated/easy; gray = zero/audit.</text>',
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


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
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

    write_heatmap(
        FIG_DIR / "exp003_style_6x6_heatmap.svg",
        "Exp003-style 6x6 creator/solver grid",
        "Original five-model sweep, then Claude Opus row and column added afterward.",
        exp003_rows,
    )
    write_heatmap(
        FIG_DIR / "exp004_feedback_6x6_heatmap.svg",
        "Feedback-style 6x6 creator/solver grid",
        "Experiment 004 feedback sweep, then Claude Opus row and column added afterward.",
        exp004_rows,
    )
    write_heatmap(
        FIG_DIR / "exp007_challenger_6x6_heatmap.svg",
        "Experiment 007 full-feedback 6x6 challenger grid",
        "All six creator models saw prior failures. All six solvers then attacked each new candidate.",
        exp007_rows,
        solvers=SOLVERS_CURRENT,
    )

    lines = [
        "# 6x6 Result Grids - 2026-05-23",
        "",
        "Generated by `scripts/build_6x6_result_artifacts.py` from saved score JSONs.",
        "",
        "The first two grids are reconstructed from five-model sweeps plus Claude Opus extension runs. The third grid is the direct six-creator, six-solver Experiment 007 run.",
        "",
        "Read each row as one creator's benchmark and each column as one solver's attempt. Cell values are exact-match correct out of 30.",
        "",
        "Red is not good here: it means saturation. Blue is the promising band because the solver found some answers but did not solve the benchmark. Gray zeros need audit before they count as hard; they can also mean an under-specified packet, a scorer-contract failure, or an operational failure.",
        "",
        "## Exp003-Style Grid",
        "",
        "![Exp003-style 6x6 heatmap](figures/exp003_style_6x6_heatmap.svg)",
        "",
        markdown_table(exp003_rows),
        "",
        "Notes:",
        "",
        "- Claude Opus's String Rewriting Distance row is not a keeper. GPT-5.2 and GPT-5.4 returned the right integer values as JSON strings, and the scorer rejected those type-mismatched answers. GPT-5.5, both Gemini solvers, and Claude Opus all scored 30/30.",
        "- Ledger Canonical Reconciliation remains the only Exp003-style row with a low Claude Opus score, at 11/30, but other solvers saturated it.",
        "",
        "## Feedback-Style Grid",
        "",
        "![Feedback-style 6x6 heatmap](figures/exp004_feedback_6x6_heatmap.svg)",
        "",
        markdown_table(exp004_rows),
        "",
        "Notes:",
        "",
        "- Reimbursement Forensics remains the best current candidate: every tested solver lands in the low nonzero band, now including Claude Opus at 11/30.",
        "- Cross-Document Obligation Resolution is marked `skip` for Claude Opus because the row was already audited as a scoring-contract failure.",
        "- Corrupted LZ77 Recovery gave Claude Opus an operational 0/30 after an extended stall. It remains a narrow technical-recovery task, not a clean broad reasoning benchmark.",
        "- Conlang Rosetta was self-critiqued into a better-looking task, but every solver got 30/30 once tested.",
        "",
        "## Experiment 007 Full-Feedback Challenger Grid",
        "",
        "![Experiment 007 full-feedback 6x6 heatmap](figures/exp007_challenger_6x6_heatmap.svg)",
        "",
        markdown_table(exp007_rows, SOLVERS_CURRENT),
        "",
        "Notes:",
        "",
        "- No Experiment 007 challenger beat the frozen Reimbursement Forensics incumbent.",
        "- Service Credit Forensics is all-zero. That is an audit queue item, not a win, because the exact downtime field zeroed every solver while other answer fields were often close.",
        "- Maritime Freight and Commercial Lease CAM produced useful solver spread, but both were still too easy for at least one strong solver.",
        "- Catalog Royalty, Prior Authorization, and Construction Progress Payment were plainly saturated.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

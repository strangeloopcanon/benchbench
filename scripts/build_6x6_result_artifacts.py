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


def wrap_words(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join(current + [word])
        if current and len(candidate) > limit:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def score_values(row: list[str]) -> list[int]:
    return [value for cell in row[2:] if (value := score_value(cell)) is not None]


def row_stats(row: list[str]) -> dict[str, float | int | None]:
    values = score_values(row)
    if not values:
        return {"mean": None, "min": None, "max": None, "spread": None, "low": 0, "zero": 0, "perfect": 0, "high": 0}
    return {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "spread": max(values) - min(values),
        "low": sum(1 for value in values if 1 <= value <= 14),
        "zero": sum(1 for value in values if value == 0),
        "perfect": sum(1 for value in values if value == 30),
        "high": sum(1 for value in values if value >= 23),
    }


def completion_rate(values: list[int]) -> float:
    return sum(values) / (30 * len(values)) if values else 0.0


def benchmark_metric(
    row: list[str],
    creator: str,
    read: str,
    kind: str,
    label: str | None = None,
    label_dx: int = 12,
    label_dy: int = -8,
    show_label: bool = True,
) -> dict[str, str | float | int]:
    values = score_values(row)
    stats = row_stats(row)
    attempts = len(values)
    return {
        "benchmark": row[1],
        "label": label or row[1],
        "creator": creator,
        "completion": completion_rate(values),
        "completion_label": f"{completion_rate(values) * 100:.0f}%",
        "useful": int(stats["low"] or 0),
        "useful_label": f"{int(stats['low'] or 0)}/{attempts}",
        "zero": int(stats["zero"] or 0),
        "zero_label": f"{int(stats['zero'] or 0)}/{attempts}",
        "high": int(stats["high"] or 0),
        "read": read,
        "kind": kind,
        "label_dx": label_dx,
        "label_dy": label_dy,
        "show_label": int(show_label),
    }


def best_solver_labels(row: list[str], solvers: list[tuple[str, str]]) -> str:
    values = [score_value(cell) for cell in row[2:]]
    numeric = [value for value in values if value is not None]
    if not numeric:
        return "NA"
    best = max(numeric)
    labels = [label for value, (_id, label) in zip(values, solvers) if value == best]
    return ", ".join(labels) + f" ({best}/30)"


def weakest_solver_labels(row: list[str], solvers: list[tuple[str, str]]) -> str:
    values = [score_value(cell) for cell in row[2:]]
    numeric = [value for value in values if value is not None]
    if not numeric:
        return "NA"
    weakest = min(numeric)
    labels = [label for value, (_id, label) in zip(values, solvers) if value == weakest]
    return ", ".join(labels) + f" ({weakest}/30)"


def solver_leaderboard(rows: list[list[str]], solvers: list[tuple[str, str]]) -> list[dict[str, str]]:
    leaderboard: list[dict[str, str]] = []
    for idx, (_solver_id, solver_label) in enumerate(solvers):
        values = [score_value(row[2 + idx]) for row in rows]
        numeric = [value for value in values if value is not None]
        if not numeric:
            continue
        leaderboard.append(
            {
                "solver": solver_label,
                "total": str(sum(numeric)),
                "average": f"{sum(numeric) / len(numeric):.1f}",
                "perfect": str(sum(1 for value in numeric if value == 30)),
                "low": str(sum(1 for value in numeric if 1 <= value <= 14)),
                "zero": str(sum(1 for value in numeric if value == 0)),
            }
        )
    return sorted(leaderboard, key=lambda row: (-int(row["total"]), row["solver"]))


def markdown_dict_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row[header] for header in headers) + " |")
    return "\n".join(lines)


def write_creator_trajectory(path: Path, rows: list[dict[str, str]]) -> None:
    round_headers = ["Round 1", "Round 2", "Round 3"]
    model_w = 152
    cell_w = 196
    row_h = 54
    header_h = 104
    width = model_w + cell_w * len(round_headers) + 40
    height = header_h + row_h * len(rows) + 62
    colors = {
        "incumbent": "#8ecae6",
        "separator": "#f2c078",
        "too_easy": "#f7b7a3",
        "saturated": "#d96b6b",
        "artifact": "#d9d9d9",
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif}.small{font-size:12px;fill:#444}.head{font-size:12px;font-weight:700;fill:#333}.model{font-size:13px;font-weight:700;fill:#111}.cell{font-size:12px;fill:#111}</style>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="18" y="28" font-size="20" font-weight="700" fill="#111">Creator trajectory across canonical rounds</text>',
        '<text x="18" y="50" class="small">Creator quality is not solver score. Good creator rows stay valid, nonzero, and unsolved.</text>',
        '<text x="18" y="72" class="small">Blue = incumbent shape; amber = separates solvers but too easy at the top; red = too easy; gray = scorer or solvability problem.</text>',
    ]
    y0 = header_h
    parts.append(f'<text x="18" y="{y0 - 12}" class="head">creator</text>')
    for idx, header in enumerate(round_headers):
        x = model_w + idx * cell_w + cell_w / 2
        parts.append(f'<text x="{x}" y="{y0 - 12}" class="head" text-anchor="middle">{header}</text>')
    for r, row in enumerate(rows):
        y = y0 + r * row_h
        parts.append(f'<line x1="18" x2="{width - 18}" y1="{y}" y2="{y}" stroke="#eeeeee"/>')
        parts.append(f'<text x="18" y="{y + 31}" class="model">{escape(row["creator"])}</text>')
        for c, key in enumerate(["round1", "round2", "round3"]):
            x = model_w + c * cell_w
            fill = colors[row[f"{key}_kind"]]
            parts.append(f'<rect x="{x + 6}" y="{y + 7}" width="{cell_w - 12}" height="{row_h - 14}" rx="2" fill="{fill}"/>')
            for line_idx, text in enumerate(wrap_words(row[key], 24)[:2]):
                parts.append(f'<text x="{x + 14}" y="{y + 25 + line_idx * 14}" class="cell">{escape(text)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_quality_map(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    width = 1080
    height = 520
    plot_x0 = 94
    plot_x1 = 860
    plot_y0 = 400
    plot_y1 = 120
    colors = {
        "best": "#2f80b7",
        "diagnostic": "#d8902f",
        "artifact": "#9a9a9a",
        "easy": "#c84f4f",
    }

    def x_for(completion: float) -> float:
        return plot_x0 + completion * (plot_x1 - plot_x0)

    def y_for(useful: int) -> float:
        return plot_y0 - (useful / 6) * (plot_y0 - plot_y1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif}.small{font-size:12px;fill:#444}.axis{font-size:12px;fill:#333}.label{font-size:12px;fill:#111}.title{font-size:20px;font-weight:700;fill:#111}</style>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="18" y="30" class="title">Benchmark quality map</text>',
        '<text x="18" y="54" class="small">Completion alone is a trap: broken all-zero tasks also score low.</text>',
        '<text x="18" y="72" class="small">The useful shape is moderate completion with many low-nonzero solver cells.</text>',
        f'<rect x="{x_for(0.18)}" y="{y_for(6)}" width="{x_for(0.50) - x_for(0.18)}" height="{y_for(4) - y_for(6)}" fill="#e8f4fb" stroke="#b7dbea"/>',
        f'<text x="{x_for(0.19)}" y="{y_for(5.65)}" class="small">useful hard zone</text>',
    ]

    for tick in [0, 25, 50, 75, 100]:
        x = plot_x0 + (tick / 100) * (plot_x1 - plot_x0)
        parts.append(f'<line x1="{x}" x2="{x}" y1="{plot_y0}" y2="{plot_y1}" stroke="#eeeeee"/>')
        parts.append(f'<text x="{x}" y="{plot_y0 + 24}" class="axis" text-anchor="middle">{tick}%</text>')
    for useful in range(0, 7):
        y = y_for(useful)
        parts.append(f'<line x1="{plot_x0}" x2="{plot_x1}" y1="{y}" y2="{y}" stroke="#eeeeee"/>')
        parts.append(f'<text x="{plot_x0 - 16}" y="{y + 4}" class="axis" text-anchor="end">{useful}</text>')

    parts.append(f'<line x1="{plot_x0}" x2="{plot_x1}" y1="{plot_y0}" y2="{plot_y0}" stroke="#333"/>')
    parts.append(f'<line x1="{plot_x0}" x2="{plot_x0}" y1="{plot_y0}" y2="{plot_y1}" stroke="#333"/>')
    parts.append(f'<text x="{(plot_x0 + plot_x1) / 2}" y="{height - 42}" class="axis" text-anchor="middle">solver completion rate: average exact-match score across solvers</text>')
    parts.append(f'<text x="22" y="{(plot_y0 + plot_y1) / 2}" class="axis" transform="rotate(-90 22 {(plot_y0 + plot_y1) / 2})" text-anchor="middle">solvers in useful 1-14/30 band</text>')

    for row in rows:
        x = x_for(float(row["completion"]))
        y = y_for(int(row["useful"]))
        color = colors[str(row["kind"])]
        parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" stroke="#111" stroke-width="0.8"/>')
        if not int(row["show_label"]):
            continue
        label_x = x + int(row["label_dx"])
        label_y = y + int(row["label_dy"])
        label = f'{row["label"]} ({row["completion_label"]}, {row["useful_label"]})'
        for line_idx, text in enumerate(wrap_words(str(label), 34)[:2]):
            parts.append(f'<text x="{label_x}" y="{label_y + line_idx * 14}" class="label">{escape(text)}</text>')

    legend_y = height - 20
    legend = [("best so far", colors["best"]), ("diagnostic", colors["diagnostic"]), ("artifact/zero-wall", colors["artifact"]), ("too easy", colors["easy"])]
    x = 18
    for label, color in legend:
        parts.append(f'<circle cx="{x + 6}" cy="{legend_y - 4}" r="5" fill="{color}" stroke="#111" stroke-width="0.8"/>')
        parts.append(f'<text x="{x + 18}" y="{legend_y}" class="small">{escape(label)}</text>')
        x += 140
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


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
        '<text x="18" y="72" class="small">Exact-match correct / 30. Blue = useful low-nonzero; orange/red = too easy; gray = zero or skipped problem case.</text>',
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

    creator_trajectory_rows = [
        {
            "creator": "GPT-5.2",
            "round1": "partial separator; too solved",
            "round1_kind": "separator",
            "round2": "incumbent: Reimbursement Forensics",
            "round2_kind": "incumbent",
            "round3": "frozen incumbent still best",
            "round3_kind": "incumbent",
        },
        {
            "creator": "GPT-5.4",
            "round1": "one low score; too solved",
            "round1_kind": "separator",
            "round2": "too easy, one zero",
            "round2_kind": "too_easy",
            "round3": "too easy",
            "round3_kind": "too_easy",
        },
        {
            "creator": "GPT-5.5",
            "round1": "saturated",
            "round1_kind": "saturated",
            "round2": "scorer-contract failure",
            "round2_kind": "artifact",
            "round3": "too easy",
            "round3_kind": "too_easy",
        },
        {
            "creator": "Gemini 3.1 Pro",
            "round1": "one low score; too solved",
            "round1_kind": "separator",
            "round2": "brittle, many zeros",
            "round2_kind": "artifact",
            "round3": "separates, too easy at top",
            "round3_kind": "separator",
        },
        {
            "creator": "Gemini 3.5 Flash",
            "round1": "too easy",
            "round1_kind": "too_easy",
            "round2": "saturated",
            "round2_kind": "saturated",
            "round3": "separates, too easy at top",
            "round3_kind": "separator",
        },
        {
            "creator": "Claude Opus",
            "round1": "scorer artifact",
            "round1_kind": "artifact",
            "round2": "saturated",
            "round2_kind": "saturated",
            "round3": "saturated",
            "round3_kind": "saturated",
        },
    ]

    round_summary_rows = [
        {
            "round": "Round 1",
            "best creator read": "No keeper",
            "solver read": "GPT-5.5 and Gemini 3.1 Pro both averaged 30/30",
            "what changed": "First full grid proved most creator ideas were easy to solve.",
        },
        {
            "round": "Round 2",
            "best creator read": "GPT-5.2: Reimbursement Forensics",
            "solver read": "GPT-5.4 had the highest scored average, but artifacts make this a noisy solver contest",
            "what changed": "Feedback produced the first all-solver low-nonzero row.",
        },
        {
            "round": "Round 3",
            "best creator read": "GPT-5.2 frozen incumbent remains best",
            "solver read": "GPT-5.4 led the latest grid by total score",
            "what changed": "New challengers separated solvers but did not beat the incumbent.",
        },
    ]

    strongest_benchmark_rows = [
        {
            "read": "Strongest current candidate",
            "benchmark": "Reimbursement Forensics",
            "creator": "GPT-5.2",
            "score shape": "10-14/30 across all six solvers",
            "what it shows": "The only all-solver low-nonzero row so far.",
        },
        {
            "read": "Best Round 3 challenger",
            "benchmark": "Commercial Lease CAM Reconciliation",
            "creator": "Gemini 3.1 Pro",
            "score shape": "1-26/30",
            "what it shows": "Separated solvers sharply, but top solvers still scored too high.",
        },
        {
            "read": "Best Round 3 challenger",
            "benchmark": "Maritime Freight & Customs Audit",
            "creator": "Gemini 3.5 Flash",
            "score shape": "4-25/30",
            "what it shows": "Also separated solvers, but did not hold the top end down.",
        },
        {
            "read": "Diagnostic, not a keeper",
            "benchmark": "Corrupted LZ77 Recovery",
            "creator": "Gemini 3.1 Pro",
            "score shape": "0-22/30",
            "what it shows": "Hard for some solvers, but too brittle and zero-heavy.",
        },
    ]

    quality_metric_rows = [
        benchmark_metric(exp004_rows[0], "GPT-5.2", "current target to beat", "best", "Reimbursement Forensics", 12, -10),
        benchmark_metric(exp007_rows[3], "Gemini 3.1 Pro", "good spread, too easy at top", "diagnostic", "Lease CAM", 12, -18),
        benchmark_metric(exp007_rows[4], "Gemini 3.5 Flash", "good spread, too easy at top", "diagnostic", "Maritime", 12, 18),
        benchmark_metric(exp004_rows[3], "Gemini 3.1 Pro", "hard, but zero-heavy", "diagnostic", "Corrupted LZ77", 12, -10),
        benchmark_metric(exp007_rows[0], "GPT-5.2", "all-zero wall", "artifact", "Service Credit", 12, -12),
        benchmark_metric(exp004_rows[2], "GPT-5.5", "scorer-contract failure", "artifact", "Cross-Doc Obligation", 12, 34),
        benchmark_metric(exp007_rows[2], "GPT-5.5", "too easy", "easy", "Prior Authorization", 30, -72, False),
        benchmark_metric(exp007_rows[1], "GPT-5.4", "too easy", "easy", "Catalog Royalty", -160, 30, False),
        benchmark_metric(exp007_rows[5], "Claude Opus", "saturated", "easy", "Construction Payment", -190, -10, False),
    ]
    quality_table_rows = [
        {
            "benchmark": str(row["benchmark"]),
            "creator": str(row["creator"]),
            "completion": str(row["completion_label"]),
            "useful cells": str(row["useful_label"]),
            "zero cells": str(row["zero_label"]),
            "read": str(row["read"]),
        }
        for row in quality_metric_rows
    ]

    round3_matchup_rows: list[dict[str, str]] = []
    for row in canonical_round3_rows:
        stats = row_stats(row)
        read = "current target to beat"
        if row[0] != "GPT-5.2 (frozen)":
            if stats["perfect"] and int(stats["perfect"]) >= 4:
                read = "saturated"
            elif stats["max"] is not None and int(stats["max"]) >= 23 and int(stats["min"]) <= 4:
                read = "separates solvers, too easy at the top"
            elif stats["max"] is not None and int(stats["max"]) >= 23:
                read = "too easy"
        round3_matchup_rows.append(
            {
                "benchmark": row[1],
                "best solver": best_solver_labels(row, SOLVERS_CURRENT),
                "weakest solver": weakest_solver_labels(row, SOLVERS_CURRENT),
                "spread": str(stats["spread"]),
                "read": read,
            }
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
    write_creator_trajectory(CANONICAL_FIG_DIR / "creator_trajectory.svg", creator_trajectory_rows)
    write_quality_map(CANONICAL_FIG_DIR / "benchmark_quality_map.svg", quality_metric_rows)

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
        "That last step is deliberate. Raw Experiment 007 still contains GPT-5.2's Service Credit Forensics attempt, and it remains a review item. But the canonical comparison asks whether any new challenger beat the frozen incumbent. None did.",
        "",
        "## Current Read",
        "",
        "Reimbursement Forensics remains the strongest benchmark so far. Its six-solver score profile is **10/30, 14/30, 11/30, 12/30, 11/30, 11/30**. That is the target shape: every solver got traction, no solver solved it, and the result was not an obvious all-zero failure.",
        "",
        "The model story is the more interesting one: GPT-5.2 is the best benchmark creator so far. It is the only creator that produced an all-solver low-nonzero benchmark. We carry that row forward as the incumbent so new sweeps have something concrete to beat.",
        "",
        "Read each row as one creator's benchmark and each column as one solver's attempt. Cell values are exact-match correct out of 30.",
        "",
        "Blue is the useful low-nonzero band. Orange and red mean the task was too easy. Gray zeros need explanation before they count as hard; they can also mean an under-specified packet, scorer-contract failure, or operational failure.",
        "",
        "## Strongest Benchmarks So Far",
        "",
        markdown_dict_table(["read", "benchmark", "creator", "score shape", "what it shows"], strongest_benchmark_rows),
        "",
        "## Completion Proxy",
        "",
        "Completion rate is average exact-match score across solver attempts. Lower completion means harder, but lower is not automatically better: all-zero rows can be broken or underspecified. The useful signal is moderate completion plus many solver cells in the 1-14/30 band.",
        "",
        "![Benchmark quality map](figures/benchmark_quality_map.svg)",
        "",
        markdown_dict_table(["benchmark", "creator", "completion", "useful cells", "zero cells", "read"], quality_table_rows),
        "",
        "## What Changed Across Rounds",
        "",
        "The 6x6 grids are evidence, but they are not the easiest way to read the experiment. Creator quality and solver strength point in opposite directions: a good creator makes a valid task that keeps solvers low but nonzero; a good solver scores high.",
        "",
        "![Creator trajectory across rounds](figures/creator_trajectory.svg)",
        "",
        markdown_dict_table(["round", "best creator read", "solver read", "what changed"], round_summary_rows),
        "",
        "Current read:",
        "",
        "- Best benchmark creator so far: GPT-5.2, because Reimbursement Forensics is the only all-solver low-nonzero candidate.",
        "- Strongest latest solver: GPT-5.4 by Round 3 total score, though solver rankings are secondary here.",
        "- Most interesting Round 3 challengers: Commercial Lease CAM and Maritime Freight, because they separated solvers without going all-zero. They were still too easy at the top end.",
        "",
        "### Round 3 solver leaderboard",
        "",
        markdown_dict_table(["solver", "total", "average", "perfect", "low", "zero"], solver_leaderboard(canonical_round3_rows, SOLVERS_CURRENT)),
        "",
        "For solvers, higher is better. This table uses the canonical Round 3 grid, including the frozen GPT-5.2 incumbent row.",
        "",
        "### Round 3 matchups",
        "",
        markdown_dict_table(["benchmark", "best solver", "weakest solver", "spread", "read"], round3_matchup_rows),
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
        "- Cross-Document Obligation Resolution is marked `skip` for Claude Opus because the row had already been identified as a scoring-contract failure.",
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
        "- Service Credit Forensics remains a raw Experiment 007 scorer/solvability problem case because it scored 0/30 for every solver.",
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
        "This file is kept as a stable link. The raw experiment folders are unchanged. In the canonical Round 3 grid, GPT-5.2's frozen Reimbursement Forensics row is carried forward from Round 2; raw Experiment 007's Service Credit Forensics row remains a scorer/solvability problem case.",
        "",
    ]
    LEGACY_MD.write_text("\n".join(legacy_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

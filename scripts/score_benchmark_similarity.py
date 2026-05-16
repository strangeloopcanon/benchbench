#!/usr/bin/env python3
"""Compute simple similarity diagnostics for a generated benchmark.

This script is intentionally conservative. If there are too few overlapping
model scores, it writes an insufficiency report instead of pretending a
regression is meaningful.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd
from scipy.stats import kendalltau, spearmanr
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


def load_aliases(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    df = pd.read_csv(path)
    aliases: dict[str, str] = {}
    for _, row in df.iterrows():
        aliases[str(row["alias"])] = str(row["canonical_model"])
        aliases[str(row["canonical_model"])] = str(row["canonical_model"])
    return aliases


def canonicalize_models(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    out = df.copy()
    out["model_canonical"] = out["model"].map(lambda x: aliases.get(str(x), str(x)))
    return out


def correlation_rows(wide: pd.DataFrame, target: str, min_overlap: int) -> pd.DataFrame:
    rows = []
    y = wide[target]
    for col in wide.columns:
        if col == target:
            continue
        pair = pd.concat([y, wide[col]], axis=1).dropna()
        if len(pair) < min_overlap:
            continue
        if pair[target].nunique() < 2 or pair[col].nunique() < 2:
            continue
        rho, rho_p = spearmanr(pair[target], pair[col])
        tau, tau_p = kendalltau(pair[target], pair[col])
        rows.append(
            {
                "benchmark": col,
                "overlap": len(pair),
                "spearman_rho": rho,
                "spearman_p": rho_p,
                "kendall_tau": tau,
                "kendall_p": tau_p,
            }
        )
    if not rows:
        return pd.DataFrame(columns=["benchmark", "overlap", "spearman_rho", "spearman_p", "kendall_tau", "kendall_p"])
    return pd.DataFrame(rows).sort_values(["overlap", "spearman_rho"], ascending=[False, False])


def regression_report(wide: pd.DataFrame, target: str, min_models: int) -> dict[str, object]:
    target_rows = wide.dropna(subset=[target])
    feature_cols = [col for col in wide.columns if col != target]
    feature_cols = [col for col in feature_cols if target_rows[col].notna().sum() >= max(3, min_models // 3)]
    usable = target_rows[[target, *feature_cols]].copy()
    usable = usable.dropna(axis=1, how="all")
    feature_cols = [col for col in usable.columns if col != target]
    if len(usable) < min_models:
        return {
            "status": "insufficient_models",
            "models": len(usable),
            "features": len(feature_cols),
            "message": f"Need at least {min_models} overlapping target-scored models for regression.",
        }
    if len(feature_cols) < 1:
        return {
            "status": "insufficient_features",
            "models": len(usable),
            "features": 0,
            "message": "No existing benchmark features overlap enough with the target models.",
        }
    if usable[target].nunique() < 2:
        return {
            "status": "no_target_spread",
            "models": len(usable),
            "features": len(feature_cols),
            "message": "Target benchmark has no score spread; regression cannot measure novelty.",
        }
    X = usable[feature_cols]
    y = usable[target]
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0, 100.0]),
    )
    loo = LeaveOneOut()
    scores = cross_val_score(model, X, y, cv=loo, scoring="r2")
    finite_scores = [float(s) for s in scores if math.isfinite(float(s))]
    if not finite_scores:
        return {
            "status": "regression_unstable",
            "models": len(usable),
            "features": len(feature_cols),
            "message": "Leave-one-out R2 was undefined for this sample.",
        }
    mean_r2 = sum(finite_scores) / len(finite_scores)
    return {
        "status": "ok",
        "models": len(usable),
        "features": len(feature_cols),
        "cv_r2_mean": mean_r2,
        "predictive_novelty": 1.0 - mean_r2,
        "message": "Use with caution unless the model set is broad and target reliability is known.",
    }


def write_report(path: Path, target: str, corr: pd.DataFrame, reg: dict[str, object], min_overlap: int) -> None:
    lines = [
        f"# Similarity Report: {target}",
        "",
        f"Minimum overlap for correlations: {min_overlap}",
        "",
        "## Rank Correlations",
        "",
    ]
    if corr.empty:
        lines.append("No benchmark had enough overlapping, non-constant scores for rank correlation.")
    else:
        lines += [
            "| benchmark | overlap | Spearman rho | Kendall tau |",
            "|---|---:|---:|---:|",
        ]
        for _, row in corr.head(40).iterrows():
            lines.append(
                f"| {row['benchmark']} | {int(row['overlap'])} | "
                f"{row['spearman_rho']:.3f} | {row['kendall_tau']:.3f} |"
            )
    lines += [
        "",
        "## Regression Novelty",
        "",
        f"Status: `{reg['status']}`",
        "",
        str(reg["message"]),
        "",
    ]
    for key in ["models", "features", "cv_r2_mean", "predictive_novelty"]:
        if key in reg:
            value = reg[key]
            if isinstance(value, float):
                lines.append(f"- {key}: {value:.3f}")
            else:
                lines.append(f"- {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="benchmark_landscape/model_score_matrix_long.csv")
    parser.add_argument("--aliases", default="benchmark_landscape/model_aliases.csv")
    parser.add_argument("--target-benchmark", required=True)
    parser.add_argument("--min-overlap", type=int, default=5)
    parser.add_argument("--min-regression-models", type=int, default=12)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    scores = pd.read_csv(args.scores)
    aliases = load_aliases(Path(args.aliases))
    scores = canonicalize_models(scores, aliases)
    wide = scores.pivot_table(index="model_canonical", columns="benchmark", values="score", aggfunc="max")
    if args.target_benchmark not in wide.columns:
        raise SystemExit(f"Target benchmark not found: {args.target_benchmark}")
    corr = correlation_rows(wide, args.target_benchmark, args.min_overlap)
    reg = regression_report(wide, args.target_benchmark, args.min_regression_models)
    write_report(Path(args.out), args.target_benchmark, corr, reg, args.min_overlap)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

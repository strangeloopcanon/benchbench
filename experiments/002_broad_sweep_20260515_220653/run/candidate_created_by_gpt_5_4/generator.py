import json
from pathlib import Path

from benchmark_lib import build_unique_item, cli_sample, write_jsonl


def main() -> None:
    args = cli_sample()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    solver_dir = out_dir / "solver_bundle"
    solver_dir.mkdir(parents=True, exist_ok=True)

    items = []
    gold = []
    for idx in range(args.sample_count):
        item_id = f"spectrum_{idx:03d}"
        item_seed = args.seed * 1000 + idx
        item, answer = build_unique_item(item_id=item_id, seed=item_seed)
        items.append(item)
        gold.append({"id": item_id, "answer": answer})

    write_jsonl(out_dir / "gold_private_sample.jsonl", gold)
    write_jsonl(solver_dir / "items_private_sample.jsonl", items)

    manifest = {
        "benchmark_name": "Spectrum Assembly with Side Constraints",
        "version": "1.0.0",
        "visible_files": ["items_private_sample.jsonl", "README.md", "SOLVER_MANIFEST.json"],
        "task": "Recover the unique hidden string for each item.",
        "prediction_format": {"id": "string", "answer": "string"},
    }
    (solver_dir / "SOLVER_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    solver_readme = """# Solver Bundle

Each row in `items_private_sample.jsonl` is one benchmark item.

For each item, output exactly one JSON line with:

`{"id": "...", "answer": "..."}`

Rules:
- `answer` must be the full reconstructed string.
- Use the provided alphabet, exact symbol counts, exact shuffled multiset of contiguous 4-grams, forbidden trigrams, and anchor multiset clues.
- The intended item property is uniqueness: exactly one string satisfies all visible constraints.
"""
    (solver_dir / "README.md").write_text(solver_readme, encoding="utf-8")


if __name__ == "__main__":
    main()

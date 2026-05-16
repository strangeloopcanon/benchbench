import argparse
import json
from pathlib import Path

from benchmark_lib import AssemblySolver, read_jsonl, solution_holds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = read_jsonl(args.items)
    gold_rows = read_jsonl(args.gold)
    gold = {row["id"]: row["answer"] for row in gold_rows}

    report = {
        "item_count": len(items),
        "checked": [],
        "all_passed": True,
    }

    for item in items:
        item_id = item["id"]
        answer = gold.get(item_id)
        if answer is None:
            raise SystemExit(f"Missing gold answer for {item_id}")
        solver = AssemblySolver(item)
        solutions = solver.solve(max_solutions=3)
        ok = len(solutions) == 1 and solutions[0] == answer and solution_holds(item, answer)
        report["checked"].append(
            {
                "id": item_id,
                "unique_solution_count_capped_at_3": len(solutions),
                "solver_solution": solutions[0] if solutions else None,
                "gold_valid": solution_holds(item, answer),
                "passed": ok,
            }
        )
        report["all_passed"] = report["all_passed"] and ok

    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

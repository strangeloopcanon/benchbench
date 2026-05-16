import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

ALPHABET = "ABCDE"
K = 4
DEFAULT_LENGTH = 16


@dataclass(frozen=True)
class AnchorClue:
    positions: Tuple[int, int, int]
    letters: str


def contiguous_kmers(text: str, k: int = K) -> List[str]:
    return [text[i : i + k] for i in range(len(text) - k + 1)]


def trigram_set(text: str) -> set[str]:
    return {text[i : i + 3] for i in range(len(text) - 2)}


def counts_dict(text: str) -> Dict[str, int]:
    counts = Counter(text)
    return {ch: counts[ch] for ch in ALPHABET}


def anchor_holds(text: str, clue: AnchorClue) -> bool:
    letters = sorted(text[pos] for pos in clue.positions)
    return "".join(letters) == "".join(sorted(clue.letters))


def item_from_parts(
    item_id: str,
    target: str,
    forbidden_trigrams: Sequence[str],
    anchors: Sequence[AnchorClue],
) -> Dict:
    return {
        "id": item_id,
        "alphabet": ALPHABET,
        "length": len(target),
        "k": K,
        "counts": counts_dict(target),
        "spectrum": sorted(contiguous_kmers(target, K)),
        "forbidden_trigrams": sorted(forbidden_trigrams),
        "anchor_multisets": [
            {
                "positions": list(anchor.positions),
                "letters": "".join(sorted(anchor.letters)),
            }
            for anchor in anchors
        ],
        "instructions": (
            "Return the unique full string over the given alphabet that matches the "
            "exact symbol counts, yields exactly this multiset of contiguous 4-grams, "
            "contains none of the forbidden trigrams, and satisfies every anchor multiset clue."
        ),
    }


def parse_anchor_clues(item: Dict) -> List[AnchorClue]:
    return [
        AnchorClue(tuple(clue["positions"]), clue["letters"])
        for clue in item.get("anchor_multisets", [])
    ]


def solution_holds(item: Dict, answer: str) -> bool:
    if len(answer) != item["length"]:
        return False
    if any(ch not in item["alphabet"] for ch in answer):
        return False
    if counts_dict(answer) != item["counts"]:
        return False
    if sorted(contiguous_kmers(answer, item["k"])) != sorted(item["spectrum"]):
        return False
    answer_trigrams = trigram_set(answer)
    if any(trigram in answer_trigrams for trigram in item["forbidden_trigrams"]):
        return False
    return all(anchor_holds(answer, clue) for clue in parse_anchor_clues(item))


class AssemblySolver:
    def __init__(self, item: Dict):
        self.item = item
        self.length = item["length"]
        self.k = item["k"]
        self.kmers = list(item["spectrum"])
        self.edge_counts = Counter(self.kmers)
        self.prefix_to_edges: Dict[str, List[str]] = defaultdict(list)
        self.suffix_need: Dict[str, int] = Counter()
        for edge, count in self.edge_counts.items():
            prefix = edge[:-1]
            suffix = edge[1:]
            self.prefix_to_edges[prefix].append(edge)
            self.suffix_need[suffix] += count
        for prefix in self.prefix_to_edges:
            self.prefix_to_edges[prefix].sort()
        self.total_edges = sum(self.edge_counts.values())
        self.required_counts = item["counts"]
        self.forbidden = set(item["forbidden_trigrams"])
        self.anchors = parse_anchor_clues(item)
        self.anchor_slots = defaultdict(list)
        for idx, anchor in enumerate(self.anchors):
            for pos in anchor.positions:
                self.anchor_slots[pos].append(idx)

    def _counts_ok(self, text: str) -> bool:
        used = Counter(text)
        for ch, need in self.required_counts.items():
            if used[ch] > need:
                return False
        remaining_slots = self.length - len(text)
        min_needed = sum(
            max(0, need - used.get(ch, 0)) for ch, need in self.required_counts.items()
        )
        return min_needed <= remaining_slots

    def _forbidden_ok(self, text: str) -> bool:
        if len(text) < 3:
            return True
        return text[-3:] not in self.forbidden

    def _anchors_ok(self, text: str) -> bool:
        for anchor in self.anchors:
            seen = [text[pos] for pos in anchor.positions if pos < len(text)]
            if not seen:
                continue
            need = Counter(anchor.letters)
            used = Counter(seen)
            if any(used[ch] > need[ch] for ch in used):
                return False
            unresolved = len([pos for pos in anchor.positions if pos >= len(text)])
            still_needed = sum(max(0, need[ch] - used[ch]) for ch in need)
            if still_needed > unresolved:
                return False
        return True

    def _remaining_letters_ok(self, edge_counts: Counter, text: str) -> bool:
        if len(text) >= self.length:
            return True
        available = Counter()
        for edge, count in edge_counts.items():
            if count:
                available[edge[-1]] += count
        used = Counter(text)
        need_remaining = {
            ch: self.required_counts[ch] - used.get(ch, 0) for ch in self.required_counts
        }
        return all(available[ch] >= need_remaining[ch] for ch in need_remaining)

    def _can_finish_from_prefix(self, edge_counts: Counter, suffix: str) -> bool:
        if sum(edge_counts.values()) == 0:
            return True
        stack = [suffix]
        seen = {suffix}
        while stack:
            node = stack.pop()
            for edge, count in edge_counts.items():
                if count and edge[:-1] == node:
                    nxt = edge[1:]
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
        for edge, count in edge_counts.items():
            if count and edge[:-1] not in seen:
                return False
        return True

    def solve(self, max_solutions: int = 2) -> List[str]:
        solutions: List[str] = []
        start_edges = sorted(self.edge_counts)
        for start in start_edges:
            remaining = self.edge_counts.copy()
            remaining[start] -= 1
            if remaining[start] == 0:
                del remaining[start]
            text = start
            if not self._counts_ok(text) or not self._anchors_ok(text) or not self._forbidden_ok(text):
                continue
            self._search(text, remaining, solutions, max_solutions)
            if len(solutions) >= max_solutions:
                break
        return solutions

    def _search(
        self,
        text: str,
        edge_counts: Counter,
        solutions: List[str],
        max_solutions: int,
    ) -> None:
        if len(solutions) >= max_solutions:
            return
        if len(text) == self.length:
            if not edge_counts and solution_holds(self.item, text):
                solutions.append(text)
            return
        suffix = text[-(self.k - 1) :]
        if not self._can_finish_from_prefix(edge_counts, suffix):
            return
        if not self._remaining_letters_ok(edge_counts, text):
            return
        for edge in self.prefix_to_edges.get(suffix, []):
            if edge_counts.get(edge, 0) == 0:
                continue
            next_char = edge[-1]
            candidate = text + next_char
            if not self._counts_ok(candidate):
                continue
            if not self._forbidden_ok(candidate):
                continue
            if not self._anchors_ok(candidate):
                continue
            next_counts = edge_counts.copy()
            next_counts[edge] -= 1
            if next_counts[edge] == 0:
                del next_counts[edge]
            self._search(candidate, next_counts, solutions, max_solutions)
            if len(solutions) >= max_solutions:
                return


def random_target(rng: random.Random, length: int = DEFAULT_LENGTH) -> str:
    while True:
        text = "".join(rng.choice(ALPHABET) for _ in range(length))
        counts = Counter(text)
        if min(counts.values()) >= 2 and len(trigram_set(text)) >= length - 4:
            return text


def choose_forbidden_trigrams(target: str, rng: random.Random, count: int = 5) -> List[str]:
    present = trigram_set(target)
    universe = [a + b + c for a in ALPHABET for b in ALPHABET for c in ALPHABET]
    candidates = [tri for tri in universe if tri not in present]
    rng.shuffle(candidates)
    return sorted(candidates[:count])


def candidate_anchor_pool(target: str) -> List[AnchorClue]:
    anchors = []
    length = len(target)
    for start in range(0, length - 2):
        positions = (start, start + 1, start + 2)
        letters = "".join(target[pos] for pos in positions)
        anchors.append(AnchorClue(positions, letters))
    spaced = [
        (0, 5, 10),
        (1, 6, 11),
        (2, 7, 12),
        (3, 8, 13),
        (4, 9, 14),
        (5, 10, 15),
        (0, 7, 15),
        (2, 9, 14),
        (1, 8, 12),
    ]
    for triple in spaced:
        if max(triple) < length:
            letters = "".join(target[pos] for pos in triple)
            anchors.append(AnchorClue(triple, letters))
    dedup = []
    seen = set()
    for anchor in anchors:
        key = (anchor.positions, "".join(sorted(anchor.letters)))
        if key not in seen:
            seen.add(key)
            dedup.append(anchor)
    return dedup


def build_unique_item(item_id: str, seed: int, length: int = DEFAULT_LENGTH) -> Tuple[Dict, str]:
    rng = random.Random(seed)
    for attempt in range(1, 500):
        target = random_target(rng, length)
        forbidden = choose_forbidden_trigrams(target, rng)
        pool = candidate_anchor_pool(target)
        rng.shuffle(pool)
        anchors: List[AnchorClue] = []
        item = item_from_parts(item_id, target, forbidden, anchors)
        solver = AssemblySolver(item)
        solutions = solver.solve(max_solutions=3)
        if len(solutions) == 1 and solutions[0] == target and greedy_baseline_answer(item) != target:
            return item, target
        for anchor in pool:
            anchors.append(anchor)
            item = item_from_parts(item_id, target, forbidden, anchors)
            solver = AssemblySolver(item)
            solutions = solver.solve(max_solutions=3)
            if len(solutions) == 1 and solutions[0] == target and greedy_baseline_answer(item) != target:
                return item, target
    raise RuntimeError(f"Failed to build unique item {item_id} after many attempts")


def write_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def exact_match_score(gold_rows: Sequence[Dict], pred_rows: Sequence[Dict]) -> Dict:
    gold = {row["id"]: row["answer"] for row in gold_rows}
    preds = {row["id"]: row["answer"] for row in pred_rows}
    missing = sorted(set(gold) - set(preds))
    extra = sorted(set(preds) - set(gold))
    correct = sum(1 for item_id, answer in gold.items() if preds.get(item_id) == answer)
    total = len(gold)
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "missing_ids": missing,
        "extra_ids": extra,
    }


def greedy_baseline_answer(item: Dict) -> str:
    edge_counts = Counter(item["spectrum"])
    starts = sorted(edge_counts)
    best = None
    for start in starts:
        remaining = edge_counts.copy()
        remaining[start] -= 1
        if remaining[start] == 0:
            del remaining[start]
        text = start
        while len(text) < item["length"]:
            suffix = text[-(item["k"] - 1) :]
            options = [edge for edge in sorted(remaining) if edge[:-1] == suffix]
            if not options:
                break
            chosen = options[0]
            text += chosen[-1]
            remaining[chosen] -= 1
            if remaining[chosen] == 0:
                del remaining[chosen]
        if len(text) == item["length"] and (best is None or text < best):
            best = text
    return best or starts[0]


def cli_sample(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args(args=args)

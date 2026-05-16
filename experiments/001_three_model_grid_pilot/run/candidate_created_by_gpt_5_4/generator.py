#!/usr/bin/env python3
import argparse
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


CELL = 16
GRID_W = 28
GRID_H = 28
MARGIN = 12
IMG_W = GRID_W * CELL + MARGIN * 2
IMG_H = GRID_H * CELL + MARGIN * 2
BG = (246, 244, 238)
BODY = (203, 197, 188)
OUTLINE = (34, 34, 34)
PROBE = (208, 42, 42)
BADGE_COLORS = {
    "A": (225, 92, 87),
    "B": (81, 150, 94),
    "C": (74, 118, 201),
    "D": (206, 149, 58),
}


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    def cells(self) -> Sequence[Tuple[int, int]]:
        for y in range(self.y0, self.y1):
            for x in range(self.x0, self.x1):
                yield (x, y)


@dataclass
class Piece:
    label: str
    rects: List[Rect]
    badge: Tuple[int, int]


def rect(x0: int, y0: int, x1: int, y1: int) -> Rect:
    return Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def add_rect_cells(cells: set, r: Rect) -> None:
    for cell in r.cells():
        cells.add(cell)


def piece_cells(piece: Piece) -> set:
    cells = set()
    for r in piece.rects:
        add_rect_cells(cells, r)
    return cells


def piece_is_in_bounds(piece: Piece) -> bool:
    for r in piece.rects:
        if r.x0 < 0 or r.y0 < 0 or r.x1 > GRID_W or r.y1 > GRID_H:
            return False
    bx, by = piece.badge
    return 0 <= bx < GRID_W and 0 <= by < GRID_H


def make_piece(label: str, rng: random.Random) -> Piece:
    for _ in range(200):
        orientation = rng.choice(["h", "v"])
        if orientation == "h":
            width = rng.randint(11, 15)
            height = rng.randint(3, 4)
            x0 = rng.randint(4, GRID_W - width - 4)
            y0 = rng.randint(8, GRID_H - height - 8)
            main = rect(x0, y0, x0 + width, y0 + height)
            tab_w = rng.randint(3, 4)
            tab_h = rng.randint(6, min(8, y0 + 1, GRID_H - (y0 + height) + 1))
            tab_x = rng.randint(x0 + 1, x0 + width - tab_w - 1)
            if rng.random() < 0.5:
                tab = rect(tab_x, y0 - tab_h + 1, tab_x + tab_w, y0 + 1)
                badge = (tab_x + tab_w // 2, y0 - tab_h + 2)
            else:
                tab = rect(tab_x, y0 + height - 1, tab_x + tab_w, y0 + height + tab_h - 1)
                badge = (tab_x + tab_w // 2, y0 + height + tab_h - 2)
            stub_w = rng.randint(4, 5)
            if rng.random() < 0.5:
                stub = rect(x0 - stub_w + 1, y0 + 1, x0 + 1, y0 + height - 1)
            else:
                stub = rect(x0 + width - 1, y0 + 1, x0 + width + stub_w - 1, y0 + height - 1)
            piece = Piece(label=label, rects=[main, tab, stub], badge=badge)
        else:
            width = rng.randint(3, 4)
            height = rng.randint(11, 15)
            x0 = rng.randint(8, GRID_W - width - 8)
            y0 = rng.randint(4, GRID_H - height - 4)
            main = rect(x0, y0, x0 + width, y0 + height)
            tab_w = rng.randint(6, min(8, x0 + 1, GRID_W - (x0 + width) + 1))
            tab_h = rng.randint(3, 4)
            tab_y = rng.randint(y0 + 1, y0 + height - tab_h - 1)
            if rng.random() < 0.5:
                tab = rect(x0 - tab_w + 1, tab_y, x0 + 1, tab_y + tab_h)
                badge = (x0 - tab_w + 2, tab_y + tab_h // 2)
            else:
                tab = rect(x0 + width - 1, tab_y, x0 + width + tab_w - 1, tab_y + tab_h)
                badge = (x0 + width + tab_w - 2, tab_y + tab_h // 2)
            stub_h = rng.randint(4, 5)
            if rng.random() < 0.5:
                stub = rect(x0 + 1, y0 - stub_h + 1, x0 + width - 1, y0 + 1)
            else:
                stub = rect(x0 + 1, y0 + height - 1, x0 + width - 1, y0 + height + stub_h - 1)
            piece = Piece(label=label, rects=[main, tab, stub], badge=badge)

        if piece_is_in_bounds(piece):
            return piece
    raise RuntimeError(f"Failed to sample an in-bounds piece for {label}")


def render_piece_mask(piece: Piece) -> set:
    return piece_cells(piece)


def visible_map(pieces: Sequence[Piece]) -> Tuple[Dict[Tuple[int, int], str], Dict[str, set]]:
    owner = {}
    visible_by_piece = {piece.label: set() for piece in pieces}
    for piece in pieces:
        for cell in render_piece_mask(piece):
            owner[cell] = piece.label
    for cell, label in owner.items():
        visible_by_piece[label].add(cell)
    return owner, visible_by_piece


def neighbors(cell: Tuple[int, int]) -> Sequence[Tuple[int, int]]:
    x, y = cell
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def component_sizes(cells: set) -> List[int]:
    remaining = set(cells)
    sizes = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        size = 1
        while stack:
            cur = stack.pop()
            for nxt in neighbors(cur):
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def choose_probe(pieces: Sequence[Piece], owner: Dict[Tuple[int, int], str], visible_by_piece: Dict[str, set], rng: random.Random):
    candidates = []
    piece_map = {piece.label: piece for piece in pieces}
    for label, vis_cells in visible_by_piece.items():
        full_cells = piece_cells(piece_map[label])
        hidden_cells = full_cells - vis_cells
        if len(hidden_cells) < 25:
            continue
        comp_sizes = component_sizes(vis_cells)
        if len(comp_sizes) < 2 or comp_sizes[1] < 8:
            continue
        for cell in vis_cells:
            x, y = cell
            if x < 2 or y < 2 or x >= GRID_W - 2 or y >= GRID_H - 2:
                continue
            if abs(x - piece_map[label].badge[0]) + abs(y - piece_map[label].badge[1]) < 8:
                continue
            same_neighbors = sum(1 for n in neighbors(cell) if owner.get(n) == label)
            if same_neighbors < 2:
                continue
            candidates.append((label, cell, len(hidden_cells), comp_sizes[1]))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[2], item[3]), reverse=True)
    top = candidates[: min(8, len(candidates))]
    label, cell, _, _ = rng.choice(top)
    return label, cell


def draw_rect(img: List[List[Tuple[int, int, int]]], r: Rect, color: Tuple[int, int, int]) -> None:
    px0 = MARGIN + r.x0 * CELL
    py0 = MARGIN + r.y0 * CELL
    px1 = MARGIN + r.x1 * CELL
    py1 = MARGIN + r.y1 * CELL
    for y in range(py0, py1):
        row = img[y]
        for x in range(px0, px1):
            row[x] = color


def draw_outline(img: List[List[Tuple[int, int, int]]], owner: Dict[Tuple[int, int], str]) -> None:
    for (x, y), label in owner.items():
        px0 = MARGIN + x * CELL
        py0 = MARGIN + y * CELL
        px1 = px0 + CELL
        py1 = py0 + CELL
        if owner.get((x, y - 1)) != label:
            for py in range(py0, py0 + 2):
                for px in range(px0, px1):
                    img[py][px] = OUTLINE
        if owner.get((x, y + 1)) != label:
            for py in range(py1 - 2, py1):
                for px in range(px0, px1):
                    img[py][px] = OUTLINE
        if owner.get((x - 1, y)) != label:
            for px in range(px0, px0 + 2):
                for py in range(py0, py1):
                    img[py][px] = OUTLINE
        if owner.get((x + 1, y)) != label:
            for px in range(px1 - 2, px1):
                for py in range(py0, py1):
                    img[py][px] = OUTLINE


LETTER_MAP = {
    "A": ["0110", "1001", "1111", "1001", "1001"],
    "B": ["1110", "1001", "1110", "1001", "1110"],
    "C": ["0111", "1000", "1000", "1000", "0111"],
    "D": ["1110", "1001", "1001", "1001", "1110"],
}


def draw_badge(img: List[List[Tuple[int, int, int]]], badge_cell: Tuple[int, int], label: str) -> None:
    cx = MARGIN + badge_cell[0] * CELL + CELL // 2
    cy = MARGIN + badge_cell[1] * CELL + CELL // 2
    radius = CELL // 2 + 4
    color = BADGE_COLORS[label]
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if 0 <= x < IMG_W and 0 <= y < IMG_H:
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                    img[y][x] = color
    pattern = LETTER_MAP[label]
    scale = 3
    start_x = cx - (len(pattern[0]) * scale) // 2
    start_y = cy - (len(pattern) * scale) // 2
    for row_i, row in enumerate(pattern):
        for col_i, bit in enumerate(row):
            if bit == "1":
                for dy in range(scale):
                    for dx in range(scale):
                        px = start_x + col_i * scale + dx
                        py = start_y + row_i * scale + dy
                        if 0 <= px < IMG_W and 0 <= py < IMG_H:
                            img[py][px] = (255, 255, 255)


def draw_probe(img: List[List[Tuple[int, int, int]]], cell: Tuple[int, int]) -> None:
    cx = MARGIN + cell[0] * CELL + CELL // 2
    cy = MARGIN + cell[1] * CELL + CELL // 2
    for y in range(cy - 6, cy + 7):
        for x in range(cx - 6, cx + 7):
            if 0 <= x < IMG_W and 0 <= y < IMG_H and (x - cx) ** 2 + (y - cy) ** 2 <= 24:
                img[y][x] = PROBE
    for d in range(-9, 10):
        if 0 <= cx + d < IMG_W:
            img[cy][cx + d] = (255, 255, 255)
        if 0 <= cy + d < IMG_H:
            img[cy + d][cx] = (255, 255, 255)


def write_ppm(path: Path, img: List[List[Tuple[int, int, int]]]) -> None:
    with path.open("w", encoding="ascii") as f:
        f.write(f"P3\n{IMG_W} {IMG_H}\n255\n")
        for row in img:
            f.write(" ".join(f"{r} {g} {b}" for (r, g, b) in row))
            f.write("\n")


def render_image(pieces: Sequence[Piece], probe: Tuple[int, int], out_path: Path) -> None:
    img = [[BG for _ in range(IMG_W)] for _ in range(IMG_H)]
    for piece in pieces:
        for r in piece.rects:
            draw_rect(img, r, BODY)
    owner, _ = visible_map(pieces)
    draw_outline(img, owner)
    for piece in pieces:
        draw_badge(img, piece.badge, piece.label)
    draw_probe(img, probe)
    write_ppm(out_path, img)


def make_item(index: int, seed: int, images_dir: Path) -> Dict[str, str]:
    rng = random.Random(seed + index * 1009)
    for _ in range(500):
        labels = ["A", "B", "C", "D"]
        rng.shuffle(labels)
        pieces = [make_piece(label, rng) for label in labels]
        owner, visible_by_piece = visible_map(pieces)
        probe_pick = choose_probe(pieces, owner, visible_by_piece, rng)
        if probe_pick is None:
            continue
        answer, probe = probe_pick
        image_name = f"item_{index:03d}.ppm"
        render_image(pieces, probe, images_dir / image_name)
        return {
            "id": f"tile_provenance_{index:03d}",
            "answer": answer,
            "image": f"images/{image_name}",
            "prompt": (
                "The four cardboard pieces all share the same surface texture. "
                "Each piece is identified only by its colored badge near one exposed tab. "
                "A red crosshair marks a visible patch of one piece. Which badge label owns "
                "the surface exactly under the crosshair? Answer with a single letter: A, B, C, or D."
            ),
        }
    raise RuntimeError(f"Failed to generate a valid item for index {index}")


def write_jsonl(path: Path, rows: Sequence[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def write_solver_manifest(path: Path, item_count: int) -> None:
    manifest = {
        "benchmark_name": "occluded_tile_provenance",
        "version": "1.0.0",
        "item_count": item_count,
        "task_type": "visual_reasoning",
        "answer_format": {"type": "string", "allowed_values": ["A", "B", "C", "D"]},
        "files": {
            "items": "items_private_sample.jsonl",
            "readme": "README.md",
            "images_dir": "images",
        },
        "prohibited_contents": [
            "gold answers",
            "hidden generation seeds",
            "source geometry",
            "occlusion traces",
            "solution labels",
        ],
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    out_dir = args.out_dir
    solver_dir = out_dir / "solver_bundle"
    images_dir = solver_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    public_rows = []
    gold_rows = []
    for index in range(args.sample_count):
        item = make_item(index=index, seed=args.seed, images_dir=images_dir)
        public_rows.append({
            "id": item["id"],
            "image": item["image"],
            "prompt": item["prompt"],
        })
        gold_rows.append({"id": item["id"], "answer": item["answer"]})

    write_jsonl(out_dir / "gold_private_sample.jsonl", gold_rows)
    write_jsonl(solver_dir / "items_private_sample.jsonl", public_rows)
    write_solver_manifest(solver_dir / "SOLVER_MANIFEST.json", args.sample_count)


if __name__ == "__main__":
    main()

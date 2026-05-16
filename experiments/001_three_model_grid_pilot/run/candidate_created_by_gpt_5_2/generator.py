#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


CANONICAL_LABEL_SETS = [
    list("ABCDE"),
    list("PQRST"),
    list("FGHJK"),
    list("LMNXY"),
    list("UVWYZ"),
]


@dataclass(frozen=True)
class Segment:
    label: str
    t: float
    center_xy: Tuple[float, float]
    angle_rad: float


def _mkdir_p(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _rand_unit(rng: random.Random) -> float:
    # Avoid exact 0/1 edges for stability in geometric sampling.
    return (rng.random() * 0.999998) + 0.000001


def _polyline_total_length(points: Sequence[Tuple[float, float]]) -> float:
    total = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _sample_along_polyline(
    points: Sequence[Tuple[float, float]], s: float
) -> Tuple[Tuple[float, float], float]:
    """
    Sample a point and tangent angle along the polyline at arclength fraction s in [0,1].
    Returns ((x,y), angle_rad).
    """
    total = _polyline_total_length(points)
    target = s * total
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if acc + seg >= target:
            if seg == 0:
                return (x0, y0), 0.0
            u = (target - acc) / seg
            x = x0 + u * (x1 - x0)
            y = y0 + u * (y1 - y0)
            ang = math.atan2(y1 - y0, x1 - x0)
            return (x, y), ang
        acc += seg
    # Fallback to end.
    (x0, y0), (x1, y1) = points[-2], points[-1]
    return (x1, y1), math.atan2(y1 - y0, x1 - x0)


def _make_fold_polyline(rng: random.Random, w: int, h: int) -> List[Tuple[float, float]]:
    """
    Create a long folded strip centerline as a polyline that meanders and folds back.
    Deterministic given rng.
    """
    margin = 60
    xmin, xmax = margin, w - margin
    ymin, ymax = margin, h - margin

    num_points = rng.randint(11, 15)
    points: List[Tuple[float, float]] = []
    x = rng.uniform(xmin, xmax)
    y = rng.uniform(ymin, ymax)
    points.append((x, y))

    # Alternate large turns to force folds; keep it inside bounds.
    heading = rng.uniform(0, 2 * math.pi)
    for i in range(1, num_points):
        turn = rng.uniform(0.9, 1.6) * (1 if i % 2 == 0 else -1)
        heading += turn
        step = rng.uniform(80, 120)
        x = x + step * math.cos(heading)
        y = y + step * math.sin(heading)
        x = min(max(x, xmin), xmax)
        y = min(max(y, ymin), ymax)
        points.append((x, y))

    # Ensure endpoints are well separated (to reduce trivial ordering).
    if math.hypot(points[-1][0] - points[0][0], points[-1][1] - points[0][1]) < 260:
        points[-1] = (xmax if points[0][0] < (w / 2) else xmin, points[-1][1])
    return points


def _draw_textured_strip(
    img: Image.Image,
    points: Sequence[Tuple[float, float]],
    strip_width: int,
    rng: random.Random,
) -> None:
    """
    Draw a strip with a high-frequency, piecewise-unique texture that is continuous along arclength.
    """
    draw = ImageDraw.Draw(img)

    # Base strip.
    base = (242, 238, 230)
    edge = (70, 70, 70)
    draw.line(points, fill=base, width=strip_width, joint="curve")
    draw.line(points, fill=edge, width=max(1, strip_width // 8), joint="curve")

    # Texture: repeated "barcode" ticks + occasional unique motifs derived from arclength bucket id.
    # We render along the polyline by sampling points at fixed arclength steps.
    steps = int(_polyline_total_length(points) // 6)
    steps = max(250, min(900, steps))
    for i in range(steps + 1):
        s = i / steps
        (x, y), ang = _sample_along_polyline(points, s)
        # Normal vector.
        nx = -math.sin(ang)
        ny = math.cos(ang)
        # Tick length varies with a deterministic pseudo-code tied to i.
        code = (i * 2654435761) & 0xFFFFFFFF
        short = 0.18 * strip_width
        long = 0.42 * strip_width
        tick_len = long if (code >> 29) & 1 else short
        tick_off = (strip_width * 0.18) * (1 if (code >> 27) & 1 else -1)
        x0 = x + nx * tick_off
        y0 = y + ny * tick_off
        x1 = x0 + nx * (tick_len if tick_off >= 0 else -tick_len)
        y1 = y0 + ny * (tick_len if tick_off >= 0 else -tick_len)
        tick_col = (115, 108, 98) if (code >> 23) & 1 else (155, 148, 138)
        draw.line([(x0, y0), (x1, y1)], fill=tick_col, width=2)

        # Every N ticks, draw a tiny motif near centerline that is unique per bucket.
        if i % 37 == 0:
            bucket = i // 37
            motif = bucket % 7
            cx = x - nx * (strip_width * 0.06)
            cy = y - ny * (strip_width * 0.06)
            r = 4
            if motif == 0:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(90, 85, 78), width=2)
            elif motif == 1:
                draw.polygon([(cx, cy - r), (cx + r, cy + r), (cx - r, cy + r)], outline=(90, 85, 78))
            elif motif == 2:
                draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=(90, 85, 78), width=2)
            elif motif == 3:
                draw.line([(cx - r, cy), (cx + r, cy)], fill=(90, 85, 78), width=2)
                draw.line([(cx, cy - r), (cx, cy + r)], fill=(90, 85, 78), width=2)
            elif motif == 4:
                draw.arc([cx - r, cy - r, cx + r, cy + r], start=0, end=240, fill=(90, 85, 78), width=2)
            elif motif == 5:
                draw.polygon(
                    [(cx - r, cy - r), (cx + r, cy - r), (cx, cy + r)],
                    outline=(90, 85, 78),
                )
            else:
                draw.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill=(90, 85, 78), width=2)

    # Add slight paper grain (tiny dots), deterministic.
    for _ in range(800):
        x = rng.uniform(0, img.size[0])
        y = rng.uniform(0, img.size[1])
        c = rng.randint(210, 235)
        draw.point((x, y), fill=(c, c - 2, c - 6))


def _draw_occluders(
    img: Image.Image, rng: random.Random, count: int, avoid: Sequence[Tuple[float, float]]
) -> None:
    """
    Draw opaque occluder rectangles that block continuity cues, while avoiding label centers.
    """
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(count):
        cw = rng.randint(80, 140)
        ch = rng.randint(55, 95)
        x0 = rng.randint(15, w - 15 - cw)
        y0 = rng.randint(15, h - 15 - ch)
        x1 = x0 + cw
        y1 = y0 + ch
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        if any((abs(cx - ax) < 55 and abs(cy - ay) < 45) for ax, ay in avoid):
            continue
        fill = (rng.randint(20, 45), rng.randint(20, 45), rng.randint(20, 45))
        draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=fill)
        # Fake highlight edge to mimic "shadow/contact" but not encode depth.
        draw.line([(x0 + 6, y0 + 6), (x1 - 6, y0 + 6)], fill=(70, 70, 70), width=2)


def _pick_segments(
    rng: random.Random,
    points: Sequence[Tuple[float, float]],
    labels: Sequence[str],
) -> List[Segment]:
    # Choose well-spaced arclength positions so labels span the strip.
    ts: List[float] = []
    while len(ts) < len(labels):
        t = _rand_unit(rng)
        if all(abs(t - u) > 0.12 for u in ts):
            ts.append(t)
    ts.sort()
    # Then permute label assignment to break easy inference about t monotonicity vs label order.
    shuffled_labels = list(labels)
    rng.shuffle(shuffled_labels)
    segs: List[Segment] = []
    for label, t in zip(shuffled_labels, ts):
        (x, y), ang = _sample_along_polyline(points, t)
        segs.append(Segment(label=label, t=t, center_xy=(x, y), angle_rad=ang))
    return segs


def _try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Keep deterministic by preferring a bundled-ish font name; fall back to default.
    for name in ["DejaVuSans.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_labels_and_endcaps(
    img: Image.Image,
    segments: Sequence[Segment],
    points: Sequence[Tuple[float, float]],
    strip_width: int,
) -> None:
    draw = ImageDraw.Draw(img)
    font = _try_load_font(30)
    # Label patches.
    for seg in segments:
        x, y = seg.center_xy
        patch_w = 52
        patch_h = 38
        x0 = x - patch_w / 2
        y0 = y - patch_h / 2
        x1 = x + patch_w / 2
        y1 = y + patch_h / 2
        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=(250, 250, 250), outline=(40, 40, 40), width=2)
        tw, th = draw.textbbox((0, 0), seg.label, font=font)[2:]
        draw.text((x - tw / 2, y - th / 2 - 1), seg.label, font=font, fill=(10, 10, 10))

    # START / END markers near the polyline endpoints.
    start = points[0]
    end = points[-1]
    r = strip_width // 2 + 8
    draw.ellipse([start[0] - r, start[1] - r, start[0] + r, start[1] + r], outline=(0, 130, 40), width=5)
    draw.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], outline=(160, 0, 40), width=5)
    f2 = _try_load_font(20)
    draw.text((start[0] + r + 6, start[1] - 12), "START", font=f2, fill=(0, 130, 40))
    draw.text((end[0] + r + 6, end[1] - 12), "END", font=f2, fill=(160, 0, 40))


def _render_item_image(rng: random.Random, labels: Sequence[str]) -> Tuple[Image.Image, str]:
    w, h = 640, 640
    img = Image.new("RGB", (w, h), (248, 248, 248))

    points = _make_fold_polyline(rng, w, h)
    strip_width = rng.randint(36, 46)

    segments = _pick_segments(rng, points, labels)
    _draw_textured_strip(img, points, strip_width, rng)
    _draw_labels_and_endcaps(img, segments, points, strip_width)

    # Occluders last: they can cover crossings and hide joins, making 2D proximity unreliable.
    avoid = [s.center_xy for s in segments] + [points[0], points[-1]]
    _draw_occluders(img, rng, count=rng.randint(5, 8), avoid=avoid)

    # Answer: labels sorted by true arclength order from START to END (t ascending).
    ans = "".join([s.label for s in sorted(segments, key=lambda z: z.t)])
    return img, ans


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    _mkdir_p(out_dir)

    solver_dir = out_dir / "solver_bundle"
    items_dir = solver_dir / "items"
    _mkdir_p(items_dir)

    rng = random.Random(args.seed)
    gold_rows: List[dict] = []
    item_rows: List[dict] = []

    for i in range(args.sample_count):
        labels = CANONICAL_LABEL_SETS[i % len(CANONICAL_LABEL_SETS)]
        local_rng = random.Random(rng.randint(0, 2**31 - 1))
        img, ans = _render_item_image(local_rng, labels)
        item_id = f"fso_{args.seed}_{i:03d}"
        rel_path = Path("items") / f"{item_id}.png"
        img.save(items_dir / f"{item_id}.png", format="PNG", optimize=True)

        gold_rows.append({"id": item_id, "answer": ans})
        item_rows.append(
            {
                "id": item_id,
                "path": str(rel_path).replace(os.sep, "/"),
                "prompt": (
                    "You are given a single image of a folded paper strip. Several visible segments on the strip are labeled "
                    f"with letters. The strip has a START marker (green ring) and an END marker (red ring). "
                    "Determine the true order of the labeled segments encountered when walking along the strip from START to END. "
                    "Return the labels as a single string with no separators (e.g. ABCDE). Exact match required."
                ),
            }
        )

    # Write private gold.
    _write_jsonl(out_dir / "gold_private_sample.jsonl", gold_rows)
    # Write solver items (no answers).
    _write_jsonl(solver_dir / "items_private_sample.jsonl", item_rows)

    # Solver manifest.
    manifest = {
        "benchmark_id": "folded_strip_order_v1",
        "version": "1.0.0",
        "items_file": "items_private_sample.jsonl",
        "item_schema": {"id": "string", "path": "string (relative to solver_bundle)", "prompt": "string"},
        "answer_schema": {"id": "string", "answer": "string"},
        "constraints": [
            "Predictions must be a JSONL with one object per line.",
            "Each predictions row must contain exactly: id, answer.",
            "Answer must be a permutation of the labels present in the image (no separators).",
        ],
    }
    (solver_dir / "SOLVER_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Solver readme.
    solver_readme = """# Folded Strip Order (FSO) v1 — Solver Packet

## Task
Each item is a PNG image in `items/`. The image shows a single folded paper strip with:
- A **START** marker (green ring)
- An **END** marker (red ring)
- Several labeled visible segments on the strip (letters in white rounded boxes)

Your job: infer the **true order** of the labeled segments encountered when traversing the strip from START to END.

## Output format
Write `predictions.jsonl` with one JSON object per line:
```json
{"id":"<item id>","answer":"<label string>"}
```
Where `answer` is the labels as a single string with no separators (e.g. `ABCDE`).

## Important notes
- The 2D left-to-right or nearest-neighbor adjacency in the image is *not* reliable: folds, crossings, and occluders are intentional.
- The strip texture is continuous along the strip and provides the auditable cue for adjacency across folds.
"""
    (solver_dir / "README.md").write_text(solver_readme, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


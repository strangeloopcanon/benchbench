#!/usr/bin/env python3
import argparse
import json
import math
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


LABELS = ["K", "L", "M", "N", "P", "Q"]
COLORS = {
    "K": (224, 74, 74),
    "L": (63, 142, 210),
    "M": (74, 166, 91),
    "N": (232, 178, 54),
    "P": (151, 91, 191),
    "Q": (47, 166, 164),
}


def font(size):
    for p in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def interp(points, t):
    if t <= 0:
        return points[0]
    if t >= 1:
        return points[-1]
    segs = len(points) - 1
    f = t * segs
    i = min(segs - 1, int(f))
    u = f - i
    x0, y0 = points[i]
    x1, y1 = points[i + 1]
    return (x0 * (1 - u) + x1 * u, y0 * (1 - u) + y1 * u)


def make_paths(rng):
    # Three mostly horizontal and three mostly vertical folded paper strips.
    ys = [120 + rng.randint(-12, 12), 246 + rng.randint(-12, 12), 374 + rng.randint(-12, 12)]
    xs = [124 + rng.randint(-12, 12), 252 + rng.randint(-12, 12), 382 + rng.randint(-12, 12)]
    paths = {}
    labels = LABELS[:]
    rng.shuffle(labels)
    for i, y in enumerate(ys):
        amp = rng.randint(18, 34)
        phase = rng.random() * math.tau
        pts = []
        for k in range(7):
            x = 50 + k * 72
            pts.append((x, y + math.sin(k * 1.15 + phase) * amp + rng.randint(-5, 5)))
        paths[labels[i]] = {"kind": "h", "pts": pts}
    for i, x in enumerate(xs):
        amp = rng.randint(18, 34)
        phase = rng.random() * math.tau
        pts = []
        for k in range(7):
            y = 50 + k * 72
            pts.append((x + math.cos(k * 1.1 + phase) * amp + rng.randint(-5, 5), y))
        paths[labels[i + 3]] = {"kind": "v", "pts": pts}
    return paths


def crossing_point(hpts, vpts):
    # With near-monotone H and V paths, a midpoint fixed-point iteration is stable
    # enough for drawing probe windows and for the private audit trace.
    x = sum(p[0] for p in vpts) / len(vpts)
    y = sum(p[1] for p in hpts) / len(hpts)
    for _ in range(8):
        tx = (x - hpts[0][0]) / (hpts[-1][0] - hpts[0][0])
        _, y = interp(hpts, tx)
        ty = (y - vpts[0][1]) / (vpts[-1][1] - vpts[0][1])
        x, _ = interp(vpts, ty)
    return (x, y)


def draw_strip(base, pts, color, label, decoy_rank):
    w = 34
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    shifted = [(x + 5, y + 6) for x, y in pts]
    sd.line(shifted, fill=(0, 0, 0, 80), width=w + 3, joint="curve")
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    base.alpha_composite(shadow)

    d = ImageDraw.Draw(base)
    d.line(pts, fill=color + (255,), width=w, joint="curve")
    d.line(pts, fill=(255, 255, 255, 90), width=3, joint="curve")
    d.line(pts, fill=(40, 40, 40, 70), width=w + 2, joint="curve")
    d.line(pts, fill=color + (255,), width=w - 2, joint="curve")

    f_big = font(23)
    f_small = font(16)
    for t in (0.08, 0.92):
        x, y = interp(pts, t)
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(255, 255, 255, 230), outline=(35, 35, 35, 180), width=2)
        d.text((x, y - 1), label, anchor="mm", font=f_big, fill=(20, 20, 20, 255))
    # Decoy rank chips: conspicuous, deterministic, and intentionally not the layer order.
    for t in (0.32, 0.68):
        x, y = interp(pts, t)
        d.rounded_rectangle((x - 13, y - 10, x + 13, y + 10), radius=4, fill=(255, 255, 255, 180))
        d.text((x, y), str(decoy_rank), anchor="mm", font=f_small, fill=(25, 25, 25, 255))


def make_item(item_id, rng, out_solver):
    paths = make_paths(rng)
    layer_order = LABELS[:]
    rng.shuffle(layer_order)
    decoy_order = layer_order[:]
    decoy_order.reverse()
    decoys = {lab: i + 1 for i, lab in enumerate(decoy_order)}

    img = Image.new("RGBA", (520, 520), (239, 237, 229, 255))
    d = ImageDraw.Draw(img)
    for x in range(20, 520, 40):
        d.line((x, 0, x, 520), fill=(210, 207, 198, 55), width=1)
    for y in range(20, 520, 40):
        d.line((0, y, 520, y), fill=(210, 207, 198, 55), width=1)

    for lab in layer_order:
        draw_strip(img, paths[lab]["pts"], COLORS[lab], lab, decoys[lab])

    crossings = []
    hs = [lab for lab, p in paths.items() if p["kind"] == "h"]
    vs = [lab for lab, p in paths.items() if p["kind"] == "v"]
    rank = {lab: i for i, lab in enumerate(layer_order)}
    for h in hs:
        for v in vs:
            x, y = crossing_point(paths[h]["pts"], paths[v]["pts"])
            if 70 < x < 450 and 70 < y < 450:
                top = h if rank[h] > rank[v] else v
                crossings.append({"pair": [h, v], "xy": [round(x, 1), round(y, 1)], "top": top})
    rng.shuffle(crossings)
    probes = crossings[:4]
    letters = ["A", "B", "C", "D"]
    f_probe = font(25)
    for letter, c in zip(letters, probes):
        x, y = c["xy"]
        d.ellipse((x - 25, y - 25, x + 25, y + 25), outline=(12, 12, 12, 255), width=4)
        d.rectangle((x - 35, y - 38, x - 10, y - 12), fill=(255, 255, 255, 235), outline=(20, 20, 20, 255), width=2)
        d.text((x - 22.5, y - 25), letter, anchor="mm", font=f_probe, fill=(0, 0, 0, 255))

    img_path = out_solver / "images" / f"{item_id}.png"
    img.convert("RGB").save(img_path)
    answer = "".join(c["top"] for c in probes)
    item = {
        "id": item_id,
        "image": f"images/{item_id}.png",
        "question": "For probe rings A, B, C, and D, read which labeled strip is visibly on top at the contact point. Answer with the four strip labels in A-to-D order, no spaces, e.g. KMPQ.",
    }
    gold = {"id": item_id, "answer": answer}
    trace = {"id": item_id, "layer_order_bottom_to_top": layer_order, "probes": probes}
    return item, gold, trace


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    solver = out / "solver_bundle"
    if solver.exists():
        shutil.rmtree(solver)
    (solver / "images").mkdir(parents=True)

    rng = random.Random(args.seed)
    items, gold, traces = [], [], []
    for i in range(args.sample_count):
        item_id = f"swt_{i+1:03d}"
        item, g, t = make_item(item_id, rng, solver)
        items.append(item)
        gold.append(g)
        traces.append(t)
    write_jsonl(solver / "items_private_sample.jsonl", items)
    write_jsonl(out / "gold_private_sample.jsonl", gold)
    write_jsonl(out / "private_traces.jsonl", traces)
    manifest = {
        "benchmark": "Shadow Weave Topology",
        "item_count": args.sample_count,
        "item_file": "items_private_sample.jsonl",
        "answer_format": "exactly four labels from KLMNPQ, one per probe A-D",
        "assets": "images/*.png",
    }
    (solver / "SOLVER_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (solver / "solver_packet.md").write_text(
        "# Shadow Weave Topology Solver Packet\n\n"
        "Each item is a raster image of six labeled paper strips. Four probe rings A-D mark strip contacts. "
        "Return the label of the strip visibly on top at the exact center of each ring, in A-to-D order with no separators. "
        "Ignore printed number chips; they are not depth ranks.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

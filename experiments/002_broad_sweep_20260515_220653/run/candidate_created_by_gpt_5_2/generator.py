#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class Rule:
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool
    has_slash: bool


def _split_gitignore_lines(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        # Preserve leading spaces (they are significant), but drop trailing \r.
        line = raw.rstrip("\r")
        lines.append(line)
    return lines


def parse_gitignore(gitignore_text: str) -> List[Rule]:
    rules: List[Rule] = []
    for line in _split_gitignore_lines(gitignore_text):
        if line == "" or line.lstrip(" ").startswith("#"):
            continue

        negated = False
        s = line
        if s.startswith("!"):
            negated = True
            s = s[1:]

        # Escape handling: "\#" and "\!" are literal; "\\" escapes backslash.
        if s.startswith("\\"):
            s = s[1:]

        directory_only = s.endswith("/")
        if directory_only:
            s = s[:-1]

        anchored = s.startswith("/")
        if anchored:
            s = s[1:]

        has_slash = "/" in s
        if s == "":
            continue

        rules.append(
            Rule(
                pattern=s,
                negated=negated,
                directory_only=directory_only,
                anchored=anchored,
                has_slash=has_slash,
            )
        )
    return rules


_re_special = re.compile(r"([.^$+{}()|\\])")


def _glob_to_regex(glob_pat: str) -> re.Pattern[str]:
    """
    Translate a restricted gitignore glob pattern into a regex.

    Supported:
    - "*" matches any string except "/"
    - "?" matches any single char except "/"
    - "**" matches any string including "/" (may be empty), but only as a whole
      path segment token or adjacent to "/" boundaries in our generator.
    - character classes like "[abc]" or "[a-z]"
    """
    i = 0
    out = ""
    while i < len(glob_pat):
        ch = glob_pat[i]
        if ch == "*":
            if i + 1 < len(glob_pat) and glob_pat[i + 1] == "*":
                out += ".*"
                i += 2
                continue
            out += "[^/]*"
            i += 1
            continue
        if ch == "?":
            out += "[^/]"
            i += 1
            continue
        if ch == "[":
            j = i + 1
            if j < len(glob_pat) and glob_pat[j] == "!":
                j += 1
            if j < len(glob_pat) and glob_pat[j] == "]":
                j += 1
            while j < len(glob_pat) and glob_pat[j] != "]":
                j += 1
            if j >= len(glob_pat):
                out += r"\["
                i += 1
                continue
            cls = glob_pat[i : j + 1]
            out += cls
            i = j + 1
            continue
        out += _re_special.sub(r"\\\1", ch)
        i += 1
    return re.compile(rf"^{out}$")


def _path_segments(path: str) -> List[str]:
    # Normalize: treat multiple slashes as a single slash; no leading "./".
    parts = [p for p in path.split("/") if p not in ("", ".")]
    return parts


def _match_rule_to_path(rule: Rule, path: str, is_dir: bool) -> bool:
    """
    Implement a well-defined subset of gitignore semantics.

    The matching policy:
    - All paths are relative and use "/" as separator.
    - If rule.directory_only is true, it can match a directory path or any file
      under that directory.
    - If rule.anchored is true, match is evaluated against the full path from
      repo root.
    - If rule.has_slash is false (pattern with no "/"), it can match any
      single path segment (basename semantics).
    - If rule.has_slash is true, it matches against the full path string.
    - Globbing uses the restricted translator above.
    """
    segments = _path_segments(path)
    norm_path = "/".join(segments)

    if norm_path == "":
        return False

    if rule.has_slash:
        target = norm_path if rule.anchored else norm_path
        rx = _glob_to_regex(rule.pattern)
        matched = rx.match(target) is not None
        if not matched:
            return False
        if rule.directory_only:
            # If path is dir: ok; if file: ok only if it's under that dir.
            if is_dir:
                return True
            # For directory-only patterns that include slashes, we treat a match
            # as applying to that directory prefix.
            return target.startswith(rule.pattern + "/")
        return True

    # Basename-style: match any segment.
    rx = _glob_to_regex(rule.pattern)
    for seg in segments:
        if rx.match(seg) is not None:
            if rule.directory_only:
                # Directory-only basename pattern matches any directory segment,
                # and therefore ignores the whole subtree.
                return True
            return True
    return False


def is_ignored(gitignore_text: str, path: str, is_dir: bool) -> bool:
    rules = parse_gitignore(gitignore_text)
    ignored = False
    for rule in rules:
        if _match_rule_to_path(rule, path=path, is_dir=is_dir):
            ignored = not rule.negated
    return ignored


def _stable_id(seed: int, idx: int, gitignore_text: str, paths: List[str]) -> str:
    h = hashlib.sha256()
    h.update(f"{seed}:{idx}\n".encode("utf-8"))
    h.update(gitignore_text.encode("utf-8"))
    h.update(b"\n")
    for p in paths:
        h.update(p.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()[:16]


_SEG_ATOMS = [
    "src",
    "lib",
    "test",
    "tests",
    "docs",
    "build",
    "dist",
    "bin",
    "obj",
    "tmp",
    "cache",
    "node_modules",
    "vendor",
    "assets",
    "data",
    "out",
]

_FILE_ATOMS = [
    "main.py",
    "app.js",
    "index.html",
    "README.md",
    "notes.txt",
    "a.out",
    "report.log",
    "image.png",
    "model.bin",
    "archive.tar",
    "archive.tar.gz",
    ".env",
]


def _rand_segment(rng: random.Random) -> str:
    base = rng.choice(_SEG_ATOMS)
    if rng.random() < 0.15:
        base = f"{base}{rng.randint(0, 9)}"
    if rng.random() < 0.05:
        base = base.replace("_", "-")
    return base


def _rand_path(rng: random.Random) -> Tuple[str, bool]:
    depth = rng.randint(1, 4)
    segs = [_rand_segment(rng) for _ in range(depth - 1)]
    if rng.random() < 0.30:
        # Directory path query.
        segs.append(_rand_segment(rng))
        return ("/".join(segs) + "/", True)
    leaf = rng.choice(_FILE_ATOMS)
    segs.append(leaf)
    return ("/".join(segs), False)


def _pattern_from_path(rng: random.Random, path: str) -> str:
    # Produce a pattern likely to match the path, with controlled complexity.
    s = path.rstrip("/")
    segs = s.split("/")
    choice = rng.random()
    if choice < 0.30:
        # Basename pattern
        leaf = segs[-1]
        if rng.random() < 0.35 and "." in leaf:
            ext = leaf.split(".")[-1]
            return f"*.{ext}"
        if rng.random() < 0.20:
            return leaf[0] + "?" + leaf[2:] if len(leaf) >= 3 else leaf
        return leaf
    if choice < 0.65:
        # Directory pattern
        d = segs[rng.randint(0, max(0, len(segs) - 2))]
        return f"{d}/"
    # Slash-containing pattern
    prefix_len = rng.randint(1, min(len(segs), 3))
    prefix = "/".join(segs[:prefix_len])
    if rng.random() < 0.25:
        prefix = f"{prefix}/**"
    if rng.random() < 0.25 and prefix.endswith("**"):
        prefix = f"{prefix}/*.log"
    return prefix


def _maybe_escape_prefix(rng: random.Random, pat: str) -> str:
    if pat and pat[0] in ("#", "!") and rng.random() < 0.7:
        return "\\" + pat
    return pat


def _make_gitignore(rng: random.Random, paths: List[Tuple[str, bool]]) -> str:
    lines: List[str] = []
    # Add some comments and blank lines
    if rng.random() < 0.6:
        lines.append("# IgnoreSense generated gitignore")
    if rng.random() < 0.3:
        lines.append("")

    # Choose a few patterns derived from paths, plus some distractors.
    chosen = rng.sample(paths, k=min(len(paths), rng.randint(4, 7)))
    patterns: List[str] = []
    for p, _is_dir in chosen:
        patterns.append(_pattern_from_path(rng, p))
    if rng.random() < 0.5:
        patterns.append("*.tmp")
    if rng.random() < 0.5:
        patterns.append("*.log")
    if rng.random() < 0.3:
        patterns.append("**/cache/**")

    rng.shuffle(patterns)

    # Add negations to create precedence traps.
    negations: List[str] = []
    for pat in patterns[:]:
        if rng.random() < 0.25 and not pat.startswith("!"):
            # Create a negation that partially overlaps
            if pat.endswith("/"):
                base = pat[:-1]
                neg = f"!{base}/keep.*"
            elif pat.startswith("*."):
                neg = f"!important{pat[1:]}"
            else:
                neg = f"!{pat}"
            negations.append(neg)

    # Build final lines with occasional anchoring.
    all_lines: List[str] = []
    for pat in patterns + negations:
        p = pat
        if not p.startswith(("!", "\\")) and rng.random() < 0.2:
            p = "/" + p
        p = _maybe_escape_prefix(rng, p)
        all_lines.append(p)

    # Ensure at least one negation and one directory-only pattern in most items.
    if not any(l.startswith("!") for l in all_lines):
        all_lines.append("!README.md")
    if not any(l.rstrip("\n").rstrip("\r").endswith("/") for l in all_lines if not l.startswith("#")):
        all_lines.append("build/")

    # Intermix some spacing and comment quirks
    out: List[str] = []
    for l in all_lines:
        if rng.random() < 0.15:
            out.append("  " + l)
        else:
            out.append(l)
        if rng.random() < 0.10:
            out.append("# trailing comment line")
    return "\n".join(out) + "\n"


def _compute_answer(gitignore_text: str, paths: List[Tuple[str, bool]]) -> str:
    ignored: List[str] = []
    for p, is_dir in paths:
        if is_ignored(gitignore_text, p.rstrip("/"), is_dir=is_dir):
            ignored.append(p)
    ignored_sorted = sorted(ignored)
    return json.dumps(ignored_sorted, ensure_ascii=False, separators=(",", ":"))


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    solver_dir = out_dir / "solver_bundle"
    solver_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    items_rows: List[dict] = []
    gold_rows: List[dict] = []

    for idx in range(args.sample_count):
        # Create candidate paths with some duplicates removed.
        raw_paths: List[Tuple[str, bool]] = []
        while len(raw_paths) < 12:
            p, is_dir = _rand_path(rng)
            if (p, is_dir) not in raw_paths:
                raw_paths.append((p, is_dir))

        gitignore_text = _make_gitignore(rng, raw_paths)
        paths_only = [p for p, _ in raw_paths]
        item_id = _stable_id(args.seed, idx, gitignore_text, paths_only)

        answer = _compute_answer(gitignore_text, raw_paths)
        items_rows.append(
            {
                "id": item_id,
                "gitignore": gitignore_text,
                "paths": paths_only,
            }
        )
        gold_rows.append({"id": item_id, "answer": answer})

    _write_jsonl(solver_dir / "items_private_sample.jsonl", items_rows)
    _write_jsonl(out_dir / "gold_private_sample.jsonl", gold_rows)

    manifest = {
        "benchmark_name": "IgnoreSense",
        "benchmark_version": "1.0.0",
        "items_file": "items_private_sample.jsonl",
        "answer_format": "JSON array of ignored paths sorted lexicographically; answer is serialized as a compact JSON string.",
        "notes": [
            "All tasks are self-contained; do not assume full gitignore semantics beyond what the packet describes.",
            "Paths use '/' separators and are relative (no leading './'). Directory paths end with '/'.",
        ],
    }
    (solver_dir / "SOLVER_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()


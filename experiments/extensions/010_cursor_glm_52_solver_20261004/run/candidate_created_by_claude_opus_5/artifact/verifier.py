#!/usr/bin/env python3
"""Verifier for the Consolidation Point benchmark.

Usage:
    python3 verifier.py --items solver_bundle/items_private_sample.jsonl \
                        --gold gold_private_sample.jsonl

Checks performed:

  Structure   - both files parse as JSONL objects; gold rows carry exactly
                `id` and `answer`; item rows carry the declared fields and
                nothing that could leak a solution.
  Alignment   - item ids and gold ids are the same set, in the same order,
                with no duplicates.
  Wellformed  - every gold answer is a canonical non-negative integer string.
  Assets      - every asset referenced by an item resolves inside the bundle,
                and no item references anything outside it.
  Leakage     - no bundle file is a private artefact by name; no bundle line
                carries an item id together with that item's gold answer; the
                bundle contains no forbidden keys or private file types.
  Provenance  - if the authored source corpus is present, gold answers, item
                questions and the asset bytes are cross-checked against it,
                so a transcription slip between corpus and package fails.
  Diagnostics - answer distribution, best constant-guess baseline, and an
                informational count of gold values that happen to appear as
                standalone numbers somewhere in the bundle.

Exit code 0 means PASS, 1 means FAIL, 2 means the verifier could not run.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")

GOLD_KEYS = {"id", "answer"}
ITEM_REQUIRED_KEYS = {"id", "case_ref", "assets", "question", "answer_format"}
ITEM_FORBIDDEN_KEYS = {
    "answer",
    "answers",
    "gold",
    "gold_answer",
    "label",
    "solution",
    "solutions",
    "target",
    "key",
    "rationale",
    "derivation",
    "working",
    "explanation",
}
FORBIDDEN_BUNDLE_NAME_PATTERNS = (
    re.compile(r"gold", re.IGNORECASE),
    re.compile(r"answer[_-]?key", re.IGNORECASE),
    re.compile(r"\bsolution", re.IGNORECASE),
    re.compile(r"generator\.py$", re.IGNORECASE),
    re.compile(r"verifier\.py$", re.IGNORECASE),
    re.compile(r"scorer\.py$", re.IGNORECASE),
    re.compile(r"validation_report", re.IGNORECASE),
    re.compile(r"failure_modes", re.IGNORECASE),
    re.compile(r"audit", re.IGNORECASE),
    re.compile(r"^corpus$", re.IGNORECASE),
)
CANONICAL_INT = re.compile(r"^(0|[1-9][0-9]*)$")
TEXT_SUFFIXES = (".md", ".json", ".jsonl", ".txt", ".csv", ".yaml", ".yml", ".py")


class Report(object):
    def __init__(self):
        self.failures = []
        self.warnings = []
        self.notes = []

    def fail(self, message):
        self.failures.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def note(self, message):
        self.notes.append(message)


def read_jsonl(path, label, report):
    rows = []
    if not os.path.isfile(path):
        report.fail("%s file not found: %s" % (label, path))
        return rows
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except ValueError as exc:
                report.fail("%s line %d is not valid JSON: %s" % (label, number, exc))
                continue
            if not isinstance(obj, dict):
                report.fail("%s line %d is not a JSON object" % (label, number))
                continue
            rows.append(obj)
    return rows


def check_gold_rows(gold_rows, report):
    ids = []
    answers = {}
    for index, row in enumerate(gold_rows, start=1):
        keys = set(row.keys())
        if keys != GOLD_KEYS:
            report.fail(
                "gold row %d must have exactly the keys id and answer, found %s"
                % (index, sorted(keys))
            )
            continue
        item_id = row["id"]
        answer = row["answer"]
        if not isinstance(item_id, str) or not item_id:
            report.fail("gold row %d has a non-string or empty id" % index)
            continue
        if not isinstance(answer, str):
            report.fail("gold row %d answer must be a string, found %r" % (index, answer))
            continue
        if not CANONICAL_INT.match(answer):
            report.fail(
                "gold row %d answer %r is not a canonical non-negative integer"
                % (index, answer)
            )
            continue
        if item_id in answers:
            report.fail("duplicate gold id: %s" % item_id)
            continue
        ids.append(item_id)
        answers[item_id] = answer
    return ids, answers


def check_item_rows(item_rows, bundle_dir, report):
    ids = []
    questions = {}
    seen = set()
    for index, row in enumerate(item_rows, start=1):
        keys = set(row.keys())
        missing = ITEM_REQUIRED_KEYS - keys
        if missing:
            report.fail("item row %d is missing required fields %s" % (index, sorted(missing)))
            continue
        leaked = keys & ITEM_FORBIDDEN_KEYS
        if leaked:
            report.fail("item row %d carries forbidden fields %s" % (index, sorted(leaked)))
            continue
        extra = keys - ITEM_REQUIRED_KEYS
        if extra:
            report.warn("item row %d has undeclared extra fields %s" % (index, sorted(extra)))
        item_id = row["id"]
        if not isinstance(item_id, str) or not item_id:
            report.fail("item row %d has a non-string or empty id" % index)
            continue
        if item_id in seen:
            report.fail("duplicate item id: %s" % item_id)
            continue
        seen.add(item_id)
        question = row["question"]
        if not isinstance(question, str) or len(question) < 40:
            report.fail("item %s has a missing or implausibly short question" % item_id)
            continue
        assets = row["assets"]
        if not isinstance(assets, list) or not assets:
            report.fail("item %s must reference at least one asset" % item_id)
            continue
        for asset in assets:
            if not isinstance(asset, str):
                report.fail("item %s has a non-string asset reference" % item_id)
                continue
            if os.path.isabs(asset) or asset.startswith("..") or "\\" in asset:
                report.fail(
                    "item %s asset reference %r is not a safe bundle-relative path"
                    % (item_id, asset)
                )
                continue
            resolved = os.path.normpath(os.path.join(bundle_dir, asset))
            if not resolved.startswith(os.path.normpath(bundle_dir) + os.sep):
                report.fail("item %s asset %r escapes the bundle" % (item_id, asset))
                continue
            if not os.path.isfile(resolved):
                report.fail("item %s asset %r does not exist in the bundle" % (item_id, asset))
        ids.append(item_id)
        questions[item_id] = question
    return ids, questions


def walk_bundle(bundle_dir):
    paths = []
    for root, dirnames, filenames in os.walk(bundle_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.startswith("."):
                continue
            paths.append(os.path.join(root, filename))
    return paths


def check_bundle_hygiene(bundle_dir, gold_answers, report):
    paths = walk_bundle(bundle_dir)
    if not paths:
        report.fail("solver bundle is empty: %s" % bundle_dir)
        return

    required = {"SOLVER_MANIFEST.json", "items_private_sample.jsonl"}
    present = set(os.path.relpath(p, bundle_dir).replace(os.sep, "/") for p in paths)
    for name in sorted(required):
        if name not in present:
            report.fail("solver bundle is missing required file: %s" % name)
    if not ({"README.md", "solver_packet.md"} & present):
        report.fail("solver bundle needs a README.md or a solver_packet.md")

    for path in paths:
        relative = os.path.relpath(path, bundle_dir).replace(os.sep, "/")
        for pattern in FORBIDDEN_BUNDLE_NAME_PATTERNS:
            if pattern.search(relative):
                report.fail(
                    "bundle file %r looks like a private artefact (matched %r)"
                    % (relative, pattern.pattern)
                )

    standalone_hits = {}
    for path in paths:
        relative = os.path.relpath(path, bundle_dir).replace(os.sep, "/")
        if not relative.lower().endswith(TEXT_SUFFIXES):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for number, line in enumerate(handle, start=1):
                for item_id, answer in gold_answers.items():
                    if item_id in line and re.search(
                        r"(?<![0-9.])" + re.escape(answer) + r"(?![0-9.])", line
                    ):
                        report.fail(
                            "possible answer leak: %s line %d carries id %s next to its gold value"
                            % (relative, number, item_id)
                        )
                for answer in set(gold_answers.values()):
                    if re.search(r"(?<![0-9.])" + re.escape(answer) + r"(?![0-9.])", line):
                        standalone_hits.setdefault(answer, []).append(relative)

    if standalone_hits:
        report.note(
            "informational: %d distinct gold value(s) also occur as standalone numbers "
            "in the bundle (expected, since the statute itself quotes money amounts): %s"
            % (
                len(standalone_hits),
                ", ".join(
                    "%s in %s" % (value, sorted(set(files))[0])
                    for value, files in sorted(standalone_hits.items())
                ),
            )
        )


def cross_check_corpus(item_ids, gold_answers, questions, bundle_dir, report):
    items_path = os.path.join(CORPUS_DIR, "items.json")
    pack_path = os.path.join(CORPUS_DIR, "statute_pack.md")
    if not os.path.isfile(items_path) or not os.path.isfile(pack_path):
        report.note("authored source corpus not present; provenance cross-check skipped")
        return
    with open(items_path, "r", encoding="utf-8") as handle:
        corpus = json.load(handle)
    by_id = {}
    for row in corpus["items"]:
        by_id[row["id"]] = row
    for item_id in item_ids:
        source = by_id.get(item_id)
        if source is None:
            report.fail("item %s is not present in the authored corpus" % item_id)
            continue
        if str(source["answer"]) != gold_answers.get(item_id):
            report.fail(
                "gold answer for %s (%r) disagrees with the authored corpus (%r)"
                % (item_id, gold_answers.get(item_id), str(source["answer"]))
            )
        if source["question"] != questions.get(item_id):
            report.fail(
                "solver-visible question for %s differs from the authored corpus" % item_id
            )
    with open(pack_path, "r", encoding="utf-8") as handle:
        source_pack = handle.read()
    bundle_pack = os.path.join(bundle_dir, "assets", "statute_pack.md")
    if not os.path.isfile(bundle_pack):
        report.fail("bundle asset assets/statute_pack.md is missing")
    else:
        with open(bundle_pack, "r", encoding="utf-8") as handle:
            if handle.read() != source_pack:
                report.fail(
                    "bundle asset assets/statute_pack.md differs from corpus/statute_pack.md"
                )


def diagnostics(gold_answers, item_ids, report):
    values = [gold_answers[item_id] for item_id in item_ids if item_id in gold_answers]
    if not values:
        return
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    best_value, best_count = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    numeric = sorted(int(v) for v in values)
    report.note("items: %d" % len(values))
    report.note("distinct gold values: %d" % len(counts))
    report.note(
        "best constant-guess baseline: %d/%d (%.1f%%) by always answering %s"
        % (best_count, len(values), 100.0 * best_count / len(values), best_value)
    )
    report.note("gold value range: %d to %d" % (numeric[0], numeric[-1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify the Consolidation Point package.")
    parser.add_argument("--items", required=True)
    parser.add_argument("--gold", required=True)
    args = parser.parse_args(argv)

    report = Report()
    bundle_dir = os.path.dirname(os.path.abspath(args.items))

    gold_rows = read_jsonl(args.gold, "gold", report)
    item_rows = read_jsonl(args.items, "items", report)

    gold_ids, gold_answers = check_gold_rows(gold_rows, report)
    item_ids, questions = check_item_rows(item_rows, bundle_dir, report)

    if gold_ids and item_ids:
        if gold_ids != item_ids:
            if set(gold_ids) != set(item_ids):
                only_gold = sorted(set(gold_ids) - set(item_ids))
                only_items = sorted(set(item_ids) - set(gold_ids))
                report.fail(
                    "id sets differ; gold-only=%s items-only=%s" % (only_gold, only_items)
                )
            else:
                report.fail("gold and item files contain the same ids in a different order")

    check_bundle_hygiene(bundle_dir, gold_answers, report)
    cross_check_corpus(item_ids, gold_answers, questions, bundle_dir, report)
    diagnostics(gold_answers, item_ids, report)

    for note in report.notes:
        sys.stdout.write("NOTE: %s\n" % note)
    for warning in report.warnings:
        sys.stdout.write("WARN: %s\n" % warning)
    for failure in report.failures:
        sys.stdout.write("FAIL: %s\n" % failure)

    if report.failures:
        sys.stdout.write("VERIFY: FAIL (%d problem(s))\n" % len(report.failures))
        return 1
    sys.stdout.write("VERIFY: PASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

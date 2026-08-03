# Consolidation Point - solver bundle

This directory is the complete public solver bundle for the Consolidation
Point benchmark. It contains no answers.

Contents:

- `solver_packet.md` - read this first. Task statement, answer format, ground
  rules and a fully worked example.
- `items_private_sample.jsonl` - the graded cases, one JSON object per line.
- `assets/statute_pack.md` - the legislative source pack referenced by every
  item.
- `SOLVER_MANIFEST.json` - machine-readable description of this bundle.

Produce a JSONL file with one object per line containing exactly the keys
`id` and `answer`, one line per item id, where `answer` is the levy in marks
written as digits only.

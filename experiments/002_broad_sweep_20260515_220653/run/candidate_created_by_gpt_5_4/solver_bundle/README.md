# Solver Bundle

Each row in `items_private_sample.jsonl` is one benchmark item.

For each item, output exactly one JSON line with:

`{"id": "...", "answer": "..."}`

Rules:
- `answer` must be the full reconstructed string.
- Use the provided alphabet, exact symbol counts, exact shuffled multiset of contiguous 4-grams, forbidden trigrams, and anchor multiset clues.
- The intended item property is uniqueness: exactly one string satisfies all visible constraints.

# Failure Modes

## Likely solver mistakes

1. Greedy local stitching
   - Taking the lexicographically first available 4-gram extension often yields a full-length string that is globally wrong.
   - The generator explicitly filters for items where this shortcut fails.

2. Ignoring multiplicity
   - Treating the spectrum as a set rather than a multiset drops repeated 4-grams and changes the search space.

3. Ignoring side constraints until the end
   - Counts, forbidden trigrams, and anchor clues are strongest when used during search, not only as a final filter.

4. Off-by-one anchor handling
   - Anchor positions are zero-indexed and refer to the final string.

5. Partial Eulerian reasoning
   - The 4-gram spectrum suggests a de Bruijn graph view, but side constraints break pure graph-local reasoning. Solvers need graph structure plus global pruning.

## Known package limitations

1. Human baseline is argued but not empirically measured in this package.
2. The current sample uses one family of synthetic structured items rather than multiple task families.
3. Some items are already unique from spectrum plus count and trigram constraints alone, so anchor clues appear only when needed.

## What would make a future version stronger

1. Collect measured human-with-tools baselines.
2. Add a tiny anchor subset and a larger held-out test set.
3. Run several real solver models and publish item-level failure traces.

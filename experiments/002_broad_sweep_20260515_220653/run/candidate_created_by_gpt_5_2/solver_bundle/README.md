# IgnoreSense solver packet

You are given a set of independent items. Each item contains:

- `gitignore`: the contents of a `.gitignore` file (single file, no nested `.gitignore`s)
- `paths`: a list of relative paths to classify as ignored vs not ignored

Your job is to output `predictions.jsonl` with **exactly**:

```json
{"id":"...","answer":"..."}
```

Where `answer` is a **string** that is itself a JSON array of strings: the paths from `paths` that are ignored, sorted lexicographically.

Example answer string:

```json
"[\"build/\",\"dist/app.js\"]"
```

## Matching semantics (the subset used in this benchmark)

This benchmark uses a precise subset of `.gitignore` semantics, implemented by the reference matcher used to generate the gold answers.

### Line handling

- Blank lines are ignored.
- Lines whose first non-space character is `#` are comments and ignored.
- A leading `!` negates a pattern (un-ignore). Last matching rule wins.
- A leading `\\` escapes the next character so that `\\#` and `\\!` match literal `#` and `!` at the start.

### Pattern handling

Patterns are matched against each query path using `/` as separator:

- A trailing `/` makes a pattern **directory-only**: if it matches a directory, it ignores the entire directory subtree.
- A leading `/` anchors a pattern to the repo root (all paths are already relative).
- If the pattern contains no `/`, it is a **basename** pattern and is tested against each path segment.
- If the pattern contains `/`, it is tested against the full normalized path.

### Globs

- `*` matches any string except `/`
- `?` matches any single character except `/`
- `**` matches any string including `/` (may be empty)
- Character classes like `[abc]` and `[a-z]` are supported

Important: do not assume additional gitignore features beyond the above subset.


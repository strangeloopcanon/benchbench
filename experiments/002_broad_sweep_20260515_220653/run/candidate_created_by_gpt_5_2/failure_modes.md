# Failure modes (IgnoreSense)

This benchmark is designed so that naive or partial `.gitignore` implementations fail in characteristic, auditable ways.

## Common solver failures

- **No negation support**: treating `!pattern` as literal text or ignoring it, causing last-rule precedence to be wrong.
- **Wrong precedence**: using “first match wins” rather than “last match wins”.
- **Basename semantics wrong**: applying `foo` only to the full path instead of to each path segment.
- **Anchoring wrong**: treating leading `/` as a literal slash rather than “match from repo root”.
- **Directory-only wrong**: treating `build/` as matching only the literal directory path, not all files under it.
- **Escaping wrong**: not handling `\\#` and `\\!` correctly at the start of a pattern.
- **Glob mistakes**: treating `*` as crossing `/`, or failing to implement `**` correctly.

## Benchmark limitations (intentional scope)

- No nested `.gitignore` files.
- No `**/` special-casing beyond treating `**` as “match anything including `/`”.
- No platform path-separator issues: all paths use `/`.
- No symlinks, filesystem calls, or git attributes.

If you extend this benchmark, expand the subset carefully and keep the reference matcher and solver packet aligned.


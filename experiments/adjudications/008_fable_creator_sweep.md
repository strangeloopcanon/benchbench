# Adjudication: Fable Creator Sweep (Experiment 008)

Outcome: **infrastructure incomplete; not canonical**.

The manifest records a GPT-5.2 provider failure (`returncode: 1`, zero prediction rows) and a Claude Opus timeout. Earlier reporting rendered both as `0/30`; that is false. They are typed execution states:

| evidence | SHA-256 |
|---|---|
| `manifest.json` | `044b2d32691fc1c7e661c66bd3d814b949166addb3fd183b898b2d4d62e24dca` |

| solver | canonical cell state |
|---|---|
| GPT-5.2 | `provider_error` |
| Claude Opus | `timeout` |

The successful historical cells remain visible in the registry, but an incomplete panel is not a benchmark result. Provider preflight and typed cell-state handling must be in place before the missing cells are rerun.

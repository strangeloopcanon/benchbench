# Maritime General Average & Salvage Forensics (MGAF) — Solver Packet

Read `assets/maritime_ga_rulebook.md` and `assets/fx_and_port_tariffs.csv` alongside the case dossiers in `assets/dossiers_part1.md` (`mgaf_01`–`mgaf_10`), `assets/dossiers_part2.md` (`mgaf_11`–`mgaf_20`), and `assets/dossiers_part3.md` (`mgaf_21`–`mgaf_30`).

For each item in `items_private_sample.jsonl` (`mgaf_01` through `mgaf_30`), return the exact integer USD cents (`$1.00 = 100` cents) payable by Cargo Interest `Lot-A`:

$$\text{Answer (USD Cents)} = \text{Salvage}_{\text{Lot-A}} + \text{GA}_{\text{Lot-A}} + \text{SpecialCharges}_{\text{Lot-A}}$$

Each output row in `predictions.jsonl` must be a JSON object with keys `"id"` and `"answer"` (an integer in USD cents).

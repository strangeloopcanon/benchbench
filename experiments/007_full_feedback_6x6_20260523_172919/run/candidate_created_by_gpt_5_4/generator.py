import argparse
import csv
import json
import math
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


BENCHMARK_NAME = "Catalog Royalty Forensics (CRF) v1"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def cents(n: int) -> str:
    return f"${n / 100:.2f}"


def clamp_non_negative(n: int) -> int:
    return n if n > 0 else 0


TERRITORY_GROUPS: Dict[str, List[str]] = {
    "NA": ["US", "CA"],
    "UKIE": ["GB", "IE"],
    "ANZ": ["AU", "NZ"],
    "EU_CORE": ["DE", "FR", "ES", "IT", "NL"],
    "LATAM": ["BR", "MX", "AR"],
}

FORMATS = ["ebook", "audio", "paperback", "hardcover"]
CHANNELS = ["retail", "direct", "subscription", "library", "bundle"]


@dataclass(frozen=True)
class ItemTerms:
    item_id: str
    title: str
    licensed_territories: Tuple[str, ...]
    excluded_territories: Tuple[str, ...]
    licensed_formats: Tuple[str, ...]
    single_channel_exclusions: Tuple[str, ...]
    rate_bps: Dict[str, int]
    opening_advance_cents: int
    reserve_release_cents: int
    reserve_withhold_pct: int
    discount_floor_pct: int
    discount_floor_exempt_channels: Tuple[str, ...]
    bundle_split_pct: int
    effective_start: str
    effective_end: str
    amendments: List[Dict[str, Any]]


def public_policy_text() -> str:
    return (
        "# Catalog Royalty Forensics (Public Rulebook)\n\n"
        "This benchmark asks you to compute a quarter-end royalty statement from public contract documents and public sales evidence.\n\n"
        "## Answer fields\n\n"
        "Return JSON with exactly these fields:\n"
        "- `included_units`: integer\n"
        "- `earned_royalty_cents`: integer\n"
        "- `recouped_advance_cents`: integer\n"
        "- `payable_cents`: integer\n\n"
        "## 1) Inclusion rules\n\n"
        "A sales row contributes only if all of the following are true:\n"
        "1. `sale_date` falls within the licensed effective window.\n"
        "2. `territory` is licensed and not carved out.\n"
        "3. `format` is licensed.\n"
        "4. `channel` is not excluded by the base rider or a later amendment.\n"
        "5. `is_promo` is `0` unless a later amendment explicitly says otherwise.\n\n"
        "Negative `units` or negative money values represent reversals or returns. If the original row type would have been included, the negative row also counts and subtracts from totals.\n\n"
        "## 2) Document precedence\n\n"
        "Use the latest applicable rule in this order:\n"
        "1. Later amendment\n"
        "2. Base rights rider\n"
        "3. This public rulebook\n\n"
        "The finance memo is authoritative only for opening advance balance and reserve release.\n\n"
        "## 3) Recognized base per row\n\n"
        "Start from the row's `gross_cents`.\n\n"
        "Then apply these public adjustments in order:\n"
        "1. If `channel = bundle`, use `bundle_allocated_cents` instead of `gross_cents`.\n"
        "2. If the row is included, check the contractual discount floor. Compute the row's actual unit price as `gross_cents / units` using absolute values. If that unit price is below `discount_floor_pct` of `list_price_cents`, and the channel is not floor-exempt, replace the recognized base with `units * floor(discount_floor_pct * list_price_cents / 100)` while preserving the original sign.\n"
        "3. If an amendment applies a base multiplier for that row, multiply the recognized base by that percentage and round down toward zero.\n\n"
        "## 4) Rate selection\n\n"
        "Each format has a base royalty rate in basis points.\n"
        "An amendment may override the rate for a format, channel, territory set, or date window.\n"
        "Use the latest applicable override. If multiple filters are listed, all of them must match.\n\n"
        "## 5) Row earnings and units\n\n"
        "For each included row:\n"
        "- `included_units` adds the signed `units` value.\n"
        "- Row royalty earnings are `trunc_toward_zero(recognized_base_cents * rate_bps / 10000)`.\n\n"
        "Truncation toward zero means:\n"
        "- `123.9 -> 123`\n"
        "- `-123.9 -> -123`\n\n"
        "## 6) Reserve withholding\n\n"
        "Current-quarter reserve withholding applies only to included physical rows (`paperback` and `hardcover`) whose royalty earnings are positive.\n"
        "Reserve withheld is `floor(sum(positive physical-row earnings) * reserve_withhold_pct / 100)`.\n\n"
        "## 7) Advance recoupment and payable amount\n\n"
        "- `earned_royalty_cents` is the sum of all included row earnings.\n"
        "- `recouped_advance_cents = min(max(earned_royalty_cents, 0), opening_advance_cents)`.\n"
        "- `payable_cents = max(0, earned_royalty_cents + reserve_release_cents - reserve_withheld_cents - recouped_advance_cents)`.\n\n"
        "Reserve release increases payable but does not reduce recoupment.\n"
    )


def make_item_terms(rng: random.Random, item_index: int) -> ItemTerms:
    all_territories = sorted({t for group in TERRITORY_GROUPS.values() for t in group})
    territory_pool = list(TERRITORY_GROUPS.keys())
    chosen_groups = rng.sample(territory_pool, k=rng.randint(2, 4))
    licensed = sorted({t for g in chosen_groups for t in TERRITORY_GROUPS[g]})
    carveout_count = rng.randint(0, min(2, max(0, len(licensed) - 2)))
    excluded = tuple(sorted(rng.sample(licensed, k=carveout_count))) if carveout_count else tuple()

    format_count = rng.randint(2, 4)
    licensed_formats = tuple(sorted(rng.sample(FORMATS, k=format_count)))
    excluded_channels = tuple(sorted(rng.sample(CHANNELS, k=rng.randint(0, 1))))

    base_rates = {
        "ebook": rng.choice([1800, 2000, 2200, 2500]),
        "audio": rng.choice([1600, 1800, 2000, 2200]),
        "paperback": rng.choice([900, 1000, 1200, 1400]),
        "hardcover": rng.choice([1100, 1300, 1500, 1700]),
    }

    opening_advance = rng.randint(15000, 110000)
    reserve_release = rng.randint(0, 35000)
    reserve_pct = rng.choice([10, 15, 20, 25])
    floor_pct = rng.choice([55, 60, 65, 70])
    floor_exempt = tuple(sorted(rng.sample(["direct", "subscription"], k=rng.randint(0, 1))))
    bundle_split_pct = rng.choice([25, 30, 35, 40, 50])

    quarter_start = "2026-01-01"
    quarter_end = "2026-03-31"

    title = rng.choice(
        [
            "Signal Harbor",
            "Glass Provinces",
            "North of Eventide",
            "The Latent Orchard",
            "Errata for Wolves",
            "Quiet Meridian",
            "The Fifth Freight",
            "Pale Cartography",
        ]
    )

    amendments: List[Dict[str, Any]] = []
    if rng.random() < 0.8:
        amendments.append(
            {
                "type": "rate_override",
                "effective_from": rng.choice(["2026-02-01", "2026-02-10", "2026-02-20"]),
                "format": rng.choice(list(licensed_formats)),
                "channel": rng.choice(["subscription", "direct", "retail", "ANY"]),
                "territories": rng.choice(["ANY", "US|CA", "GB|IE", "DE|FR|ES|IT|NL"]),
                "new_rate_bps": rng.choice([700, 900, 1100, 1500, 1800, 2400, 2800]),
            }
        )
    if rng.random() < 0.65:
        amendments.append(
            {
                "type": "base_multiplier",
                "effective_from": rng.choice(["2026-01-15", "2026-02-15", "2026-03-01"]),
                "format": rng.choice(list(licensed_formats)),
                "channel": rng.choice(["bundle", "library", "subscription", "ANY"]),
                "territories": rng.choice(["ANY", "US|CA", "AU|NZ", "BR|MX|AR"]),
                "multiplier_pct": rng.choice([50, 60, 70, 80]),
            }
        )
    if rng.random() < 0.55:
        amendments.append(
            {
                "type": "promo_exception",
                "effective_from": rng.choice(["2026-01-01", "2026-02-01", "2026-03-01"]),
                "channel": rng.choice(["direct", "subscription"]),
                "format": rng.choice(list(licensed_formats) + ["ANY"]),
                "multiplier_pct": rng.choice([25, 40, 50]),
            }
        )
    if rng.random() < 0.5:
        territory_candidates = [t for t in all_territories if t not in licensed]
        if territory_candidates:
            amendments.append(
                {
                    "type": "territory_add",
                    "effective_from": rng.choice(["2026-01-20", "2026-02-15", "2026-03-10"]),
                    "territories": "|".join(sorted(rng.sample(territory_candidates, k=1))),
                }
            )
    if rng.random() < 0.45:
        channel_candidates = [c for c in CHANNELS if c not in excluded_channels]
        if channel_candidates:
            amendments.append(
                {
                    "type": "channel_exclusion",
                    "effective_from": rng.choice(["2026-02-05", "2026-03-05"]),
                    "channel": rng.choice(channel_candidates),
                }
            )

    amendments.sort(key=lambda x: (x["effective_from"], x["type"]))
    return ItemTerms(
        item_id=f"crf_{item_index:03d}",
        title=title,
        licensed_territories=tuple(licensed),
        excluded_territories=excluded,
        licensed_formats=licensed_formats,
        single_channel_exclusions=excluded_channels,
        rate_bps=base_rates,
        opening_advance_cents=opening_advance,
        reserve_release_cents=reserve_release,
        reserve_withhold_pct=reserve_pct,
        discount_floor_pct=floor_pct,
        discount_floor_exempt_channels=floor_exempt,
        bundle_split_pct=bundle_split_pct,
        effective_start=quarter_start,
        effective_end=quarter_end,
        amendments=amendments,
    )


def trunc_toward_zero(value: float) -> int:
    return math.trunc(value)


def amendment_applies(amendment: Dict[str, Any], row: Dict[str, Any]) -> bool:
    if row["sale_date"] < amendment["effective_from"]:
        return False
    if amendment.get("format") and amendment["format"] != "ANY" and row["format"] != amendment["format"]:
        return False
    if amendment.get("channel") and amendment["channel"] != "ANY" and row["channel"] != amendment["channel"]:
        return False
    territories = amendment.get("territories")
    if territories and territories != "ANY":
        allowed = set(territories.split("|"))
        if row["territory"] not in allowed:
            return False
    return True


def licensed_territories_for_date(terms: ItemTerms, sale_date: str) -> set[str]:
    territories = set(terms.licensed_territories)
    for amendment in terms.amendments:
        if amendment["type"] == "territory_add" and sale_date >= amendment["effective_from"]:
            territories.update(amendment["territories"].split("|"))
    return territories


def channel_excluded_for_date(terms: ItemTerms, row: Dict[str, Any]) -> bool:
    excluded = set(terms.single_channel_exclusions)
    for amendment in terms.amendments:
        if amendment["type"] == "channel_exclusion" and row["sale_date"] >= amendment["effective_from"]:
            excluded.add(amendment["channel"])
    return row["channel"] in excluded


def promo_exception_for_row(terms: ItemTerms, row: Dict[str, Any]) -> int | None:
    result: int | None = None
    for amendment in terms.amendments:
        if amendment["type"] != "promo_exception":
            continue
        if not amendment_applies(amendment, row):
            continue
        result = amendment["multiplier_pct"]
    return result


def multiplier_for_row(terms: ItemTerms, row: Dict[str, Any]) -> int:
    result = 100
    for amendment in terms.amendments:
        if amendment["type"] != "base_multiplier":
            continue
        if not amendment_applies(amendment, row):
            continue
        result = amendment["multiplier_pct"]
    return result


def rate_for_row(terms: ItemTerms, row: Dict[str, Any]) -> int:
    result = terms.rate_bps[row["format"]]
    for amendment in terms.amendments:
        if amendment["type"] != "rate_override":
            continue
        if not amendment_applies(amendment, row):
            continue
        result = amendment["new_rate_bps"]
    return result


def row_included(terms: ItemTerms, row: Dict[str, Any]) -> Tuple[bool, int]:
    if not (terms.effective_start <= row["sale_date"] <= terms.effective_end):
        return (False, 0)
    if row["format"] not in terms.licensed_formats:
        return (False, 0)
    if row["territory"] in terms.excluded_territories:
        return (False, 0)
    if row["territory"] not in licensed_territories_for_date(terms, row["sale_date"]):
        return (False, 0)
    if channel_excluded_for_date(terms, row):
        return (False, 0)
    if row["is_promo"] == 1:
        promo_multiplier = promo_exception_for_row(terms, row)
        if promo_multiplier is None:
            return (False, 0)
        return (True, promo_multiplier)
    return (True, 100)


def recognized_base_cents(terms: ItemTerms, row: Dict[str, Any], promo_multiplier: int) -> int:
    gross = int(row["gross_cents"])
    units = int(row["units"])
    sign = -1 if gross < 0 or units < 0 else 1
    abs_units = abs(units)
    base = abs(gross)
    if row["channel"] == "bundle":
        base = abs(int(row["bundle_allocated_cents"]))
    exempt = row["channel"] in terms.discount_floor_exempt_channels
    list_price = int(row["list_price_cents"])
    if abs_units > 0 and not exempt:
        actual_per_unit = base / abs_units
        floor_unit = (terms.discount_floor_pct * list_price) // 100
        if actual_per_unit < floor_unit:
            base = abs_units * floor_unit
    base = trunc_toward_zero(base * promo_multiplier / 100)
    base = trunc_toward_zero(base * multiplier_for_row(terms, row) / 100)
    return sign * base


def make_rows(rng: random.Random, terms: ItemTerms) -> List[Dict[str, Any]]:
    all_territories = sorted({t for group in TERRITORY_GROUPS.values() for t in group})
    rows: List[Dict[str, Any]] = []
    row_count = rng.randint(9, 14)
    for idx in range(row_count):
        fmt = rng.choice(FORMATS)
        channel = rng.choice(CHANNELS)
        territory = rng.choice(all_territories)
        units = rng.choice([1, 1, 2, 2, 3, 4, 5, 8, 10, 12, 15])
        if rng.random() < 0.18:
            units *= -1
        list_price = {
            "ebook": rng.choice([899, 1099, 1299, 1499]),
            "audio": rng.choice([1599, 1899, 2199, 2499]),
            "paperback": rng.choice([1499, 1699, 1899, 2099]),
            "hardcover": rng.choice([2299, 2499, 2799, 2999]),
        }[fmt]
        unit_price = rng.choice(
            [
                list_price,
                int(list_price * 0.9),
                int(list_price * 0.75),
                int(list_price * 0.6),
                int(list_price * 0.45),
            ]
        )
        gross = abs(units) * unit_price
        if rng.random() < 0.08:
            gross = 0
        if units < 0:
            gross *= -1

        bundle_alloc = 0
        if channel == "bundle":
            bundle_alloc = trunc_toward_zero(abs(gross) * terms.bundle_split_pct / 100)
            if units < 0:
                bundle_alloc *= -1

        sale_date = f"2026-{rng.choice(['01', '02', '03'])}-{rng.randint(1, 28):02d}"
        is_promo = 1 if rng.random() < 0.16 else 0
        if units < 0 and rng.random() < 0.7:
            is_promo = 0

        rows.append(
            {
                "row_id": f"{terms.item_id}_r{idx + 1:02d}",
                "sale_date": sale_date,
                "territory": territory,
                "channel": channel,
                "format": fmt,
                "units": units,
                "gross_cents": gross,
                "list_price_cents": list_price,
                "bundle_allocated_cents": bundle_alloc,
                "is_promo": is_promo,
                "notes": rng.choice(
                    [
                        "standard shipment",
                        "wholesale feed import",
                        "DSP settlement",
                        "library batch",
                        "metadata sync row",
                        "manual correction row",
                    ]
                ),
            }
        )
    return rows


def compute_answer(terms: ItemTerms, rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    included_units = 0
    earned = 0
    positive_physical_earnings = 0
    for row in rows:
        included, promo_multiplier = row_included(terms, row)
        if not included:
            continue
        base = recognized_base_cents(terms, row, promo_multiplier)
        rate_bps = rate_for_row(terms, row)
        row_earned = trunc_toward_zero(base * rate_bps / 10000)
        included_units += int(row["units"])
        earned += row_earned
        if row["format"] in {"paperback", "hardcover"} and row_earned > 0:
            positive_physical_earnings += row_earned
    reserve_withheld = (positive_physical_earnings * terms.reserve_withhold_pct) // 100
    recouped = min(max(earned, 0), terms.opening_advance_cents)
    payable = clamp_non_negative(earned + terms.reserve_release_cents - reserve_withheld - recouped)
    return {
        "included_units": included_units,
        "earned_royalty_cents": earned,
        "recouped_advance_cents": recouped,
        "payable_cents": payable,
    }


def make_rights_rider(terms: ItemTerms) -> str:
    territory_text = ", ".join(terms.licensed_territories)
    carveout_text = ", ".join(terms.excluded_territories) if terms.excluded_territories else "(none)"
    excluded_channels = ", ".join(terms.single_channel_exclusions) if terms.single_channel_exclusions else "(none)"
    floor_exempt = ", ".join(terms.discount_floor_exempt_channels) if terms.discount_floor_exempt_channels else "(none)"
    lines = [
        "# Base Rights Rider\n",
        f"Title: {terms.title}",
        f"Effective window: {terms.effective_start} through {terms.effective_end}",
        f"Licensed territories: {territory_text}",
        f"Territory carve-outs: {carveout_text}",
        f"Licensed formats: {', '.join(terms.licensed_formats)}",
        f"Excluded channels at signing: {excluded_channels}\n",
        "## Base royalty rates",
        f"- ebook: {terms.rate_bps['ebook']} bps",
        f"- audio: {terms.rate_bps['audio']} bps",
        f"- paperback: {terms.rate_bps['paperback']} bps",
        f"- hardcover: {terms.rate_bps['hardcover']} bps\n",
        "## Commercial mechanics",
        f"- Opening unrecouped advance balance: {terms.opening_advance_cents} cents",
        f"- Reserve release this quarter: {terms.reserve_release_cents} cents",
        f"- Current-quarter reserve withholding on positive physical royalties: {terms.reserve_withhold_pct}%",
        f"- Discount floor: {terms.discount_floor_pct}% of list price per unit",
        f"- Discount floor-exempt channels: {floor_exempt}",
        f"- Bundle allocation share for this title: {terms.bundle_split_pct}% of bundle gross\n",
        "Interpretation note: all amendments are cumulative; later amendments override earlier terms when they conflict.",
    ]
    return "\n".join(lines) + "\n"


def make_amendments_text(terms: ItemTerms) -> str:
    if not terms.amendments:
        return "# Amendments\n\n- None.\n"
    out = ["# Amendments\n"]
    for idx, amendment in enumerate(terms.amendments, start=1):
        if amendment["type"] == "rate_override":
            out.append(
                f"{idx}. Effective {amendment['effective_from']}: rate override to {amendment['new_rate_bps']} bps "
                f"for format={amendment['format']}, channel={amendment['channel']}, territories={amendment['territories']}."
            )
        elif amendment["type"] == "base_multiplier":
            out.append(
                f"{idx}. Effective {amendment['effective_from']}: apply a recognized-base multiplier of {amendment['multiplier_pct']}% "
                f"for format={amendment['format']}, channel={amendment['channel']}, territories={amendment['territories']}."
            )
        elif amendment["type"] == "promo_exception":
            out.append(
                f"{idx}. Effective {amendment['effective_from']}: promo rows may count at {amendment['multiplier_pct']}% of recognized base "
                f"for channel={amendment['channel']} and format={amendment['format']}."
            )
        elif amendment["type"] == "territory_add":
            out.append(
                f"{idx}. Effective {amendment['effective_from']}: add licensed territory set {amendment['territories']}."
            )
        elif amendment["type"] == "channel_exclusion":
            out.append(
                f"{idx}. Effective {amendment['effective_from']}: exclude channel={amendment['channel']} from royalty-bearing sales."
            )
    out.append("")
    return "\n".join(out)


def make_finance_memo(terms: ItemTerms, answer: Dict[str, int], rows: Sequence[Dict[str, Any]]) -> str:
    positive_physical_earned = 0
    for row in rows:
        included, promo_multiplier = row_included(terms, row)
        if not included:
            continue
        if row["format"] not in {"paperback", "hardcover"}:
            continue
        row_earned = trunc_toward_zero(recognized_base_cents(terms, row, promo_multiplier) * rate_for_row(terms, row) / 10000)
        if row_earned > 0:
            positive_physical_earned += row_earned
    reserve_withheld = (positive_physical_earned * terms.reserve_withhold_pct) // 100
    return (
        "# Finance Memo\n\n"
        f"- Opening unrecouped advance entering the quarter: {terms.opening_advance_cents} cents.\n"
        f"- Approved reserve release to add back this quarter: {terms.reserve_release_cents} cents.\n"
        f"- Current-quarter reserve withholding is computed from positive physical-row earnings at {terms.reserve_withhold_pct}%.\n"
        f"- For audit sanity only: the reserve-withholding base is positive physical earnings, not net earnings, and not total gross revenue.\n"
        f"- This implies a current-quarter reserve withheld amount of {reserve_withheld} cents once the statement is computed.\n"
    )


def make_solver_packet_readme() -> str:
    return (
        f"# {BENCHMARK_NAME} Solver Packet\n\n"
        "This bundle is sufficient for an external solver.\n\n"
        "For each item, read:\n"
        "- `public_rulebook.md`\n"
        "- the item's `rights_rider.md`\n"
        "- the item's `amendments.md`\n"
        "- the item's `finance_memo.md`\n"
        "- the item's `sales_statement.csv`\n\n"
        "Then produce one JSON answer object per item with exactly these keys:\n"
        "- `included_units`\n"
        "- `earned_royalty_cents`\n"
        "- `recouped_advance_cents`\n"
        "- `payable_cents`\n\n"
        "No hidden labels are required. Every answer field is determined by public rows and public rules.\n"
    )


def make_items_and_gold(sample_count: int, seed: int, out_dir: Path) -> None:
    rng = random.Random(seed)
    solver_dir = out_dir / "solver_bundle"
    if solver_dir.exists():
        shutil.rmtree(solver_dir)
    solver_dir.mkdir(parents=True, exist_ok=True)

    write_text(solver_dir / "public_rulebook.md", public_policy_text())
    write_text(solver_dir / "README.md", make_solver_packet_readme())

    items_rows: List[Dict[str, Any]] = []
    gold_rows: List[Dict[str, Any]] = []

    for i in range(1, sample_count + 1):
        terms = make_item_terms(rng, i)
        rows = make_rows(rng, terms)
        answer = compute_answer(terms, rows)

        item_dir = solver_dir / "items" / terms.item_id
        write_text(item_dir / "rights_rider.md", make_rights_rider(terms))
        write_text(item_dir / "amendments.md", make_amendments_text(terms))
        write_text(item_dir / "finance_memo.md", make_finance_memo(terms, answer, rows))
        write_csv(
            item_dir / "sales_statement.csv",
            rows,
            [
                "row_id",
                "sale_date",
                "territory",
                "channel",
                "format",
                "units",
                "gross_cents",
                "list_price_cents",
                "bundle_allocated_cents",
                "is_promo",
                "notes",
            ],
        )

        items_rows.append(
            {
                "id": terms.item_id,
                "title": terms.title,
                "assets": {
                    "rulebook": "public_rulebook.md",
                    "rights_rider": f"items/{terms.item_id}/rights_rider.md",
                    "amendments": f"items/{terms.item_id}/amendments.md",
                    "finance_memo": f"items/{terms.item_id}/finance_memo.md",
                    "sales_statement": f"items/{terms.item_id}/sales_statement.csv",
                },
            }
        )
        gold_rows.append({"id": terms.item_id, "answer": answer})

    write_jsonl(solver_dir / "items_private_sample.jsonl", items_rows)
    write_jsonl(out_dir / "gold_private_sample.jsonl", gold_rows)
    write_json(
        solver_dir / "SOLVER_MANIFEST.json",
        {
            "benchmark": BENCHMARK_NAME,
            "sample_count": sample_count,
            "entrypoint": "README.md",
            "items_file": "items_private_sample.jsonl",
            "visible_assets": [
                "public_rulebook.md",
                "items/*/rights_rider.md",
                "items/*/amendments.md",
                "items/*/finance_memo.md",
                "items/*/sales_statement.csv",
            ],
        },
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-count", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", type=str, required=True)
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    make_items_and_gold(sample_count=args.sample_count, seed=args.seed, out_dir=out_dir)
    print(f"generated {args.sample_count} items")


if __name__ == "__main__":
    main()

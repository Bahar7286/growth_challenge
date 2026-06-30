"""Merge web-researched verification data into verified_profile_fields.csv."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
VERIFIED_CSV = ROOT / "data" / "enrichment" / "verified_profile_fields.csv"
BATCH_JSON = ROOT / "data" / "enrichment" / "verified_web_batch.json"

FIELDS = (
    "linkedin_url",
    "company_name",
    "title",
    "location",
    "email",
    "company_size",
    "company_industry",
)


def canonical_linkedin_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "in":
        slug = unquote(path_parts[1]).lower()
        return f"https://www.linkedin.com/in/{slug}/"
    return url.strip()


def load_batch(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, dict[str, str]] = {}
    for item in data:
        url = canonical_linkedin_url(item["linkedin_url"])
        lookup[url] = {k: str(v).strip() for k, v in item.items() if k != "linkedin_url" and v}
    return lookup


def merge_rows(existing: list[dict[str, str]], batch: dict[str, dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    updated = 0
    for row in existing:
        url = canonical_linkedin_url(row.get("linkedin_url", ""))
        patch = batch.get(url)
        if not patch:
            continue
        changed = False
        for key, value in patch.items():
            if key == "linkedin_url":
                continue
            if value and (not row.get(key) or not str(row[key]).strip()):
                row[key] = value
                changed = True
        if changed:
            updated += 1
    return existing, updated


def main() -> None:
    batch_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BATCH_JSON
    if not batch_path.exists():
        raise SystemExit(f"Batch file not found: {batch_path}")
    if not VERIFIED_CSV.exists():
        raise SystemExit(f"Verified CSV not found: {VERIFIED_CSV}")

    batch = load_batch(batch_path)
    with VERIFIED_CSV.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    rows, updated = merge_rows(rows, batch)

    with VERIFIED_CSV.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    filled = sum(
        1 for row in rows
        if row.get("company_name", "").strip() and row.get("title", "").strip()
    )
    print(f"Updated {updated} rows from {batch_path.name}")
    print(f"Verified company+title: {filled}/{len(rows)}")


if __name__ == "__main__":
    main()

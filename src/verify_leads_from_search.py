from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from enrich_from_public_search import canonical_linkedin_url, search_public_web, slug_from_url
from llm_enrich import _call_llm, _get_client

# Import name parser without running build_leads main
from build_leads import full_name_from_slug

RAW_INPUT = ROOT / "data" / "raw" / "linkedin_profile_links_100.csv"
VERIFIED_OUTPUT = ROOT / "data" / "enrichment" / "verified_profile_fields.csv"
VERIFY_CACHE = ROOT / "data" / "enrichment" / "verify_search_cache.json"

FIELDNAMES = [
    "linkedin_url", "company_name", "title", "location", "email",
    "company_size", "company_industry",
]

BATCH_EXTRACT_PROMPT = """Sen veri çıkarma asistanısın. Aşağıdaki Türkiye HR lead'leri için arama snippet'lerinden şirket ve unvan çıkar.

Kurallar:
- Sadece snippet'lerde açıkça görünen bilgiyi yaz; emin değilsen boş bırak.
- HR / İnsan Kaynakları unvanı tercih et.
- Uydurma yapma.

Leads:
{leads_block}

Sadece JSON array döndür. Her eleman:
{{"linkedin_url":"","company_name":"","title":"","location":"","company_industry":""}}
"""


def is_valid_title(title: str) -> bool:
    t = (title or "").strip()
    if len(t) < 5:
        return False
    if t.upper() in {"HR", "IK", "İK"}:
        return False
    return True


def is_valid_company(company: str) -> bool:
    c = (company or "").strip()
    return len(c) >= 3 and "to verify" not in c.lower()


def is_filled(row: dict[str, str]) -> bool:
    return is_valid_company(row.get("company_name", "")) and is_valid_title(row.get("title", ""))


def load_cache() -> dict[str, Any]:
    if VERIFY_CACHE.exists():
        return json.loads(VERIFY_CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, Any]) -> None:
    VERIFY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    VERIFY_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def read_urls() -> list[str]:
    with RAW_INPUT.open(encoding="utf-8-sig", newline="") as f:
        return list(dict.fromkeys(
            canonical_linkedin_url(r["linkedin_url"].strip())
            for r in csv.DictReader(f) if r.get("linkedin_url")
        ))


def load_verified() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    if not VERIFIED_OUTPUT.exists():
        return lookup
    with VERIFIED_OUTPUT.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            url = canonical_linkedin_url(row.get("linkedin_url", ""))
            if url:
                lookup[url] = row
    return lookup


def search_one(url: str) -> tuple[str, str]:
    slug = slug_from_url(url)
    name = full_name_from_slug(slug)
    query = f'site:linkedin.com/in/{slug} "{name}" İnsan Kaynakları'
    try:
        snippets = search_public_web(query, timeout=10)
    except Exception as exc:
        snippets = f"SEARCH_ERROR: {exc}"
    return url, snippets


def extract_batch(batch: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    """batch: [(url, full_name, snippets), ...]"""
    client = _get_client()
    if not client:
        return []

    blocks = []
    for url, name, snippets in batch:
        blocks.append(
            f"URL: {url}\nName: {name}\nSnippets:\n{snippets[:1500]}\n"
        )
    prompt = BATCH_EXTRACT_PROMPT.format(leads_block="\n---\n".join(blocks))
    try:
        data = _call_llm(client, prompt)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "leads" in data:
            return data["leads"]
        if isinstance(data, dict):
            return [data]
    except Exception as exc:
        print(f"  Batch LLM error: {exc}", flush=True)
    return []


def sanitize(row: dict[str, str]) -> dict[str, str]:
    out = {k: str(row.get(k, "") or "").strip() for k in ("company_name", "title", "location", "company_industry")}
    if not is_valid_title(out["title"]):
        out["title"] = ""
    if not is_valid_company(out["company_name"]):
        out["company_name"] = ""
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size", type=int, default=5)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--force", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    urls = read_urls()
    existing = load_verified()
    cache = load_cache()

    pending = [
        u for u in urls
        if args.force or not is_filled(existing.get(u, {"linkedin_url": u}))
    ]
    print(f"Pending verification: {len(pending)} leads", flush=True)

    for start in range(0, len(pending), args.batch_size):
        chunk = pending[start : start + args.batch_size]
        print(f"Batch {start // args.batch_size + 1}: {len(chunk)} leads", flush=True)

        search_results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(search_one, url): url for url in chunk}
            for fut in as_completed(futures):
                url, snippets = fut.result()
                search_results[url] = snippets

        batch_input = [
            (url, full_name_from_slug(slug_from_url(url)), search_results[url])
            for url in chunk
        ]
        extracted_rows = extract_batch(batch_input)

        by_url = {
            canonical_linkedin_url(r.get("linkedin_url", "")): sanitize(r)
            for r in extracted_rows if r.get("linkedin_url")
        }

        for url in chunk:
            found = by_url.get(url, {})
            if not found and url in cache:
                found = cache[url]
            cache[url] = found
            row = existing.get(url, {"linkedin_url": url})
            for key in ("company_name", "title", "location", "company_industry"):
                if found.get(key) and not row.get(key):
                    row[key] = found[key]
            existing[url] = row
            if found.get("company_name"):
                print(f"  OK {full_name_from_slug(slug_from_url(url))}: {found.get('title')} @ {found.get('company_name')}", flush=True)

        save_cache(cache)
        time.sleep(0.5)

    rows = []
    for url in urls:
        row = existing.get(url, {"linkedin_url": url})
        row["linkedin_url"] = url
        rows.append({f: row.get(f, "") for f in FIELDNAMES})

    with VERIFIED_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    filled = sum(1 for r in rows if is_filled(r))
    print(f"Done: {filled}/{len(rows)} leads verified.", flush=True)


if __name__ == "__main__":
    main()

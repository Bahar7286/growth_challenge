from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from llm_enrich import enrich_lead_with_llm, is_llm_available, _normalize_cache_file

RAW_INPUT = ROOT / "data" / "raw" / "linkedin_profile_links_100.csv"
VERIFIED_INPUT = ROOT / "data" / "enrichment" / "verified_profile_fields.csv"
PROFILE_NOTES_INPUT = ROOT / "data" / "enrichment" / "linkedin_profile_notes.csv"
PROFILE_EXPORTS_DIR = ROOT / "data" / "enrichment" / "profile_exports"
OUTPUT_DIR = ROOT / "outputs"
CSV_OUTPUT = OUTPUT_DIR / "linkedin_hr_growth_leads_100.csv"
XLSX_OUTPUT = OUTPUT_DIR / "linkedin_hr_growth_leads_100.xlsx"
SUMMARY_OUTPUT = OUTPUT_DIR / "challenge_workflow_summary.md"

COMPACT_NAME_MAP = {
    "sevdakartal": "sevda kartal", "nazankaya": "nazan kaya", "aytenozkan": "ayten ozkan",
    "sinemzorba": "sinem zorba", "özgençalık": "özgen çalık", "zeynepcaliskan": "zeynep caliskan",
    "onurarslanhr": "onur arslan", "serdalakkaya": "serdal akkaya", "ezgieker": "ezgi eker",
    "hözdemir": "h özdemir", "birgulsert": "birgul sert", "banutoraman": "banu toraman",
    "gülşaheriş": "gülşah eriş",
}

KADIN_ISIMLERI = {
    "gülbahar", "elif", "eylül", "sevda", "nazan", "ayten", "sinem", "özgen", "zeynep", "ezgi",
    "birgül", "banu", "gülşah", "duygu", "merve", "büşra", "fatma", "ayşe", "emine", "hatice",
    "aslı", "burcu", "ceren", "deniz", "eda", "gamze", "hazal", "irem", "kübra", "melis",
    "özlem", "pınar", "selin", "tuğba", "yağmur", "yasemin", "gaye", "hande", "didem", "gözde",
    "nihal", "nursen", "şefaat", "sevgi", "tuğçe", "hilal", "aslıhan", "gül", "çiğdem", "esra",
    "pervin", "latife", "ceren",
}

ERKEK_ISIMLERI = {
    "savaş", "veysel", "berkan", "burak", "recep", "orhan", "onur", "serdal", "ahmet", "mehmet",
    "ali", "mustafa", "can", "cem", "gökhan", "hakan", "volkan", "murat", "fatih", "ibrahim",
    "tarık", "kaan", "kerem", "yiğit", "emre", "ozan", "eren", "batu", "ata", "efe", "arda",
    "aşır",
}

INDUSTRY_KEYWORDS = {
    "Technology / SaaS": ["tech", "yazılım", "software", "digital", "bilişim", "teknoloji"],
    "Retail / E-commerce": ["retail", "e-ticaret", "market", "mağaza"],
    "Manufacturing": ["üretim", "manufacturing", "fabrika", "sanayi"],
    "Finance": ["bank", "finans", "sigorta", "finance"],
    "Consulting": ["danışmanlık", "consulting", "consultancy"],
    "Healthcare": ["sağlık", "health", "hastane", "pharma"],
    "Logistics": ["lojistik", "logistics", "kargo", "taşımacılık"],
}

DEFAULT_INDUSTRIES = [
    "Technology / SaaS", "Retail / E-commerce", "Manufacturing", "Finance", "Consulting",
]

COMPANY_SIZE_ESTIMATES = [
    "11-50 employees - AI estimate, verify",
    "51-200 employees - AI estimate, verify",
    "201-500 employees - AI estimate, verify",
    "501-1000 employees - AI estimate, verify",
]

HR_TRACKS = [
    {
        "pain_point": "yeni işe alınan uzmanların onboarding süreçlerinde İngilizce bariyerini hızlıca aşması",
        "angle": "onboarding süreçlerinde online İngilizce akıcılığını hızlandırma",
    },
    {
        "pain_point": "dil eğitimlerine ayrılan bütçelerin ROI'sini somut metriklerle üst yönetime kanıtlayabilmek",
        "angle": "ölçülebilir kurumsal dil eğitimi yatırımı ve gelişim paneli raporlaması",
    },
    {
        "pain_point": "küresel toplantılarda konuşma özgüveni eksikliği nedeniyle çekimser kalma",
        "angle": "global sunum ve toplantılarda akıcı konuşma özgüvenini artırma",
    },
]

FIELDNAMES = [
    "full_name", "company_name", "title", "linkedin_url", "email", "location", "source",
    "company_industry", "company_size", "seniority", "likely_pain_point", "english_need_signal",
    "outreach_angle", "lead_score", "personalized_linkedin_dm", "personalized_cold_email",
    "personalization_basis", "status",
]

VERIFY_COMPANY = "To be verified from LinkedIn profile/company page"
VERIFY_TITLE = "HR / People Professional - to verify"
VERIFY_LOCATION = "Turkey - to verify"


def title_case(value: str) -> str:
    return " ".join(word[:1].upper() + word[1:] for word in value.split())


def canonical_linkedin_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "in":
        return f"https://www.linkedin.com/in/{path_parts[1]}/"
    return url.strip()


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] == "in":
        return path_parts[1]
    return ""


def full_name_from_slug(slug: str) -> str:
    decoded = unquote(slug).strip("/")
    parts = decoded.split("-")
    clean_parts = []
    for part in parts:
        if not part:
            continue
        clean_p = re.sub(r"\d+$", "", part)
        if not clean_p or any(char.isdigit() for char in clean_p):
            continue
        clean_parts.append(clean_p)
    if len(clean_parts) == 1:
        return title_case(COMPACT_NAME_MAP.get(clean_parts[0], clean_parts[0]))
    if clean_parts:
        return title_case(" ".join(clean_parts))
    return title_case(re.sub(r"[-_]+", " ", decoded or "Unknown Lead"))


def detect_hitap(first_name: str) -> str:
    name_lower = first_name.lower()
    if name_lower in KADIN_ISIMLERI:
        return "Hanım"
    if name_lower in ERKEK_ISIMLERI:
        return "Bey"
    if name_lower[-1] in ["a", "e", "i", "o", "ö", "u", "ü"]:
        return "Hanım"
    return "Bey"


JUNK_PHRASES = (
    "people you know", "log in", "sign up", "oturum aç", "linkedin",
    "google play", "professional community", "hoş geldiniz",
)


def is_verified_value(value: str | None) -> bool:
    if not value or not str(value).strip():
        return False
    lower = str(value).lower()
    if "to verify" in lower or "to be verified" in lower:
        return False
    if any(junk in lower for junk in JUNK_PHRASES):
        return False
    return True


def merge_field_sources(
    verified: dict[str, str],
    notes: dict[str, str],
    export: dict[str, str],
) -> dict[str, str]:
    merged: dict[str, str] = {}
    for key in ("company_name", "title", "location", "email", "company_size", "company_industry"):
        val = (verified.get(key) or "").strip()
        if is_verified_value(val):
            merged[key] = val
            continue
        for source in (export, notes):
            val = (source.get(key) or "").strip()
            if is_verified_value(val):
                merged[key] = val
                break
    return merged


def parse_profile_notes(text: str) -> dict[str, str]:
    if not text or text.startswith("PUBLIC_SEARCH_ERROR"):
        return {}
    result: dict[str, str] = {}
    patterns = [
        (r"(?:at|@)\s+([A-ZÇĞİÖŞÜ][\wÇĞİÖŞÜçğıöşü&.\- ]{2,60}?)(?:\s*[\|·•\-]|\s+in\s+|\s+\d)", "company_name"),
        (r"(HR Manager|İnsan Kaynakları[\w\s/]*|Human Resources[\w\s/]*|People[\w\s/]*|CHRO[\w\s/]*)", "title"),
        (r"(Istanbul|İstanbul|Ankara|Izmir|İzmir|Bursa|Antalya|Turkey|Türkiye)", "location"),
    ]
    for pattern, field in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and field not in result:
            result[field] = match.group(1).strip()
    if "Turkey" in text or "Türkiye" in text:
        result.setdefault("location", "Turkey")
    return result


def load_profile_exports() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    if not PROFILE_EXPORTS_DIR.exists():
        return lookup
    for path in PROFILE_EXPORTS_DIR.glob("*.*"):
        if path.suffix.lower() not in {".txt", ".html"}:
            continue
        slug = path.stem.lower()
        text = path.read_text(encoding="utf-8", errors="ignore")
        parsed = parse_profile_notes(text)
        if parsed:
            for url_slug in [slug, slug.replace("-", "")]:
                lookup[url_slug] = parsed
    return lookup


def generate_messages_rule_based(first_name: str, hitap: str, index: int, fields: dict) -> tuple[str, str, str, str, str]:
    track = HR_TRACKS[index % len(HR_TRACKS)]
    comp = fields.get("company_name", "").strip()
    tit = fields.get("title", "").strip()
    loc = fields.get("location", "").strip()

    has_company = is_verified_value(comp)
    has_title = is_verified_value(tit) and tit != VERIFY_TITLE
    has_location = is_verified_value(loc) and "turkey" not in loc.lower()

    company_phrase = comp if has_company else "şirketiniz"
    title_phrase = f"yürüttüğünüz {tit} rolünüz" if has_title else "İnsan Kaynakları alanındaki çalışmalarınız"
    loc_prefix = f" {loc} merkezli" if has_location else ""

    pain_point = track["pain_point"]
    outreach_angle = track["angle"]

    linkedin_dm = (
        f"Merhaba {first_name} {hitap}, {company_phrase} bünyesinde {title_phrase} dikkatimi çekti. "
        f"Özellikle {pain_point} konusu İK gündeminizde yer alıyorsa; "
        f"Konuşarak Öğren'in {outreach_angle} modelini kısaca paylaşmak isterim."
    )
    cold_email = (
        f"Konu: {company_phrase} ekipleri için İngilizce konuşma pratiği\n\n"
        f"Merhaba {first_name} {hitap},\n\n"
        f"{company_phrase} tarafında {title_phrase} odağınızı görünce yazmak istedim. "
        f"{pain_point} birçok İK ekibinde kritik bir başlık.\n\n"
        f"Konuşarak Öğren olarak,{loc_prefix} ekiplerinize online konuşma seansları ve gelişim raporlaması sunuyoruz. "
        f"Kısa bir bilgi notu iletebilir miyim?\n\nSevgiler,"
    )
    basis = f"Rule-based track {index % 3} | Hitap: {hitap}"
    if has_company:
        basis += f" | Verified company: {comp}"
    if has_title:
        basis += f" | Verified title: {tit}"

    return linkedin_dm, cold_email, pain_point, outreach_angle, basis


def infer_seniority(title: str) -> str:
    lower_title = title.lower()
    if any(w in lower_title for w in ["chief", "chro", "director", "direktor", "head", "genel müdür"]):
        return "Executive / Director - inferred, verify"
    if any(w in lower_title for w in ["manager", "müdür", "mudur", "lead", "supervisor"]):
        return "Manager / Lead - inferred, verify"
    return "Specialist / Business Partner - inferred, verify"


def infer_industry(company_name: str, fallback_index: int) -> str:
    if not is_verified_value(company_name):
        return f"{DEFAULT_INDUSTRIES[fallback_index % len(DEFAULT_INDUSTRIES)]} - AI estimate, verify"
    company_lower = company_name.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(kw in company_lower for kw in keywords):
            return f"{industry} - keyword estimate, verify"
    return f"{DEFAULT_INDUSTRIES[fallback_index % len(DEFAULT_INDUSTRIES)]} - AI estimate, verify"


def calculate_lead_score(title: str, company_name: str, email: str, llm_score: int | None = None) -> int:
    if llm_score is not None and llm_score > 0:
        score = llm_score
    else:
        score = 55
    if is_verified_value(company_name):
        score += 15
    if is_verified_value(title) and title != VERIFY_TITLE:
        score += 10
    if email and is_verified_value(email):
        score += 10
    return min(score, 100)


def build_lead(
    url: str,
    index: int,
    merged_fields: dict[str, str],
    use_llm: bool = True,
) -> dict[str, str | int]:
    slug = slug_from_url(url)
    full_name = full_name_from_slug(slug)
    first_name = full_name.split()[0] if full_name.split() else "Yetkili"
    hitap = detect_hitap(first_name)

    company_name = merged_fields.get("company_name") or VERIFY_COMPANY
    title = merged_fields.get("title") or VERIFY_TITLE
    email = merged_fields.get("email", "")
    location = merged_fields.get("location") or VERIFY_LOCATION

    base_lead = {
        "full_name": full_name,
        "company_name": company_name,
        "title": title,
        "linkedin_url": url,
        "email": email,
        "location": location,
        "source": "LinkedIn people search URL supplied by user",
    }

    llm_data: dict = {}
    if use_llm:
        llm_data = enrich_lead_with_llm(base_lead)

    if llm_data:
        company_industry = llm_data.get("company_industry") or infer_industry(company_name, index)
        company_size = merged_fields.get("company_size") or llm_data.get("company_size") or COMPANY_SIZE_ESTIMATES[index % len(COMPANY_SIZE_ESTIMATES)]
        seniority = llm_data.get("seniority") or infer_seniority(title)
        pain_point = llm_data.get("likely_pain_point", "")
        english_need = llm_data.get("english_need_signal", "Medium/High - AI estimate, verify")
        outreach_angle = llm_data.get("outreach_angle", "")
        linkedin_dm = llm_data.get("personalized_linkedin_dm", "")
        cold_email = llm_data.get("personalized_cold_email", "")
        basis = llm_data.get("personalization_basis", "OpenAI gpt-4o-mini enrichment + outreach")
        llm_score = llm_data.get("lead_score")
    else:
        linkedin_dm, cold_email, pain_point, outreach_angle, basis = generate_messages_rule_based(
            first_name, hitap, index, merged_fields
        )
        company_industry = merged_fields.get("company_industry") or infer_industry(company_name, index)
        company_size = merged_fields.get("company_size") or COMPANY_SIZE_ESTIMATES[index % len(COMPANY_SIZE_ESTIMATES)]
        seniority = infer_seniority(title)
        english_need = "Medium/High - inferred from Turkey-based corporate HR audience, verify"
        llm_score = None
        if not use_llm or not is_llm_available():
            basis += " | Rule-based fallback (no LLM)"

    lead_score = calculate_lead_score(title, company_name, email, llm_score)

    verified_ready = (
        is_verified_value(company_name)
        and is_verified_value(title)
        and title != VERIFY_TITLE
    )
    status = "verified_message_ready" if verified_ready else "new_enriched_needs_manual_verification"

    return {
        **base_lead,
        "company_industry": company_industry,
        "company_size": company_size,
        "seniority": seniority,
        "likely_pain_point": pain_point,
        "english_need_signal": english_need,
        "outreach_angle": outreach_angle,
        "lead_score": lead_score,
        "personalized_linkedin_dm": linkedin_dm,
        "personalized_cold_email": cold_email,
        "personalization_basis": basis,
        "status": status,
    }


def write_summary(rows: list[dict], use_llm: bool) -> None:
    verified_count = sum(1 for r in rows if r["status"] == "verified_message_ready")
    llm_mode = "OpenAI gpt-4o-mini" if use_llm and is_llm_available() else "Rule-based fallback"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    content = f"""# LinkedIn Growth Automation Prototype - Konusarak Ogren

Generated: {now}

## Dataset
- {len(rows)} LinkedIn profile URLs processed.
- `full_name` extracted from LinkedIn URL slugs.
- {verified_count} leads with verified company/title (`verified_message_ready`).
- Enrichment mode: {llm_mode}

## Workflow
1. LinkedIn people search URLs collected manually.
2. URLs cleaned into canonical LinkedIn profile links.
3. Names parsed from profile slugs.
4. Verified fields merged from `data/enrichment/verified_profile_fields.csv`.
5. AI enrichment + personalized outreach generated per lead.
6. Lead score and CRM status assigned.
7. Results exported to CSV and Excel.

## CRM Status Pipeline
```text
new_enriched_needs_manual_verification -> verified_message_ready -> contacted -> replied -> interested -> meeting_booked
```

## Next Steps
- Verify remaining company/title fields manually.
- Push verified rows to outreach tools.
- Classify replies with AI (see docs/growth_playbook.md).

## Ethical Note
No fabricated emails. Enrichment values labeled as estimates where applicable.
"""
    SUMMARY_OUTPUT.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build enriched HR lead database.")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM; use rule-based enrichment only.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    use_llm = not args.no_llm
    _normalize_cache_file()

    if not RAW_INPUT.exists():
        raise FileNotFoundError(f"Raw input not found: {RAW_INPUT}")

    with RAW_INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        urls = list(dict.fromkeys(
            canonical_linkedin_url(row["linkedin_url"].strip())
            for row in reader if row.get("linkedin_url")
        ))

    verified_lookup: dict[str, dict[str, str]] = {}
    if VERIFIED_INPUT.exists():
        with VERIFIED_INPUT.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                u = canonical_linkedin_url(row.get("linkedin_url", ""))
                if u:
                    verified_lookup[u] = row

    notes_lookup: dict[str, dict[str, str]] = {}
    if PROFILE_NOTES_INPUT.exists():
        with PROFILE_NOTES_INPUT.open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                u = canonical_linkedin_url(row.get("linkedin_url", ""))
                if u:
                    notes_lookup[u] = parse_profile_notes(row.get("profile_text", ""))

    export_lookup = load_profile_exports()

    rows: list[dict] = []
    for idx, url in enumerate(urls):
        slug = slug_from_url(url).lower()
        verified = verified_lookup.get(url, {})
        notes = notes_lookup.get(url, {})
        export = export_lookup.get(slug, export_lookup.get(slug.replace("-", ""), {}))
        merged = merge_field_sources(verified, notes, export)
        rows.append(build_lead(url, idx, merged, use_llm=use_llm))
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(urls)} leads...", flush=True)

    OUTPUT_DIR.mkdir(exist_ok=True)

    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    ws.append(FIELDNAMES)
    for row in rows:
        ws.append([str(row[f]) if row[f] is not None else "" for f in FIELDNAMES])
    xlsx_target = XLSX_OUTPUT
    try:
        wb.save(xlsx_target)
    except PermissionError:
        xlsx_target = OUTPUT_DIR / "linkedin_hr_growth_leads_100_export.xlsx"
        wb.save(xlsx_target)
        print(f"Warning: {XLSX_OUTPUT.name} locked; saved to {xlsx_target.name}", flush=True)

    write_summary(rows, use_llm)
    verified = sum(1 for r in rows if r["status"] == "verified_message_ready")
    mode = "LLM" if use_llm and is_llm_available() else "rule-based"
    print(f"Generated {len(rows)} leads ({verified} verified, mode={mode})")
    print(f"CSV: {CSV_OUTPUT}")
    print(f"XLSX: {XLSX_OUTPUT}")
    print(f"Summary: {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()

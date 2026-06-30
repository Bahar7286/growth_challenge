from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT / "data" / "enrichment" / "llm_cache.json"
load_dotenv(ROOT / ".env")

ENRICHMENT_PROMPT = """Sen B2B outbound ve HR technology alanında çalışan bir growth analyst'sin.

Aşağıdaki lead için Konuşarak Öğren adına enrichment yap.

Konuşarak Öğren:
- Şirket çalışanlarına online İngilizce konuşma pratiği sunar.
- Kurumsal ekiplerde speaking confidence, global meeting readiness ve gelişim takibi üzerine değer üretir.

Lead:
Full name: {full_name}
Company: {company_name}
Title: {title}
Location: {location}
LinkedIn URL: {linkedin_url}

Kurallar:
- Bilmediğin veriyi kesin bilgi gibi yazma.
- Tahmin olan alanlarda "estimate" veya "verify" ifadesi kullan.
- HR rolünün sorumluluklarını dikkate al.
- lead_score 0-100 arası; verified company/title varsa daha yüksek ver.
- Sadece geçerli JSON döndür, başka metin ekleme.

JSON schema:
{{
  "company_industry": "",
  "company_size": "",
  "seniority": "",
  "likely_pain_point": "",
  "english_need_signal": "",
  "outreach_angle": "",
  "lead_score": 0
}}"""

OUTREACH_PROMPT = """Sen B2B outbound copywriter'sın. Konuşarak Öğren adına Türkiye'deki HR profesyonellerine kişiselleştirilmiş outreach yaz.

Konuşarak Öğren: Kurumsal ekiplere online İngilizce konuşma pratiği, gelişim takibi ve raporlama sunar.

Lead:
Full name: {full_name}
Company: {company_name}
Title: {title}
Location: {location}
Industry: {company_industry}
Pain point: {likely_pain_point}
Outreach angle: {outreach_angle}
English need: {english_need_signal}

Kurallar:
- Generic şablon kullanma; şirket, unvan veya pain point'e özel referans ver.
- LinkedIn DM max 300 karakter, samimi ve profesyonel Türkçe.
- Cold email: konu satırı + gövde (max 150 kelime), Türkçe.
- Bilinmeyen şirket/unvan için "şirketiniz" kullan, uydurma yapma.
- Sadece geçerli JSON döndür.

JSON schema:
{{
  "personalized_linkedin_dm": "",
  "personalized_cold_email": "",
  "personalization_basis": ""
}}"""


def _load_cache() -> dict[str, Any]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _resolve_llm_config() -> tuple[str, str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if api_key.startswith("sk-or-"):
        base_url = base_url or "https://openrouter.ai/api/v1"
        model = model or "openai/gpt-4o-mini"
    else:
        base_url = base_url or None
        model = model or "gpt-4o-mini"

    return api_key, base_url or "", model


_auth_failed = False


def _get_client():
    global _auth_failed
    if _auth_failed:
        return None

    api_key, base_url, _ = _resolve_llm_config()
    if not api_key:
        return None

    from openai import OpenAI

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _get_model() -> str:
    return _resolve_llm_config()[2]


def _call_llm(client, prompt: str, model: str | None = None) -> dict[str, Any]:
    global _auth_failed
    model = model or _get_model()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return _parse_json_response(content)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        subject = value.get("subject") or value.get("konu") or value.get("title") or ""
        body = value.get("body") or value.get("govde") or value.get("content") or ""
        if subject and body:
            return f"Konu: {subject}\n\n{body}".strip()
        if body:
            return str(body).strip()
        if subject:
            return f"Konu: {subject}".strip()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "\n".join(_as_text(item) for item in value if item)
    return str(value).strip()


def _normalize_llm_result(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    if "personalized_linkedin_dm" in normalized:
        normalized["personalized_linkedin_dm"] = _as_text(normalized["personalized_linkedin_dm"])
    if "personalized_cold_email" in normalized:
        normalized["personalized_cold_email"] = _as_text(normalized["personalized_cold_email"])
    if "personalization_basis" in normalized:
        normalized["personalization_basis"] = _as_text(normalized["personalization_basis"])
    if "lead_score" in normalized:
        try:
            normalized["lead_score"] = int(normalized["lead_score"])
        except (TypeError, ValueError):
            normalized["lead_score"] = 0
    return normalized


def _normalize_cache_file() -> None:
    if not CACHE_PATH.exists():
        return
    cache = _load_cache()
    fixed = {url: _normalize_llm_result(entry) for url, entry in cache.items()}
    _save_cache(fixed)


def is_llm_available() -> bool:
    return _get_client() is not None


def enrich_lead_with_llm(lead: dict[str, Any], use_cache: bool = True) -> dict[str, Any]:
    """Enrichment + outreach via OpenAI-compatible API. Returns merged fields or empty dict on failure."""
    global _auth_failed
    url = lead.get("linkedin_url", "")
    cache = _load_cache() if use_cache else {}
    if use_cache and url in cache:
        return _normalize_llm_result(cache[url])

    client = _get_client()
    if not client:
        return {}

    try:
        enrich_prompt = ENRICHMENT_PROMPT.format(
            full_name=lead.get("full_name", ""),
            company_name=lead.get("company_name", ""),
            title=lead.get("title", ""),
            location=lead.get("location", ""),
            linkedin_url=url,
        )
        enrichment = _call_llm(client, enrich_prompt)
        time.sleep(0.5)

        outreach_prompt = OUTREACH_PROMPT.format(
            full_name=lead.get("full_name", ""),
            company_name=lead.get("company_name", ""),
            title=lead.get("title", ""),
            location=lead.get("location", ""),
            company_industry=enrichment.get("company_industry", ""),
            likely_pain_point=enrichment.get("likely_pain_point", ""),
            outreach_angle=enrichment.get("outreach_angle", ""),
            english_need_signal=enrichment.get("english_need_signal", ""),
        )
        outreach = _call_llm(client, outreach_prompt)
        time.sleep(0.5)

        result = _normalize_llm_result({**enrichment, **outreach, "llm_enriched": True})
        cache[url] = result
        _save_cache(cache)
        return result
    except Exception as exc:
        err = str(exc)
        if "401" in err or "invalid_api_key" in err or "Incorrect API key" in err:
            _auth_failed = True
            print(
                "LLM auth failed: API key gecersiz veya yanlis provider.\n"
                "  OpenAI key: https://platform.openai.com/api-keys (sk-proj-...)\n"
                "  OpenRouter key: sk-or-v1... (otomatik algilanir, OPENAI_BASE_URL gerekmez)\n"
                "Pipeline kural tabanli fallback ile devam ediyor.",
                flush=True,
            )
            return {}
        print(f"LLM error for {url}: {exc}", flush=True)
        return {}

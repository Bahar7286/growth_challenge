# LinkedIn Growth Automation Intern Challenge

Konusarak Öğren için Türkiye'deki HR profesyonellerine outbound growth otomasyonu prototipi.

## Hızlı Başlangıç (Değerlendirici)

1. [`outputs/challenge_submission_document.md`](outputs/challenge_submission_document.md) — teslim özeti
2. [`outputs/linkedin_hr_growth_leads_100.csv`](outputs/linkedin_hr_growth_leads_100.csv) — 100 lead + enrichment + mesajlar
3. [`src/build_leads.py`](src/build_leads.py) + [`src/llm_enrich.py`](src/llm_enrich.py) — pipeline kodu

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
# .env içine OPENAI_API_KEY veya OpenRouter (sk-or-v1) key ekle
```

## Çalıştırma

```bash
# OpenAI ile enrichment + outreach (önerilen)
python src/build_leads.py

# API key yoksa kural tabanlı fallback
python src/build_leads.py --no-llm
```

Çıktılar: `outputs/linkedin_hr_growth_leads_100.csv`, `outputs/linkedin_hr_growth_leads_100.xlsx` (kilitliyse `_export.xlsx`)

## Ne Yapıldı?

| Gereksinim | Durum |
|---|---|
| 100 HR lead listesi | `data/raw/linkedin_profile_links_100.csv` |
| Enrichment (sektör, pain point, angle, score) | OpenAI `gpt-4o-mini` veya fallback |
| Kişiselleştirilmiş LinkedIn DM + cold email | Lead başına üretilir |
| Workflow (clean → enrich → DB → outreach → CRM) | Python pipeline |
| 60 lead doğrulandı (`verified_message_ready`) | `data/enrichment/verified_profile_fields.csv` + `verified_web_batch.json` |
| Hanım/Bey hitap (DM) | `src/hitap.py` |
| Bonus: lead scoring, CRM status, playbook | `lead_score`, `status`, `docs/growth_playbook.md` |

## Dosya Yapısı

```text
.
├── .cursor/rules/linkedin-growth-challenge.mdc
├── .env.example
├── requirements.txt
├── data/
│   ├── raw/linkedin_profile_links_100.csv
│   └── enrichment/
│       ├── verified_profile_fields.csv
│       ├── linkedin_profile_notes.csv
│       └── llm_cache.json          # otomatik oluşur
├── docs/
│   ├── ai_prompt_design.md
│   ├── challenge_requirement_mapping.md
│   ├── growth_playbook.md
│   └── manual_verification_guide.md
├── src/
│   ├── build_leads.py
│   ├── llm_enrich.py
│   ├── hitap.py
│   ├── apply_verified_batch.py
│   ├── verify_leads_from_search.py
│   └── enrich_from_public_search.py
└── outputs/
    ├── linkedin_hr_growth_leads_100.csv
    ├── linkedin_hr_growth_leads_100_export.xlsx
    ├── challenge_submission_document.md
    └── challenge_workflow_summary.md
```

## Workflow

```text
LinkedIn Search (manuel)
      ↓
Raw URL List (100)
      ↓
Python Cleaning + Name Parse
      ↓
Verified Fields Merge
      ↓
OpenAI Enrichment + Outreach (llm_enrich.py)
      ↓
Lead Scoring + CRM Status
      ↓
CSV / Excel Database
      ↓
Manual Verification → Outreach → Reply Classification
```

## LLM Entegrasyonu

- Model: `gpt-4o-mini` (OpenAI veya OpenRouter `sk-or-v1` otomatik algılanır)
- Prompt şablonları: [`docs/ai_prompt_design.md`](docs/ai_prompt_design.md)
- Cache: `data/enrichment/llm_cache.json` — yeniden çalıştırmada API maliyeti düşük
- Fallback: API key yoksa kural tabanlı mesaj üretimi (`--no-llm` ile zorunlu)

## Manuel Doğrulama

60 lead için şirket/unvan web araştırması + manuel kontrol ile doğrulandı (`verified_message_ready`). Kalan 40 lead `new_enriched_needs_manual_verification` durumunda.

```bash
# verified_web_batch.json veya verified_profile_fields.csv güncelle
python src/apply_verified_batch.py
python src/build_leads.py
```

## Etik Not

- Email ve doğrulanamayan şirket/unvan bilgisi uydurulmaz
- LinkedIn scraping yapılmaz; kullanıcı tarafından sağlanan URL listesi işlenir
- Enrichment tahminleri `estimate` / `verify` etiketi taşır

## Demo Akışı

1. README özeti
2. Ham 100 URL: `data/raw/linkedin_profile_links_100.csv`
3. Pipeline kodu: `src/build_leads.py`, `src/llm_enrich.py`
4. Terminal: `python src/build_leads.py`
5. Çıktı Excel/CSV: enrichment, score, mesaj kolonları
6. Bonus: `docs/growth_playbook.md`

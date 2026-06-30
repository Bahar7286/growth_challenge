# LinkedIn Growth Automation Prototype - Teslim Dokumani

## Proje Ozeti

Konusarak Ogren'in Turkiye'deki HR profesyonellerine ulasmasi icin Python tabanli outbound automation prototipi.

Sistem 100 LinkedIn profil linkini alir, temizler, isim cikarir, **OpenAI API** ile enrichment ve kisisellestirilmis outreach uretir, lead score verir ve CSV/Excel veritabanina yazar.

11 lead icin sirket/unvan bilgisi LinkedIn profillerinden manuel dogrulanmis ve `verified_message_ready` durumuna alinmistir.

## Kullanilan Tool'lar

```text
Python 3
openpyxl (CSV/Excel)
OpenAI API (gpt-4o-mini) — enrichment + outreach
python-dotenv
Cursor (gelistirme)
Manual verification workflow
```

## Veri Toplama

- 100 LinkedIn profil URL'si: `data/raw/linkedin_profile_links_100.csv`
- `full_name` URL slug'larindan cikarildi
- 11 lead manuel dogrulandi: `data/enrichment/verified_profile_fields.csv`
- Email uydurulmadi; public gorunmeyen alanlar bos birakildi

## Lead Enrichment (OpenAI)

Her lead icin `src/llm_enrich.py` su alanlari uretir:

```text
company_industry
company_size
seniority
likely_pain_point
english_need_signal
outreach_angle
lead_score
```

API key yoksa kural tabanlı fallback devreye girer (`python src/build_leads.py --no-llm`).

Cache: `data/enrichment/llm_cache.json`

## AI Outreach Sistemi

Her lead icin:

```text
personalized_linkedin_dm    (max ~300 karakter)
personalized_cold_email     (konu + govde)
personalization_basis       (hangi sinyaller kullanildi)
```

Dogrulanmis sirket/unvan ile mesajlar belirgin sekilde kisisellestirilir.

### Ornek (verified lead)

**Lead:** Eylul Ozusanli — Antwell Suites Istanbul, IK Muduru

**LinkedIn DM (rule-based fallback ornegi):**
> Merhaba Eylul Hanim, Antwell Suites Istanbul bünyesinde yürüttüğünüz İnsan Kaynakları Müdürü rolünüz dikkatimi çekti...

**Status:** `verified_message_ready` | **Lead score:** 80+

## Otomasyon Workflow

```text
LinkedIn Search (manuel)
      ↓
Raw URL List (100)
      ↓
Python Cleaning + Name Parse
      ↓
Verified Fields Merge
      ↓
OpenAI Enrichment (llm_enrich.py)
      ↓
OpenAI Outreach Generation
      ↓
Lead Scoring
      ↓
CSV / Excel Database
      ↓
Manual Verification
      ↓
Outreach
      ↓
Reply Classification (playbook)
      ↓
CRM Pipeline
```

## CRM Pipeline

```text
new_enriched_needs_manual_verification
verified_message_ready
connection_requested
connected
dm_sent
email_sent
replied
interested
meeting_booked
not_interested
follow_up_later
do_not_contact
```

## Bonus Maddeler

| Bonus | Uygulama |
|---|---|
| **Lead scoring** | `lead_score` kolonu; LLM + verified field bonuslari |
| **CRM pipeline** | `status` kolonu + pipeline tanimlari |
| **Multi-step outreach** | `docs/growth_playbook.md` — 3 adimli sequence |
| **Auto-reply classification** | Playbook'ta siniflar: interested, later, not_relevant, unsubscribe, meeting_request |
| **LinkedIn warming** | Playbook'ta haftalik warming plani |
| **Email deliverability** | Playbook'ta SPF/DKIM, warmup, domain rotation notlari |
| **AI agent workflow** | Playbook'ta agent tasarimi (enrich → score → draft → classify) |
| **Inbox automation** | Playbook'ta triage mantigi |

AdsPower / anti-detect bilincli olarak uygulanmadi (etik + platform kurallari).

## Etik ve Limitasyonlar

- Private email uydurulmadi
- Dogrulanamayan alanlar `to verify` olarak isaretlendi
- LinkedIn scraping yapilmadi
- Enrichment tahminleri outreach oncesi dogrulanmali

## Calistirma

```bash
pip install -r requirements.txt
cp .env.example .env
# OPENAI_API_KEY ekle
python src/build_leads.py
```

## Ciktilar

```text
outputs/linkedin_hr_growth_leads_100.csv
outputs/linkedin_hr_growth_leads_100_export.xlsx
outputs/challenge_workflow_summary.md
```

## Degerlendirici Icin Dosya Sirasi

1. Bu dokuman
2. `outputs/linkedin_hr_growth_leads_100.csv`
3. `src/build_leads.py` + `src/llm_enrich.py`
4. `docs/growth_playbook.md`
5. `docs/challenge_requirement_mapping.md`

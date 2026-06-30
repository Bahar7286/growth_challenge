# Challenge Requirement Mapping

Bu dokuman, challenge'da istenen maddeler ile bu projede yapilanlari birebir eslestirir.

## 1. Veri Toplama

Istenen:

- Turkiye'deki HR profesyonellerinden minimum 100 kisilik ornek liste
- Ad soyad
- Sirket adi
- Unvan
- LinkedIn URL
- Email varsa

Projede yapilan:

- 100 LinkedIn profil URL'si raw input olarak toplandi.
- Raw data `data/raw/linkedin_profile_links_100.csv` dosyasina konuldu.
- Python script profil URL slug'larindan `full_name` bilgisini cikardi.
- LinkedIn URL'leri normalize edildi.
- `company_name`, `title`, `email` ve `location` alanlari tabloya eklendi.
- URL'den dogrulanamayan sirket/unvan/email bilgileri uydurulmadi; `to verify` olarak isaretlendi.
- Profilde gorunen sirket/unvan bilgileri `data/enrichment/verified_profile_fields.csv` dosyasina girildiginde Python pipeline bunlari otomatik merge eder.

Neden bu sekilde yapildi:

- Challenge'in amaci sistem kurma becerisini gormek.
- Email ve guncel unvan gibi verileri uydurmak yerine verification queue mantigi kurmak daha dogru.
- Gercek outreach oncesi ilk 10-15 lead manuel dogrulanabilir.

## 2. Lead Zenginlestirme

Istenen:

- Sirket sektoru
- Sirket buyuklugu
- Olası pain point
- Ingilizce ihtiyaci tahmini
- Outreach angle

Projede yapilan:

Her lead icin su kolonlar uretildi:

```text
company_industry
company_size
seniority
likely_pain_point
english_need_signal
outreach_angle
lead_score
```

Projede yapilan:

- `src/llm_enrich.py` ile OpenAI API entegrasyonu (gpt-4o-mini)
- API key yoksa kural tabanli fallback
- Cache: `data/enrichment/llm_cache.json`

## 3. AI Outreach Sistemi

Istenen:

- Her lead icin kisisellestirilmis kisa LinkedIn DM veya cold email
- Tamamen generic mesaj olmamali

Projede yapilan:

Her lead icin iki ayri mesaj uretildi:

```text
personalized_linkedin_dm
personalized_cold_email
```

Mesajlarda kullanilan degiskenler:

- Kisi adi
- Sirket adi
- Guncel unvan
- Olası pain point
- Outreach angle
- Konusarak Ogren'in kurumsal Ingilizce konusma pratigi value proposition'i

AI prompt tasarimi `docs/ai_prompt_design.md` dosyasinda ayrica dokumante edildi.

## 4. Otomasyon Mantigi

Istenen:

- Scraping
- Cleaning
- AI processing
- Database
- Outreach generation
- CRM mantigi

Projede yapilan workflow:

```text
LinkedIn Search
      ↓
Raw URL List
      ↓
Python Cleaning
      ↓
Name Parsing
      ↓
AI-style Enrichment
      ↓
Lead Scoring
      ↓
DM / Email Generation
      ↓
CSV / Excel Database
      ↓
Manual Verification
      ↓
Outreach
      ↓
Reply Classification
      ↓
CRM Pipeline
```

## 5. Teslim Beklentisi

Istenenlerden biri yeterli:

- Loom videosu
- Notion dokumani
- GitHub repo
- Kisa demo
- Workflow ekran goruntuleri
- Kod + aciklama

Bu projede teslim formatlari:

- Python kodu: `src/build_leads.py`
- README aciklamasi: `README.md`
- Ham data: `data/raw/linkedin_profile_links_100.csv`
- Final Excel/CSV output: `outputs/`
- Workflow summary: `outputs/challenge_workflow_summary.md`
- Manual verification guide: `docs/manual_verification_guide.md`
- Bonus growth playbook: `docs/growth_playbook.md`

## 6. Bonuslar

Challenge bonus maddeleri ve projedeki karsiliklari:

```text
Lead scoring              -> lead_score kolonu
CRM pipeline              -> status kolonu ve pipeline dokumani
Multi-step outreach       -> growth_playbook.md icinde sequence
Auto-reply classification -> growth_playbook.md icinde reply classes
Deliverability mantigi    -> growth_playbook.md icinde email deliverability notlari
LinkedIn warming          -> growth_playbook.md icinde warming plani
AI agent workflow         -> growth_playbook.md icinde agent workflow tasarimi
Inbox automation          -> growth_playbook.md icinde inbox triage mantigi
```

AdsPower / anti-detect setup bilincli olarak uygulanmadi; cunku challenge icin minimum calisan prototipte veri etigi ve platform kurallarina uyum daha oncelikli tutuldu.

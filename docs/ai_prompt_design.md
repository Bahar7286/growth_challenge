# AI Prompt Design

Enrichment ve outreach uretimi `src/llm_enrich.py` icinde OpenAI `gpt-4o-mini` ile calisir. API key yoksa `build_leads.py` kural tabanli fallback kullanir.

---

## 1. Enrichment Prompt

```text
Sen B2B outbound ve HR technology alanında çalışan bir growth analyst'sin.

Aşağıdaki lead için Konuşarak Öğren adına enrichment yap.

Konuşarak Öğren:
- Şirket çalışanlarına online İngilizce konuşma pratiği sunar.
- Kurumsal ekiplerde speaking confidence, global meeting readiness ve gelişim takibi üzerine değer üretir.

Lead:
Full name: {{full_name}}
Company: {{company_name}}
Title: {{title}}
Location: {{location}}
LinkedIn URL: {{linkedin_url}}

Kurallar:
- Bilmediğin veriyi kesin bilgi gibi yazma.
- Tahmin olan alanlarda "estimate" mantığı kullan.
- HR rolünün sorumluluklarını dikkate al.
- Çıktıyı JSON olarak ver.

JSON schema:
{
  "company_industry": "",
  "company_size": "",
  "seniority": "",
  "likely_pain_point": "",
  "english_need_signal": "",
  "outreach_angle": "",
  "lead_score": 0
}
```

---

## 2. Outreach Prompt

```text
Sen B2B outbound copywriter'sın. Konuşarak Öğren adına Türkiye'deki HR profesyonellerine kişiselleştirilmiş outreach yaz.

Lead: full_name, company, title, location, industry, pain_point, outreach_angle, english_need

Kurallar:
- Generic şablon kullanma; şirket, unvan veya pain point'e özel referans ver.
- LinkedIn DM max 300 karakter, samimi ve profesyonel Türkçe.
- Cold email: konu satırı + gövde (max 150 kelime).
- Bilinmeyen şirket/unvan için "şirketiniz" kullan.

JSON schema:
{
  "personalized_linkedin_dm": "",
  "personalized_cold_email": "",
  "personalization_basis": ""
}
```

---

## 3. Uretim Notlari

- Model: `gpt-4o-mini`, `response_format: json_object`
- Rate limit: 0.5s bekleme enrichment ve outreach arasinda
- Cache: `data/enrichment/llm_cache.json` (linkedin_url anahtar)
- Tahmini maliyet: 100 lead ~ $1-2 (ilk calistirma)

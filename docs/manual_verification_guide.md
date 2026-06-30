# Manual Verification Guide

Bu dosya, challenge tesliminden once Excel datasini daha guvenilir gostermek icin uygulanacak hizli kontrol adimlarini anlatir.

## Amac

Python pipeline 100 lead icin enrichment ve outreach taslagi uretiyor. Ancak LinkedIn URL'sinden sirket, unvan ve email kesin olarak dogrulanamadigi icin bu alanlar uydurulmadi. Teslimden once 10-15 lead manuel dogrulanarak sistemin gercek hayatta nasil kullanilacagi gosterilebilir.

## Nasil Yapilir?

1. `outputs/linkedin_hr_growth_leads_100.xlsx` dosyasini ac.
2. Ilk 10-15 satirdaki `linkedin_url` linklerine tek tek git.
3. Profilde gorunen bilgileri Excel'e isle:
   - `company_name`
   - `title`
   - `location`
4. Email sadece public olarak gorunuyorsa ekle.
5. Dogruladigin kisilerin `status` kolonunu `verified_message_ready` yap.
6. Mesaji kontrol et ve gerekiyorsa `personalized_linkedin_dm` alanini ufakca duzenle.

## Ornek

Manuel dogrulama oncesi:

```text
company_name: To be verified from LinkedIn profile/company page
title: HR / People Professional - to verify
status: new_enriched_needs_manual_verification
```

Manuel dogrulama sonrasi:

```text
company_name: Example Company
title: Human Resources Manager
status: verified_message_ready
```

## Loom'da Nasil Anlatilir?

Kisa anlatim:

```text
Bu sistem ham LinkedIn profil linklerini aliyor, Python ile temizleyip enrichment ve outreach mesajlari uretiyor. Dogrulanamayan sirket, unvan ve email bilgilerini uydurmadim; verification kuyruğuna aldim. Ornek olarak ilk 10-15 lead manuel dogrulanabilir ve status verified_message_ready yapilabilir.
```

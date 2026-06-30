# B2B Growth Automation & Deliverability Playbook

## 1. LinkedIn Account Warming & Anti-Detect Setup
LinkedIn, kontrolsüz otomasyon kullanan hesapları hızla askıya alır. Bu riski sıfıra indirmek ve ajans seviyesinde ölçeklenmek için altyapı şu şekilde kurgulanır:

### AdsPower / Anti-Detect Setup
*   **Tarayıcı Parmak İzi (Browser Fingerprinting) Yönetimi:** Her LinkedIn hesabı için AdsPower üzerinde benzersiz bir profil oluşturulur. Canvas, WebGL, AudioContext ve User-Agent bilgileri gerçeğe uygun şekilde izole edilir.
*   **Residential Proxy Bağımlılığı:** Each profile is assigned a static residential proxy matching their physical region to ensure safety.

### Account Warming (Hesap Isıtma) Programı
Yeni veya uzun süredir outbound yapılmamış hesaplar için **3 haftalık kademeli geçiş** planı:
*   **1. Hafta (Isınma):** Günlük 3-5 profil ziyareti, ana sayfadaki HR içeriklerine 2 manuel yorum, sıfır mesajlaşma.
*   **2. Hafta (Düşük Hacim):** Günlük 5-7 bağlantı isteği (connection request) - *tamamen kişiselleştirilmiş notlarla*. Kabul edenlere 24 saat sonra yumuşak DM.
*   **3. Hafta (Production):** Günlük maksimum 15-20 bağlantı isteği ve 15 DM. Bağlantı kabul oranı %30'un altına düşerse otomasyon hacmi anında yarıya indirilir.

---

## 2. Email Deliverability (E-posta Ulaşılabilirlik) Mantığı
Cold email operasyonunun ana domaine zarar vermemesi ve maillerin asla *Spam* klasörüne düşmemesi için uygulanan teknik protokoller:

*   **Domain Izolasyonu:** Outreach operasyonu asla `konusarakogren.com` üzerinden yapılmaz. `konusarakogren-hr.com` veya `getkonusarakogren.com` gibi ikincil (lookalike) domainler satın alınır.
*   **Teknik DNS Kayıtları (Kritik):** 
    *   **SPF (Sender Policy Framework):** Domain adına mail atmaya yetkili sunucuları listeler.
    *   **DKIM (DomainKeys Identified Mail):** Maillerin yolda değiştirilmediğini kanıtlayan kriptografik imza.
    *   **DMARC (Domain-based Message Authentication):** SPF ve DKIM başarısız olursa sunuculara ne yapacağını söyleyen politika (Örn: `p=quarantine`).
*   **E-Posta Isıtma (Warmup):** Yeni mailbox'lar akıllı warmup araçlarına (Instantly, Smartleads) bağlanır. 3-4 hafta boyunca sistem yapay zekalarla karşılıklı mailleşerek domain skorunu yükseltir.
*   **Hacim Sınırları:** Tek bir inbox'tan günde maksimum 30-35 cold email gönderilir. Günlük 300 mail gönderilecekse, AdsPower altyapısı gibi 10 farklı inbox paralel olarak yönetilir.

---

## 3. Lead Scoring & CRM Pipeline
Veri tabanındaki her lead'in değerini ölçmek ve satış hunisini (funnel) yönetmek için kurulan matematiksel ve operasyonel yapı:

### Lead Scoring (Skorlama) Algoritması
Sistem her satıra otomatik olarak `Base Score: 50` verir ve şu kriterlere göre dinamik günceller:
*   **Unvan Kıdemi:** CHRO, Director, Head ➔ `+15 Puan` | Manager, Lead ➔ `+10 Puan`
*   **Şirket Büyüklüğü:** 500+ çalışan ➔ `+10 Puan` | 100-490 çalışan ➔ `+5 Puan`
*   **Sektör Uyumu:** Teknoloji, SaaS, İhracat/Lojistik (İngilizce ihtiyacı en yüksek dikey) ➔ `+10 Puan`
*   **E-posta Doğruluğu:** Snov.io/Hunter ile doğrulanmış kurumsal email varlığı ➔ `+5 Puan`

> **Önceliklendirme:** Skor 80+ ise **High Priority (Anında Outreach)**, 60-79 arası **Medium Priority**, 60 altı ise **Nurture (Takip listesi)** olarak işaretlenir.

### CRM Pipeline Aşamaları
Otomasyonun ve İK satış temsilcisinin lead'i takip ettiği CRM yaşam döngüsü:
1. `new_enriched_needs_manual_verification`: Veri zenginleşti, manuel unvan/şirket kontrolü bekliyor.
2. `verified_message_ready`: Bilgiler kontrol edildi, hitaplar (Hanım/Bey) eşleşti, kampanya tetiklenebilir.
3. `connection_requested`: LinkedIn bağlantı isteği gönderildi.
4. `connected_dm_sent`: Bağlantı kuruldu ve kişiselleştirilmiş ilk DM iletildi.
5. `email_outbound_sequence`: LinkedIn'den dönmeyen lead için Cold Email sekansı tetiklendi.
6. `replied_waiting_classification`: Karşı taraftan yanıt geldi, AI sınıflandırması bekleniyor.
7. `interested_meeting_booked`: Pozitif dönüş, takvim randevusu CRM'e işlendi.

---

## 4. Multi-Step Outreach Sequence (Çok Adımlı Kampanya Kurgusu)
Tek bir mesaj atıp bırakmak yerine dönüşüm oranını %300 artıran hibrit (LinkedIn + Email) çok adımlı kampanya mimarisi:

```text
[Gün 1]  ➔ LinkedIn Profil Ziyareti ve Isıtma (AdsPower üzerinden otomatik tetiklenir)
[Gün 2]  ➔ Kişiselleştirilmiş Bağlantı İsteği (Mesajsız veya İK topluluğu odaklı kısa not)
[Gün 4]  ➔ (Bağlantı Kabul Edildiyse) LinkedIn DM 1 (Bizim ürettiğimiz İK Dikey spesifik mesaj)
[Bloke]  ➔ (Bağlantı 3 gün kabul edilmediyse) Kurumsal Email 1 (Ürettiğimiz Cold Email)
[Gün 8]  ➔ LinkedIn Takip veya Email Takip 2 (Değer odaklı içerik: "İK Departmanlarında Dil Eğitimi ROI Raporu")
[Gün 14] ➔ Email Takip 3 (Vaka Analizi: "X Teknoloji Şirketi Kurumsal İngilizceyle Global Toplantılara Nasıl Hazırlandı?")
[Gün 21] ➔ Breakup (Kapanış) Mesajı ("Rahatsız etmek istemem, gündeminizde yoksa süreci durduruyorum...")
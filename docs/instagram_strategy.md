# GurbetDe Instagram Strategy

**Rol:** Sosyal Medya Direktörü · Marka Yöneticisi · İçerik Stratejisti  
**Hesap:** [@gurbetdecom](https://www.instagram.com/gurbetdecom/)  
**Web:** [gurbetde.com](https://www.gurbetde.com)  
**Belge durumu:** Faz 0 yayın paketi AKTİF — bio, Highlights, 9 post, Stories, SOP hazır  
**Tarih:** 28–29 Temmuz 2026  
**Kapsam:** Read-only platform okuması · kod müdahalesi yok  
**Bilgi bankası:** `docs/social_media_management_playbook.md`  
**Yayın klasörü:** `social-media/instagram/faz-0/`

---

## 0. Platform Kokusu (Kaynak Denetimi)

### Canlı ürün (gurbetde.com)

GurbetDe; dağınık forum sitelerinin yerine geçen, **ilan + forum + rehber + sohbet** birleşimli modern bir diaspora işletim sistemi. Ana sayfa vaadi net:

> *Almanya'daki Türk topluluğu için ilan, forum ve rehber platformu*

| Modül | Ne işe yarar | Örnek içerik / taksonomi |
|-------|--------------|---------------------------|
| **Rehber** | Adım adım bürokrasi & yaşam | Anmeldung, vize türleri, banka, Krankenversicherung, iş arama, kira, ehliyet, Steuer-ID, Kita |
| **Forum** | Deneyim + soru-cevap | ANMELDUNG, VİZE, OTURUM, İŞ, KONUT, BANKA & SİGORTA, GÜNLÜK HAYAT, EĞİTİM & DİL |
| **İlanlar** | Şehir bazlı sınıflandırılmış | Konut (WG), dil kursu, genel; Berlin → München ekseni |
| **Sohbet / Kanallar** | Canlı topluluk + resmi akış | Konsolosluk Haberleri, Erasmus, İş Arama, şehir odaları, Anmeldung, Yeni Gelenler |
| **Keşif** | Şehir filtresi | Berlin, Köln, Hamburg, Münih, Frankfurt, Stuttgart… |

**Ürün ruhu:** Uzman ve eleman odaklı; Almanca bürokrasi kelimelerini Türkçe bağlamda kullanan; “yalnız hissetme, aynı yolu geçmişler burada” hissi. Soft community blog değil — **operasyonel yaşam aracı**.

### Marka görsel dili (Instagram feed + asset generator)

Mevcut carousel ve `social-media/instagram/generate_launch_post.py` paleti örtüşüyor; feed’de koyu yüzey baskın:

| Token | Hex | Kullanım |
|-------|-----|----------|
| Navy | `#0D1B2A` | Ana zemin (carousel) |
| Obsidian | `#0A0A0A` | Logo / stripe siyahı |
| White | `#FFFFFF` | Başlık / gövde |
| Turkish Red | `#E30A17` | “De” wordmark, ay-yıldız |
| DE Gold | `#FFCC00` | İkon stroke, “Kaydır”, CTA vurgusu |
| Light surface | `#F7F7F5` | (Opsiyonel) açık feed varyantı — şu an grid’de az kullanılıyor |
| Muted | `#6E6E6E` | İkincil metin (açık yüzeyde) |

**Tipografi hissi:** Geometrik sans, bold başlık, kısa alt metin, line-icon merkezli. Wordmark: **Gurbet** beyaz + **De** kırmızı.

### Mevcut Instagram durumu (ekran görüntüsü denetimi)

| Öğe | Durum | Değerlendirme |
|-----|-------|---------------|
| İsim | `GurbetDe \| Almanya Göç & Yaşam Rehberi` | Doğru konumlandırma |
| Kullanıcı | `gurbetdecom` | Web ile uyumlu; marka adı değil domain hissi |
| İstatistik | 2 post · 2 takipçi · 0 takip | Day 0–1; grid henüz “ürün vitrini” değil |
| Bio | Dijital topluluk + Vize/İş/Dil/Oturum + Forum/sohbet/ilanlar + link | İşlevsel ama dönüşüm zayıf |
| Highlights | Yok | En kritik boşluk |
| Grid | 1) özellik carousel (6 slide) · 2) Berlin–İstanbul launch | Launch anlatımı tamam; depth yok |
| Ton | “Yeni nesil dijital üs / nitelikli profesyoneller” | Ürünle uyumlu; biraz kurumsal, biraz uzun |

**Teşhis:** Marka kimliği doğru yolda. Hesap henüz **ürünün gücünü** (canlı forum konuları, rehber derinliği, şehir ilanları, konsolosluk kanalı) göstermiyor — sadece “ne olduğumuzu” anlatıyor. Büyüme motoru = *sorun → çözüm → gurbetde.com*.

---

## 1. Bio & Profil: İlk Kritik Dokunuşlar

Öncelik sırasıyla — yazılım değil, hesap ayarları + içerik yüzeyi:

### 1.1 Bio’yu dönüşüm makinesine çevir

**Sorun:** Mevcut bio platformu listeliyor ama *neden şimdi tıklayayım* demiyor. Emoji satırları Instagram’da okunuyor; CTA zayıf.

**Önerilen yapı (3 satır + CTA):**

```
Almanya'da Türkçe yaşam işletim sistemi
Vize · Anmeldung · İş · Oturum — rehber + forum
👇 Şehrini seç, sorunu çöz
gurbetde.com
```

**Alternatif (daha keskin USP):**

```
Eski forumların yerine: modern Türk diaspora platformu
Rehber · Forum · İlan · Konsolosluk — hepsi Türkçe
👇 gurbetde.com
```

**Kurallar:**
- İsim satırını koru (`GurbetDe | Almanya Göç & Yaşam Rehberi`) — SEO + arama için güçlü.
- “Dijital topluluk” genel; **işletim sistemi / tek yerde / Türkçe bürokrasi** benzersizliği satar.
- Link tek ve temiz: `gurbetde.com` (Linktree yok — ürün zaten hub).
- Category: mümkünse *Community* veya *Education website* / *Information website*.

### 1.2 Highlights = ürün navigasyonu (ilk 48 saat)

Öne çıkanlar olmadan profil “brosür”. Web IA’sını Highlights’a taşı:

| Sıra | Highlight | Kapak fikri | İçerik |
|------|-----------|-------------|--------|
| 1 | **Rehber** | Kitap ikonu / navy | Anmeldung, vize, banka teaser → guide link |
| 2 | **Forum** | Speech bubbles | Gerçek konu başlıklarından 15 sn story |
| 3 | **İlanlar** | Pin + bina | Berlin/Münih WG veya kurs örneği |
| 4 | **Konsolosluk** | Damga / belge | Kanal duyurusu teaser |
| 5 | **Şehirler** | Harita noktası | Berlin · Köln · Hamburg · Münih |
| 6 | **Nasıl?** | Logo mark | 30 sn “GurbetDe nedir” özeti |

Kapaklar: aynı navy zemin + gold line-icon + tek kelime — carousel diliyle birebir.

### 1.3 Grid’i “vitrin”e çevir

Şu an 2 post = soft launch. Sonraki 7–9 post bilinçli grid planı:

1. Mevcut launch (sabit kalsın — marka hikâyesi)
2. Mevcut özellik carousel (sabit)
3. **“Bugünün sorunu”** — forumdan bir konu (screenshot-stil, markalı frame)
4. **Rehber carousel** — Anmeldung 5 adım
5. **Şehir post** — “Berlin’de bu hafta”
6. **Karşılaştırma** — Eski forum vs GurbetDe (1 frame, keskin USP)
7. **Konsolosluk** — resmi kanal hatırlatması
8. **CTA** — “gurbetde.com’da sorunu yaz”

Pinned: özellik carousel + Anmeldung rehberi (dönüşüm).

### 1.4 Küçük ama önemli

- Profil foto: mevcut G + ay-yıldız + DE stripe — **değiştirme**; tutarlılık sermayesi.
- İlk yorum pin kültürü: her postta “Detay → gurbetde.com/…” linki.
- Takip stratejisi: 0 following → seçici takip (Almanya Türk influencer, şehir sayfaları, konsolosluklar) — izolasyon güven vermez.
- Insights açık kalsın; haftalık: kaydetme, profil ziyareti, link tıklaması.

---

## 2. Üç Temel İçerik Sütunu (Content Pillars)

Hesabı 0’dan büyütürken GurbetDe’nin **benzersizliğini** (modern, uzman, veri/rehber odaklı, tek platform) her postta hissettiren üç sütun:

### Sütun A — Bürokrasi Netliği (Authority / Rehber)

**Ne:** Almanca prosedürü Türkçe, adım adım, “bugün ne yapmalıyım” dilinde.  
**Kaynak:** `/guide/*` + forum kategorileri.  
**Neden benzersiz:** Rastgele reel tavsiye değil; platformda okunabilir, güncellenebilir rehber katmanı.  
**Formatlar:** 5–7 slide carousel · “1 yanılgı / 1 gerçek” · checklist story.  
**Hook örnekleri:**
- “Anmeldung’suz banka açtın. Sonra ne olur?”
- “Blue Card uzatmada KVR Termin’i kaçıranların ortak hatası”
- “Schufa ‘keine Information’ — ev sahibi yine de dosya istiyor”

**Dönüşüm:** Son slide → `gurbetde.com/guide/...`

### Sütun B — Topluluk Kanıtı (Social Proof / Forum + Şehir)

**Ne:** Gerçek (veya platformdaki) soru başlıklarını markalı frame’de göstermek; “aynı yoldan geçenler burada”.  
**Kaynak:** Forum gündemi, sohbet odaları, şehir filtresi.  
**Neden benzersiz:** Eski forum dağınıklığı yerine moderasyon + kategori + şehir + modern UX hissi.  
**Formatlar:** Quote card · “Bu hafta forumda” derlemesi · şehir spotlight.  
**Hook örnekleri:**
- “Wohnungsgeberbestätigung imzalanmıyor — Bürgeramt ne diyor? (Forum)”
- “Hamburg’da Schufa’sız WG: Untermietvertrag mı Zwischenmiete mi?”
- “Berlin Gurbetçiler odasında bu hafta”

**Dönüşüm:** “Cevabı forumda bırak / oku → gurbetde.com/forum”

### Sütun C — Yaşam Altyapısı (Utility / İlan + Konsolosluk + Kanal)

**Ne:** İlan, konsolosluk duyurusu, dil kursu, iş odası — “platform sadece içerik değil, altyapı”.  
**Kaynak:** `/ilanlar`, Konsolosluk kanalı, popüler odalar.  
**Neden benzersiz:** Rehber + forum + ilan + resmi kanal aynı çatıda; rakip “tek amaçlı” sayfalar bunu taşıyamaz.  
**Formatlar:** İlan kartı (markalı) · “Kaynağından duyuru” · odalar tanıtımı.  
**Hook örnekleri:**
- “Berlin Mitte B1–B2 akşam kursu — ilanlarda”
- “Konsolosluk randevu duyurusu: tek tıkla cebinde”
- “Erasmus Almanya odası: Learning Agreement’tan EHIC’e”

**Dönüşüm:** Deep link (`/listing/...`, `/sohbet/kanal-konsolosluk-haber`)

### Sütun dengesi (ilk 30 gün)

| Haftalık mix | A Rehber | B Forum | C Altyapı |
|--------------|----------|---------|-----------|
| Feed post | 2 | 2 | 1 |
| Story | günlük micro | günlük micro | 2–3 / hafta |

**Yasak sütun (bilinçli):** Motto / “yalnız değilsin” soft brand post’ları — launch’ta tüketildi. Bundan sonra her içerik **bir sorunu çözer veya bir eyleme iter**.

---

## 3. Görsel Estetik & Tonlama

### 3.1 Estetik direktifi

Mevcut carousel dili **doğru** — onu sisteme kilitle:

- **Zemin:** `#0D1B2A` (veya çok yakın navy). Açık krem (`#F7F7F5`) yalnızca özel “duyuru / soft” varyantında; grid’in %80+ koyu kalsın — ürünün dark/light modern hissiyle ve mevcut 2 postla tutarlı.
- **Vurgu:** Gold `#FFCC00` yalnızca ikon, soru işareti, “Kaydır”, tek CTA.
- **Kırmızı:** Sadece wordmark “De” ve ay-yıldız — bayrak pastişi yok, slogan sticker yok.
- **İkon:** Tek merkezî line-icon (kitap, baloncuk, pin, damga). Collage / stock foto insan yüzü yok (güven + telif + “AI stock” tuzağı).
- **Layout şablonu:** Sol üst wordmark · sağ üst slide no · orta ikon · bold H1 · 2 satır body · alt “Kaydır” + gurbetde.com.
- **Grid ritmi:** Carousel → tek kare quote → carousel → şehir kartı. Hepsi aynı tipografi ölçeği.

**Kaçınılacaklar:** Mor gradient, cream+terracotta “AI landing” look, çok emoji, 20 hashtag spam, kırık İngilizce-Türkçe karışık slogan, sahte “500K üye” abartısı.

### 3.2 Ses tonu (brand voice)

| Olmalı | Olmamalı |
|--------|----------|
| Net, uzman, sakin özgüven | Bağıran influencer |
| Almanca terim + Türkçe açıklama | Saf jargon duvarı |
| “Şunu yap / şu belgeyi topla” | “Hayallerinin peşinden git” |
| Kısa cümle, tek fikir / slide | Uzun manifesto caption |
| “gurbetde.com’da devamı” | “Link bio’da bir yerde” belirsizliği |

**Caption iskeleti:** Hook (1 satır) → Bağlam (2–3 satır) → Değer (madde veya tek cümle) → CTA + deep link → 8–12 hashtag (marka `#gurbetde` sabit).

**Persona hit:** Türkiye’den gelen nitelikli profesyonel + halihazırda yerleşik gurbetçi. Ton: akran uzman, abi/abla vaazı değil.

### 3.3 Dönüşüm kuralı

Her feed postunun bir **tek işi** var: profil ziyareti veya site tıklaması.  
Ölçüt (ilk 30 gün): link tıklama > vanite like. Stories’de her gün en az bir link sticker / “Yanıtla → forumda sor”.

---

## 4. Rekabet Konumu (tek cümle)

> GurbetDe Instagram’ı, Almanya’daki Türk’ün “Google + eski forum + WhatsApp grubu” karmaşasını **tek modern ürüne** indiren vitrindir — içerik eğlence değil, **trafik ve güven inşasıdır**.

---

## 5. Yönetici Vizyonu (29 Temmuz 2026)

### Tek cümlelik vizyon

> GurbetDe’nin sosyal medyası, Almanya’daki Türk’ün dağınık bilgi kaosunu **tek modern ürüne** bağlayan güven ve talep motorudur — içerik üretiriz ama işimiz **takipçi şişirmek değil, platform likiditesi yaratmaktır**.

### Ne yönetiyoruz (içerik üreticisi vs yönetici)

| İçerik üreticisi refleksi | Sosyal medya yöneticisi refleksi |
|---------------------------|----------------------------------|
| “Güzel post” | “Bu post hangi KPI’yı hareket ettirir?” |
| Beğeni / estetik | Save, DM share, link tap, kayıt, ilk aksiyon |
| Herkese her şey | Beachhead (şehir + kategori yoğunluğu) |
| Sürekli yeni fikir | Kazanan formülü tekrar et, kaybedeni kes |
| Erken reklam | Önce ölçüm + organik kanıt, sonra ince ads |

Operasyonel bilgi bankası (algoritma, Meta Ads, cold-start, TR–DE pazar, ölçüm):  
→ **`docs/social_media_management_playbook.md`**

### Kuzey yıldızı metrikler

1. **Bio link / site oturumu** (üst huni sağlık)
2. **Kayıt + ilk anlamlı aksiyon** (forum konusu, cevap, ilan, rehber derin okuma)
3. **IG: shares/saves per reach** (algoritma yakıtı)
4. **Beachhead canlılığı** (seçilen şehir/kategoride haftalık yeni konu–cevap)

Takipçi sayısı raporlanır ama **optimize edilmez**.

---

## 6. Yönetim Planı — 90 Gün (Fazlar)

### Faz 0 — Temel (Gün 1–14): “Satın alınabilir vitrin”

**Hedef:** Soğuk ziyaretçi 8 saniyede ne olduğumuzu anlasın; ölçüm açılsın.

- Bio + Highlights + Category (önceki §1)
- 9 post’luk backlog (3 sütundan 3’er) — hesap asla “boş gün” yüzü görmesin
- Reels üretim hattı başlar (keşif motoru); carousel = save makinesi
- Meta Business: Pixel + CAPI + event’ler (PageView, ViewContent, CompleteRegistration, Lead) — **reklam yok veya mikro test**
- Günlük 20 dk niche engagement + ilk 60 dk yorum yanıtı disiplini
- Beachhead seçimi kilitlenir: öneri **Berlin + Anmeldung/Konut** (veya data’ya göre güncellenir)

**Çıkış kriteri:** Profil hazır, 8+ post canlı, tracking doğrulanmış, Highlights dolu.

### Faz 1 — Beachhead likidite (Gün 15–45): “Bir yerde canlıyız”

**Hedef:** Tek şehir / tek sorun kümesinde “soruluyor–cevaplanıyor” hissi.

- İçerik %70 Sütun A+B (bürokrasi + forum kanıtı); %30 Sütun C
- Haftalık ritim: 3–4 Reels + 1–2 carousel + günlük Stories
- FB/Telegram Türk gruplarında **değer-önce** varlık (15:1 soft mention kuralı)
- İlk nano/mikro collab denemeleri (1K–15K diaspora/utility creator)
- Paid: yalnızca organik kazanan 1–2 kreatifi **trafik → kayıt** ile test; günlük öğrenme bütçesi

**Çıkış kriteri:** Beachhead’te tekrarlayan etkileşim; IG’de save/share oranı yükselen 2+ format; kayıt CPA “anlamlı aralıkta” (iç benchmark oluşur).

### Faz 2 — Motor (Gün 46–90): “Tekrarlanabilir büyüme”

**Hedef:** Kazanan formülü scale; 2. şehir veya 2. kategori; retarget katmanı.

- Collab + Series (örn. “Pazartesi: Termin gerçeği”, “Perşembe: Forumdan”)
- Paid: mid-funnel event (kayıt veya ilk aksiyon) + site engagers retarget
- Creative fatigue ritmi: 2–4 haftada hook yenileme
- Sponsorluk/reklam geliri anlatısı (site `/reklam`) marka güvenini bozmadan — ayrı track

**Çıkış kriteri:** Haftalık sistem oturmuş; WAU/aksiyon trendi yukarı; playbook’a göre scale kararı alınabilir.

---

## 7. Kanal Mimarisi (İnce İşleme)

```
Keşif (Reels / Explore / Collab / micro-ads)
        ↓
Profil güveni (bio, highlights, pin’ler)
        ↓
gurbetde.com (rehber okuma / forum / ilan / sohbet)
        ↓
Kayıt + ilk aksiyon
        ↓
Retention (Stories, bildirim, e-posta ileride)
        ↓
Arz besleme (cevap yaz, ilan ver, rehber yazarı)
```

**Reklam:** Bu huninin her basamağına ayrı kampanya tipi. Cold’da “marka bilinci” için para yakmak yasak — cold = sorun hook’lu utility; warm = ürün derinliği.

**Organik öncelik sırası (ilk 90 gün):** Instagram → Facebook grup sızıntısı → Collab → (sonra) Shorts/TikTok adaptasyonu.

---

## 8. Riskler & Yönetici Kararları

| Risk | Mitigasyon |
|------|------------|
| Boş platform hissi | Beachhead + aktivite içeriği; abartılı üye sayısı yok |
| Erken ads ile pahalı kayıt | Pixel/CAPI + organik kanıt önce |
| Hukuki yanlış anlama | Disclaimer dili; “resmi kaynağı doğrula” |
| Soft brand içerik tuzağı | Her post tek iş: sorun veya CTA |
| Faceless marka yavaş büyür | Gerekirse founder/uzman yüzü Reels’e kontrollü ekle |
| Tüm Almanya’ya dağılma | Önce bir şehirde atomic network |

---

## 9. Faz 0 — Yayın Paketi (AKTİF)

**Durum:** İçerik üretildi. Sen Instagram’da aşağıdaki sırayla paylaşıyorsun.  
**Beachhead:** Berlin + Anmeldung / Konut  
**Görsel dil:** Navy `#0D1B2A` · White · Gold `#FFCC00` · Red `#E30A17` (yalnızca “De”) · sol üst wordmark · merkez line-icon  
**Saat:** Almanya saati **18:30–20:30** (hafta içi tercih)  
**Kopyala-yapıştır dosyalar:** `social-media/instagram/faz-0/`  
**Hazır görseller:** `social-media/instagram/faz-0/assets/` (carousel PNG + highlight kapakları + reel kapakları)

### 9.1 Bugün yap (paylaşımdan önce — 20 dk)

1. **Bio’yu değiştir** (aşağıdaki final metin).
2. **Highlights kapaklarını** oluştur (6 adet; içerik sonra Stories’ten eklenir).
3. Mevcut 2 post kalsın. **Özellik carousel’ini Pin’le** (en üst).
4. Professional dashboard: Insights açık.

#### Bio (final — aynen yapıştır)

```
Almanya'da Türkçe yaşam işletim sistemi
Vize · Anmeldung · İş · Oturum — rehber + forum
👇 Şehrini seç, sorunu çöz
```

Link: `https://www.gurbetde.com`  
İsim alanı (koru): `GurbetDe | Almanya Göç & Yaşam Rehberi`

#### Highlights kapakları (sırayla)

| # | İsim | Kapak metni | İkon |
|---|------|-------------|------|
| 1 | Rehber | REHBER | açık kitap |
| 2 | Forum | FORUM | konuşma balonu |
| 3 | İlanlar | İLANLAR | pin + bina |
| 4 | Konsolosluk | KONSOLOSLUK | damga |
| 5 | Şehirler | ŞEHİRLER | harita noktası |
| 6 | Başla | BAŞLA | logo G |

Kapak kuralı: navy zemin, gold ikon, tek kelime beyaz. Hikâye yokken bile boş kapak koy — profil dolu görünsün.

---

### 9.2 14 günlük yayın takvimi

| Gün | Kod | Format | Konu | Pin? |
|-----|-----|--------|------|------|
| 1 | P03 | Carousel 6 | Anmeldung: 5 adım + belge listesi | Evet (2. pin) |
| 2 | P04 | Reel 25sn | “Anmeldung’suz banka açtın — sonra ne olur?” | — |
| 3 | P05 | Carousel 5 | Forum kanıtı: Wohnungsgeberbestätigung | — |
| 4 | P06 | Reel 20sn | Eski forum vs GurbetDe (3 fark) | — |
| 5 | P07 | Tek kare + caption | Berlin beachhead: bu hafta ne soruluyor | — |
| 6 | P08 | Carousel 5 | Schufa “keine Information” — konut dosyası | — |
| 7 | P09 | Reel 22sn | Konsolosluk kanalı — tek tık | — |
| 8 | P10 | Carousel 6 | WG / kira: Mietvertrag checklist | — |
| 9 | P11 | Reel 18sn | “gurbetde.com’da sorunu yaz” CTA | — |
| 10–14 | — | Stories ağır | Aşağıdaki Story setini döndür + en iyi postu boost etme (ücretli yok) | — |

Mevcut P01 (launch) ve P02 (özellik) = grid’in temeli. Yeni postlar P03’ten başlar.

---

### 9.3 Post paketleri (metin + slide + hashtag)

Her postta **ilk yorumu sabitle** (linkli). Caption sonuna hashtag. Disclaimer gerekiyorsa: *Bilgilendirme amaçlıdır; resmi kurumdan teyit edin.*

---

#### P03 — Anmeldung Carousel (Gün 1) ★ PIN

**Format:** 1080×1080 · 6 slide · navy  
**Amaç:** Save + guide trafiği  
**Link:** https://www.gurbetde.com/guide/anmeldung

**Slide metinleri**

1. Hook  
   - H1: `Anmeldung'u erteleme`  
   - Alt: `14 gün kuralı + belge listesi — Türkçe`  
   - Altın: `Kaydır →`

2. Nedir?  
   - H1: `Anmeldung nedir?`  
   - Body: `Adresini Bürgeramt'a resmi bildirmek. Anmeldebestätigung olmadan banka, sigorta ve birçok işlem kilitlenir.`

3. Belgeler  
   - H1: `Yanına al`  
   - Madde: `Pasaport/Kimlik` · `Wohnungsgeberbestätigung` · `Mietvertrag` · `Anmeldung formu` · `(varsa) aile belgeleri`

4. Randevu  
   - H1: `Termin gerçeği`  
   - Body: `Büyük şehirde randevusuz gitme. Sabah erken slot açılır; iptalleri takip et.`  
   - Mini: `Berlin → service.berlin.de`

5. Sakla  
   - H1: `Belgeyi sakla`  
   - Body: `Anmeldebestätigung fotokopisi: banka ve işveren ister. Taşınınca yeniden Anmeldung.`

6. CTA  
   - H1: `Adım adım rehber`  
   - Body: `gurbetde.com/guide/anmeldung`  
   - Gold: `Kaydet · Paylaş`

**Caption (yapıştır)**

```
Anmeldung'u “sonra hallederim” dersen, banka ve sigorta da “sonra”a kalır.

14 gün kuralı, Wohnungsgeberbestätigung, Bürgeramt termin — hepsi tek rehberde, Türkçe.

Bu carousel'i kaydet. Taşınma çantana koy.

Detay → gurbetde.com/guide/anmeldung

Bilgilendirme amaçlıdır; şehrinin Bürgeramt sayfasından teyit et.

Soru: Senin şehirde termin kaç günde çıktı? Yorumla.
```

**İlk yorum (pin)**

```
Tam rehber: https://www.gurbetde.com/guide/anmeldung
Forumda takıldığın yeri sor: https://www.gurbetde.com/forum
```

**Hashtags**

```
#gurbetde #anmeldung #bürgeramt #almanyadahayat #türkleralmanya #berlin #gurbetçi #yenigelen #oturum #almanya
```

---

#### P04 — Reel: Anmeldung’suz banka (Gün 2)

**Format:** 1080×1920 · ~25 sn · text-on-screen · altyazı açık  
**Hook (0–2 sn):** `Anmeldung'suz banka açtın.`  
**Görsel:** koyu zemin, büyük beyaz yazı, gold vurgu kelimeler

**Ekran metni / senaryo**

| sn | Ekran |
|----|--------|
| 0–2 | `Anmeldung'suz banka açtın.` |
| 2–6 | `Hesap açıldı sanıyorsun.` |
| 6–12 | `Sonra: maaş, TK primi, Schufa dosyası…` |
| 12–18 | `Anmeldebestätigung isteyen yerler kilitlenir.` |
| 18–25 | `Önce Anmeldung. Rehber: gurbetde.com` |

**Caption**

```
Hesap açmak ≠ iş bitirmek.

Birçok banka ve kurum Anmeldebestätigung ister. Sıra: adres kaydı → belge → sonra finans.

Kaydet, taşınacak arkadaşına yolla.

Rehber → gurbetde.com/guide/anmeldung
```

**İlk yorum**

```
https://www.gurbetde.com/guide/anmeldung
```

**Hashtags**

```
#gurbetde #anmeldung #bankahesabı #almanyadahayat #gurbetçi #türkleralmanya
```

**CTA sticker (Stories paylaşımında):** Link → guide

---

#### P05 — Forum kanıtı carousel (Gün 3)

**Format:** 5 slide  
**Amaç:** Sosyal kanıt + forum trafiği  
**Link:** https://www.gurbetde.com/forum

**Slides**

1. `Forumda bugün` / `Wohnungsgeberbestätigung imzalanmıyor — ne olur?`
2. `Sorun:` `Ev sahibi formu imzalamıyor. Anmeldung bekliyor.`
3. `Neden kritik:` `Bu belge olmadan Bürgeramt kaydı çoğu yerde yürümüyor.`
4. `Ne yapılır:` `Aynı yolu geçmişlerin deneyimini oku. Sorunu foruma yaz.`
5. `CTA:` `gurbetde.com/forum` · `Şehrini seç · Konu aç`

**Caption**

```
Eski forumda konu kaybolur. GurbetDe'de kategori + şehir var.

Örnek: Wohnungsgeberbestätigung imzalanmıyor — Bürgeramt ne diyor?

Sen de takıldığın adımı yaz. Cevaplayanlar aynı yollardan geçmiş.

→ gurbetde.com/forum
```

**İlk yorum**

```
Foruma git: https://www.gurbetde.com/forum?kategori=anmeldung
```

**Hashtags**

```
#gurbetde #forum #anmeldung #wohnungsgeberbestätigung #almanyadahayat #gurbetçi #berlin
```

---

#### P06 — Reel: Eski forum vs GurbetDe (Gün 4)

**~20 sn · 3 fark**

| sn | Ekran |
|----|--------|
| 0–2 | `Eski forum yetmiyor.` |
| 2–8 | `1) Dağınık konu · GurbetDe: kategori + şehir` |
| 8–14 | `2) Sadece sohbet · GurbetDe: rehber + ilan + kanal` |
| 14–20 | `3) 2005 hissi · GurbetDe: modern, Türkçe, tek yer` |
| son | `gurbetde.com` |

**Caption**

```
Dağınık forum + WhatsApp + rastgele Reel tavsiyesi = bilgi kaosu.

GurbetDe: rehber, forum, ilan, konsolosluk kanalı — tek çatıda.

Aramıza katıl → gurbetde.com
```

**Hashtags**

```
#gurbetde #dijitaltopluluk #almanyadahayat #türkdiaspora #gurbetçi #yeninesil
```

---

#### P07 — Berlin beachhead (Gün 5)

**Format:** Tek kare 1080×1080  
**Görsel:** Navy · büyük `BERLİN` · alt: `Bu hafta forumda` · 3 mini satır konu tipi

**Kare metin**

```
BERLİN
Bu hafta sorulanlar
· Anmeldung / Bürgeramt termin
· WG & Schufa
· Dil kursu ilanları
gurbetde.com → Şehrini seç
```

**Caption**

```
Beachhead: Berlin.

Anmeldung, WG, dil kursu — aynı şehirde yaşayanlar aynı sorunları yaşıyor.

Şehrini seç, konuyu aç veya ilanlara bak.
→ gurbetde.com
```

**İlk yorum**

```
Berlin odası: https://www.gurbetde.com/sohbet/berlin
İlanlar: https://www.gurbetde.com/ilanlar
```

**Hashtags**

```
#gurbetde #berlin #türklerberlin #almanyadahayat #gurbetçi #wgzimmer
```

---

#### P08 — Schufa / konut carousel (Gün 6)

**5 slide · Link:** forum konut + guide kira

1. Hook: `Schufa "keine Information"` / `Ev sahibi yine dosya istiyor`
2. `Bu ne demek:` `Yeni gelende kayıt boş olabilir — “skor yok” ≠ “kötü skor”.`
3. `Dosyaya ne eklenir:` `İş sözleşmesi · banka ekstre · kefil/garanti · Mieterselbstauskunft`
4. `Soru foruma:` `Senin şehirde ne işe yaradı?`
5. CTA: `gurbetde.com/forum` + `Rehber: kira ve konut`

**Caption**

```
İlk Schufa çıktında "keine Information" görmek panik değil — yeni başlangıç sinyali.

Ev sahibi yine paket ister. Ne koyacağını bilmek = ev kapısı.

Kaydet. Foruma deneyimini yaz.
→ gurbetde.com/forum
Rehber: gurbetde.com/guide/kira-ve-konut
```

**Hashtags**

```
#gurbetde #schufa #kira #wg #konut #almanyadahayat #gurbetçi #berlin
```

---

#### P09 — Reel: Konsolosluk kanalı (Gün 7)

| sn | Ekran |
|----|--------|
| 0–2 | `Randevu duyurusu kaçtı mı?` |
| 2–10 | `Vize · pasaport · konsolosluk` |
| 10–16 | `Kaynağa yakın akış — tek yerde` |
| 16–22 | `gurbetde.com → Konsolosluk Haberleri` |

**Caption**

```
Konsolosluk duyurusu Story'de kaybolmasın.

GurbetDe Konsolosluk kanalı: randevu, vize, pasaport — cebinde.
→ gurbetde.com/sohbet/kanal-konsolosluk-haber
```

**Hashtags**

```
#gurbetde #konsolosluk #vize #pasaport #almanyadahayat #gurbetçi
```

---

#### P10 — Kira / WG checklist carousel (Gün 8)

**6 slide**

1. `WG / kira dosyası` / `Başvurudan önce checklist`
2. `Mietvertrag` — sözleşmeyi okumadan imzalama
3. `Kaution + Nebenkosten` — net aylık maliyeti hesapla
4. `Untermiete vs Zwischenmiete` — türü netleştir
5. `İlanlarda şehir seç` — Berlin’den Münih’e
6. CTA: `gurbetde.com/ilanlar` · `Rehber: /guide/kira-ve-konut`

**Caption**

```
WG bulmak şans işi değil — dosya işi.

Checklist'i kaydet. İlanı şehir filtreyle gör.
→ gurbetde.com/ilanlar
```

**Hashtags**

```
#gurbetde #wg #mietvertrag #kira #almanyadahayat #berlin #münih #gurbetçi
```

---

#### P11 — Reel CTA (Gün 9)

| sn | Ekran |
|----|--------|
| 0–2 | `Sorununu Story'ye yazma.` |
| 2–8 | `Foruma yaz. Rehberi oku. İlanı aç.` |
| 8–14 | `Aynı yolu geçmişler burada.` |
| 14–18 | `gurbetde.com — Aramıza katıl.` |

**Caption**

```
Bilgi dağınık olmasın.

Rehber · Forum · İlan · Konsolosluk — GurbetDe.
👇 gurbetde.com
```

**Hashtags**

```
#gurbetde #almanyadahayat #gurbetçi #türkleralmanya #dijitaltopluluk
```

---

### 9.4 Stories — Günlük set (Gün 1–14)

Her gün **3–5 Story**, sıra örnek:

1. **Sabah (opsiyonel):** “Bugünün konusu” + poll (`Anmeldung` / `Kira` / `Vize`)
2. **Öğle:** Feed postunu Story’ye paylaş + **Link sticker** (deep link)
3. **Akşam:** “Forumdan 1 satır” (ekran görüntüsü markalı frame) veya “Soru kutusu — şehir yaz”
4. **CTA:** “Cevabı siteye taşı → gurbetde.com/forum”

Highlights’a ekle:
- Anmeldung Story’leri → **Rehber**
- Forum → **Forum**
- İlan/WG → **İlanlar**
- Konsolosluk → **Konsolosluk**
- Berlin → **Şehirler**
- “Nasıl başlarım” 4 kare → **Başla**

---

### 9.5 Senin yayın SOP’un (her post)

1. Görseli mevcut carousel dilinde üret (Canva/Figma — şablon: wordmark sol üst, gold ikon, navy).
2. Caption’ı olduğu gibi yapıştır.
3. Hashtag’leri caption sonuna ekle (3–8/10 arası; set hazır).
4. Paylaş → **hemen** ilk yorumu yaz ve **pinle**.
5. Story’ye paylaş + link sticker.
6. İlk 60 dk: gelen her yoruma cevap (1 cümle + gerekirse link).
7. Insights not et: reach, saves, shares, profile visits, link taps.

**Yasak:** Beğeni isteyen CTA, 20+ hashtag, “500K üye” abartısı, hukuki garanti dili.

---

### 9.6 Görsel üretim brief (tasarımcı / sen)

- Boyut: Feed 1080×1080 · Reel 1080×1920  
- Font: geometrik sans, bold H1, body regular  
- Sol üst: `Gurbet` beyaz + `De` kırmızı  
- Sağ üst (carousel): `1/6` gold  
- Alt: `Kaydır →` gold + `gurbetde.com` white  
- Stok insan yüzü yok; line-icon merkez  
- Bayrak pastişi / sticker / emoji yağmuru yok  

---

## 10. Sonraki sprint (Faz 0 bitince)

Gün 14 Insights özeti gelince yönetici kararı:
- Kazanan formatı 2× üret
- Beachhead genişlet veya sıkılaştır
- Meta Ads mikro test (yalnızca P03/P04 tipi kazananlar)

---

## Kaynaklar

- Canlı site: gurbetde.com (anasayfa, /guide, /forum, /ilanlar, sohbet kanalları)
- Anmeldung rehberi: https://www.gurbetde.com/guide/anmeldung
- Mevcut IG grid & bio (ekran görüntüleri, Temmuz 2026)
- Repo asset’leri: `social-media/instagram/` · Faz 0: `social-media/instagram/faz-0/`
- Yönetici bilgi bankası: `docs/social_media_management_playbook.md`
- Harici öğrenim: Instagram 2026 ranking, Meta Pixel+CAPI, cold-start, TR–DE pazar (playbook §10)
)

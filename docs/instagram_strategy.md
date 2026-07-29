# GurbetDe Instagram Strategy

**Rol:** Sosyal Medya Direktörü · Marka Yöneticisi · İçerik Stratejisti  
**Hesap:** [@gurbetdecom](https://www.instagram.com/gurbetdecom/)  
**Web:** [gurbetde.com](https://www.gurbetde.com)  
**Belge durumu:** Denetim + sütunlar + yönetici vizyonu + 90 gün plan (kampanya brief’i bekleniyor)  
**Tarih:** 28–29 Temmuz 2026  
**Kapsam:** Read-only platform okuması · kod müdahalesi yok  
**Bilgi bankası:** `docs/social_media_management_playbook.md`

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

## 9. Bekleyen Karar / Sonraki Talimat

Yönetim vizyonu ve 90 günlük plan kilitlendi. Playbook kaydedildi.

**Hazır olduğunda verilecek talimat örnekleri:**
- Faz 0 uygulama paketi (bio metni final + Highlights kapak brief + 9 post backlog metinleri)
- “Anmeldung 7-gün sprint”
- Beachhead onayı (Berlin mi, başka şehir mi?)
- Meta Ads altyapı checklist (Pixel event listesi)

Talimat gelince bu dosyaya: yayın takvimi, post metinleri, hook’lar, carousel taslakları, hashtag setleri, story akışları eklenecek.

---

## Kaynaklar

- Canlı site: gurbetde.com (anasayfa, /guide, /forum, /ilanlar, sohbet kanalları)
- Mevcut IG grid & bio (ekran görüntüleri, Temmuz 2026)
- Repo asset’leri: `social-media/instagram/`
- Yönetici bilgi bankası: `docs/social_media_management_playbook.md`
- Harici öğrenim: Instagram 2026 ranking (shares/saves/Reels), Meta Pixel+CAPI 2026, marketplace cold-start, TR–DE ethno-marketing / DE sosyal kullanım verileri (playbook §10)
)

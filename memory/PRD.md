# AutoCheck - PRD (Product Requirements Document)

## Problem Statement
DoorDash/UberEats'ten ilham alan uzaktan araç kontrol platformu. Uzaktaki bir arabayı almak isteyen kişi, uygulamayı kullanarak o araca bakıp alınabilirliğini kontrol edecek bir kontrolcü bulabilecek.

**Örnek Senaryo:** Indiana'da yaşayan biri Chicago'da bir araba beğeniyor ama emin olamıyor. $100-$300 karşılığında birinden o arabaya bakmasını talep ederek güvenle karar veriyor.

## User Personas

### 1. Alıcı (Buyer)
- Uzakta olan araç almak isteyen kişi
- Araç bilgilerini ve satıcı adresini girer
- Kontrol paketi seçer ve tip verebilir
- Güvenlik kodunu satıcıya iletir
- Detaylı rapor alır

### 2. Kontrolcü (Inspector)
- Araç kontrol hizmeti veren kişi
- ID onayı zorunlu
- Yakınındaki işleri harita ve liste olarak görür
- İşi kabul eder, güvenlik koduyla başlar
- Adım adım talimatlarla fotoğraf çeker
- Rapor gönderir, ödeme alır

## Core Requirements (Static)

### Renk & Tema
- **Amber sarısı (#FFBF00)** ve **siyah (#0A0A0A)** renkleri
- DoorDash/UberEats tarzı modern, dark mode tasarım
- Outfit + Manrope fontları

### Paketler
- **Basic:** $100 - Temel kontrol, 15 fotoğraf
- **Premium:** $250 - Detaylı kontrol, 30 fotoğraf, video
- **Professional:** $300 - Tam profesyonel değerlendirme, OBD-II, 50+ fotoğraf

### Güvenlik Kodu Sistemi
- 6 haneli rastgele kod
- Alıcı → Satıcı → Kontrolcü zinciri
- Kontrolcü kod olmadan başlayamaz

## What's Been Implemented (Jan 26, 2026)

### Backend (FastAPI + MongoDB)
- ✅ Kullanıcı kaydı ve girişi (Alıcı/Kontrolcü)
- ✅ Paket sistemi (Basic $100, Premium $250, Professional $300)
- ✅ Kontrol talebi oluşturma
- ✅ 6 haneli güvenlik kodu üretimi
- ✅ Kontrolcü ID doğrulama (Mock)
- ✅ Mevcut işleri listeleme (konum bazlı)
- ✅ İş kabul etme
- ✅ Güvenlik kodu doğrulama
- ✅ Adım adım kontrol (8 adım)
- ✅ Fotoğraf yükleme
- ✅ Rapor gönderimi
- ✅ Bildirim sistemi

### Frontend (React + Tailwind + Leaflet)
- ✅ Landing page (hero, nasıl çalışır, paketler, kontrolcü ol)
- ✅ Kayıt ve giriş sayfaları
- ✅ Alıcı dashboard (talepler listesi, yeni talep formu)
- ✅ Kontrolcü dashboard (mevcut işler, işlerim, harita)
- ✅ 6 haneli OTP input
- ✅ Adım adım kontrol UI
- ✅ Leaflet harita entegrasyonu (dark mode)
- ✅ Bildirim sistemi
- ✅ Responsive tasarım

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Gerçek ödeme entegrasyonu (Stripe)
- [ ] Gerçek ID doğrulama servisi
- [ ] Fotoğraf/video gerçek yükleme ve görüntüleme

### P1 - High Priority
- [ ] Push notification (Firebase)
- [ ] SMS bildirimleri (Twilio)
- [ ] Kontrolcü konum takibi (real-time)
- [ ] Mesajlaşma sistemi (Alıcı ↔ Kontrolcü)

### P2 - Medium Priority
- [ ] Kontrolcü puan/yorum sistemi
- [ ] Favori kontrolcüler
- [ ] Tekrarlanan kontrol indirimi
- [ ] Admin paneli

### P3 - Nice to Have
- [ ] Çoklu dil desteği (EN/TR)
- [ ] Dark/Light mode toggle
- [ ] Araç geçmişi raporları
- [ ] AI destekli araç değerlendirmesi

## Tech Stack
- **Frontend:** React 19, Tailwind CSS, Leaflet (OpenStreetMap)
- **Backend:** FastAPI, Motor (MongoDB async driver)
- **Database:** MongoDB
- **Maps:** Leaflet with OpenStreetMap (ücretsiz)

## API Endpoints
```
POST /api/auth/register - Kullanıcı kaydı
POST /api/auth/login - Giriş
GET /api/packages - Paket listesi
POST /api/inspections - Kontrol talebi oluştur
GET /api/inspections/buyer/{id} - Alıcı kontrolleri
GET /api/inspections/available - Mevcut işler
POST /api/inspections/{id}/accept - İş kabul et
POST /api/inspections/{id}/verify-code - Kod doğrula
POST /api/inspections/{id}/complete-step - Adım tamamla
POST /api/inspections/{id}/submit-report - Rapor gönder
GET /api/notifications/{user_id} - Bildirimler
```

## Notes
- Ödeme sistemi MOCK - gerçek para transferi yok
- ID doğrulama MOCK - otomatik onaylanıyor
- Fotoğraflar sunucuya kaydediliyor ama görüntüleme henüz optimize değil

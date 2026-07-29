# GurbetDe Instagram — Faz 0 Yayın Klasörü

Bu klasör **kopyala-yapıştır + hazır görsel** içindir.  
Tam strateji: `docs/instagram_strategy.md` §9.

## Bugün (paylaşımdan önce)

1. `BIO.txt` → Instagram bio’ya yapıştır  
2. `assets/highlights/*.png` → 6 Highlight kapağı  
3. Mevcut özellik carousel’ini **Pin**le  

## 9 günlük feed

| Gün | Caption dosyası | Görseller |
|-----|-----------------|-----------|
| 1 | `posts/P03-anmeldung-carousel.txt` | `assets/P03-anmeldung/01–06.png` → **Pin (2.)** |
| 2 | `posts/P04-anmeldung-banka-reel.txt` | Reel: `assets/reel-covers/P04-…` kapak + ekran metni dosyada |
| 3 | `posts/P05-forum-kanit-carousel.txt` | `assets/P05-forum/01–05.png` |
| 4 | `posts/P06-eski-forum-vs-reel.txt` | `assets/reel-covers/P06-…` |
| 5 | `posts/P07-berlin-beachhead.txt` | `assets/P07-berlin/01.png` |
| 6 | `posts/P08-schufa-konut-carousel.txt` | `assets/P08-schufa/01–05.png` |
| 7 | `posts/P09-konsolosluk-reel.txt` | `assets/reel-covers/P09-…` |
| 8 | `posts/P10-kira-wg-carousel.txt` | `assets/P10-kira/01–06.png` |
| 9 | `posts/P11-cta-reel.txt` | `assets/reel-covers/P11-…` |

**Reels:** Kapak PNG’yi CapCut/IG’de text-on-screen animasyonuyla kullan; senaryo satır satır `.txt` dosyasında.  
**Stories:** `stories/DAILY.md`  
**Saat:** 18:30–20:30 (DE)

## Her post SOP

1. Görselleri yükle  
2. Caption yapıştır  
3. Paylaş  
4. İlk yorum → **Pin**  
5. Story + link sticker  
6. İlk 60 dk yorumlara cevap  

## Görselleri yeniden üret

```bash
pip install pillow
python3 social-media/instagram/faz-0/generate_faz0_assets.py
```

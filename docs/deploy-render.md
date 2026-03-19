# AURA Render Deploy

Bu doküman, AURA Faz 1'i Render üzerinde pilot kullanıma açmak için en kısa yolu özetler.

## Neden Render?

- Django için resmi deploy rehberi var
- GitHub bağlantısıyla otomatik deploy alıyor
- Yönetilen PostgreSQL sağlıyor
- Persistent disk ile yüklenen dosyalar korunabiliyor

## Bu repo içinde hazırlananlar

- production ayarları için ortam değişkeni desteği
- WhiteNoise ile static dosya servisi
- PostgreSQL bağlantısı için `DATABASE_URL` desteği
- sağlık kontrolü: `/healthz/`
- Render blueprint dosyası: `render.yaml`
- build komutları: `build.sh`
- korumalı dosya indirme akışı

## Önerilen pilot kurulumu

- Web service planı: `starter`
- PostgreSQL planı: `basic-256mb`
- Persistent disk: `1 GB`

Bu kombinasyon, küçük pilot için en düşük riskli başlangıçtır.

## Kurulum adımları

1. GitHub reposunu Render'a bağla.
2. `Blueprints` bölümünden yeni bir blueprint oluştur.
3. Bu repo içindeki `render.yaml` dosyasını kullan.
4. Deploy tamamlandıktan sonra uygulama URL'sini aç.
5. Yönetici hesabı için `createsuperuser` ya da seed komutlarını Render shell içinde çalıştır.

## İlk deploy sonrası önerilen komutlar

Pilot başlangıcı için:

```bash
python manage.py seed_demo_users --dataset pilot --reset
```

Demo turu için:

```bash
python manage.py seed_demo_users --dataset demo --reset
```

## Notlar

- `SECRET_KEY` Render tarafından üretilir.
- `DATABASE_URL` Render PostgreSQL'den gelir.
- Yüklenen dosyalar `/var/data/media` altında tutulur.
- Uygulama içindeki dosya bağlantıları artık doğrudan media URL'sine değil, Django içindeki korumalı indirme rotasına gider.

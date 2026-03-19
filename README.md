# AURA

AURA, Anadolu Üniversitesinde görme engelli öğrenciler ile gönüllü öğrenciler arasında etkileşimi güçlendiren; koordinatör ve akademik danışman desteğiyle sürdürülebilir sosyal destek ağı kurmayı amaçlayan erişilebilir bir platformdur.

## Vizyon

Anadolu Üniversitesinde görme engelli öğrenciler ile gönüllü öğrenciler arasında etkileşimi ve sosyal katılımı güçlendiren; güven ve etik ilkelere dayalı, erişilebilir, kapsayıcı ve sürdürülebilir sosyal destek ağı oluşturmak.

## Faz 1 Kapsamı

Faz 1, platformun çalışan ilk sürümünü oluşturur. Bu sürümde:

- öğrenciler destek talebi oluşturabilir
- gönüllü öğrenciler açık talepleri görüp üstlenebilir
- taraflar talep içinde mesajlaşabilir
- kaynak dosyaları paylaşılabilir
- koordinatör süreci izleyebilir, eşleştirme yapabilir ve koordinasyon notları ekleyebilir
- akademik danışman destek sürecine gözlemci ve rehber rolüyle dahil olabilir
- bildirim merkezi temel gelişmeleri kullanıcıya aktarır

## Roller

- Görme engelli öğrenci
- Gönüllü öğrenci
- Koordinatör
- Akademik danışman
- Sistem yöneticisi

## Temel Özellikler

- Kayıt, giriş ve rol seçimi
- Profil tamamlama
- Destek talebi oluşturma ve takip etme
- Geçerlilik süresi ve son tarih takibi
- Talep içi mesajlaşma
- Kaynak dosya yükleme ve paylaşma
- Koordinatör yönetim akışları
- Bildirim merkezi
- Erişilebilirlik odaklı arayüz

## Teknik Yapı

- Django
- SQLite (geliştirme ortamı)
- Django template tabanlı arayüz
- Rol bazlı yetkilendirme
- Talep, mesaj, dosya ve bildirim odaklı modüler yapı

## Yerelde Çalıştırma

PowerShell:

```powershell
cd "C:\Users\musta\Documents\Codex Projects\aura-prj"
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

Gelişim için demo veri:

```powershell
python manage.py seed_demo_users --dataset demo --reset
```

Pilot için temiz veri seti:

```powershell
python manage.py seed_demo_users --dataset pilot --reset
```

## Testler

```powershell
python manage.py test
```

## Dokümanlar

- `docs/phase-1-product-scope.md`
- `docs/phase-1-delivery-plan.md`
- `docs/phase-1-pilot-readiness-checklist.md`
- `docs/deploy-render.md`
- `docs/pilot-user-plan.md`
- `docs/pilot-scenario-validation.md`

## İlk Sürüm

`v0.1.0`, AURA Faz 1'in ilk çalışan sürümünü temsil eder. Bu sürümün odağı genel bir yardım platformu olmak değil; akademik destek ve koordinasyon merkezli, erişilebilir ve kapsayıcı bir sosyal destek akışı sunmaktır.

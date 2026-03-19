# AURA Faz 1 Pilot Hazırlık Checklist'i

## 1. Amaç

Bu liste, AURA Faz 1'in küçük ölçekli pilot kullanıma hazır olup olmadığını doğrulamak için kullanılır.

Odak:

- kritik kullanıcı akışları
- erişilebilirlik
- içerik ve metin tutarlılığı
- demo veriden temiz başlangıca geçiş
- koordinasyon ekibinin temel operasyonları

## 2. Pilot Öncesi Başlangıç Durumu

### Veri hazırlığı

- [ ] Pilot ortamında `pilot` veri seti ile temiz başlangıç oluşturuldu
- [ ] Demo öğrenci ve demo gönüllü hesapları kaldırıldı
- [ ] Demo talepler, demo mesajlar, demo materyaller ve demo bildirimler kaldırıldı
- [ ] Pilot için kullanılacak gerçek veya kontrollü test kullanıcıları belirlendi

### Temel hesaplar

- [ ] Yönetici hesabı çalışıyor
- [ ] En az 1 koordinatör hesabı hazır
- [ ] En az 1 akademik danışman hesabı hazır
- [ ] Pilotta kullanılacak öğrenci ve gönüllü hesap açma yöntemi net

## 3. Kritik Kullanıcı Akışları

### Görme engelli öğrenci

- [ ] Kayıt olabilir
- [ ] Profilini tamamlayabilir
- [ ] Akademik destek talebi oluşturabilir
- [ ] Talep detayını görüntüleyebilir
- [ ] Materyal yükleyebilir
- [ ] Eşleşen gönüllü ile mesajlaşabilir
- [ ] Talebi tamamlandı veya iptal edildi olarak kapatabilir

### Gönüllü öğrenci

- [ ] Açık talepleri görebilir
- [ ] Uygun bir talebi üstlenebilir
- [ ] Üstlendiği destekleri ayrı listede görebilir
- [ ] Öğrenci ile mesajlaşabilir
- [ ] Materyal yükleyebilir ve görüntüleyebilir
- [ ] Destek durumunu güncelleyebilir

### Koordinatör

- [ ] Koordinatör paneline erişebilir
- [ ] Açık ve kritik talepleri görebilir
- [ ] Müdahale bekleyen talepleri ayırt edebilir
- [ ] Gönüllü ataması yapabilir
- [ ] Talep durumu güncelleyebilir
- [ ] Talep önceliği belirleyebilir
- [ ] Müdahale notu ekleyebilir
- [ ] Kullanıcıları listeleyebilir ve filtreleyebilir
- [ ] Gerekirse kullanıcıyı pasife alabilir veya yeniden aktive edebilir

### Akademik danışman

- [ ] Akademik danışman paneline erişebilir
- [ ] Talepleri görüntüleyebilir
- [ ] Talep detayına girip süreci inceleyebilir
- [ ] Gerekli durumlarda koordinasyon akışına destek olabilir

## 4. Erişilebilirlik Kontrolleri

### Klavye ile kullanım

- [ ] Giriş akışı tamamen klavye ile tamamlanabiliyor
- [ ] Kayıt ve profil tamamlama akışları tamamen klavye ile tamamlanabiliyor
- [ ] Talep oluşturma akışı tamamen klavye ile tamamlanabiliyor
- [ ] Mesaj gönderme ve materyal yükleme akışları tamamen klavye ile tamamlanabiliyor
- [ ] Dashboard ve detay ekranlarındaki bölüm atlama bağlantıları çalışıyor

### Ekran okuyucu uyumu

- [ ] Form alanlarının görünür etiketleri var
- [ ] Yardım metinleri ve hata mesajları alanlarla ilişkilendirilmiş
- [ ] Boş durum mesajları anlamlı ve açık
- [ ] Durum rozetleri yalnızca renkle değil metinle de anlaşılır
- [ ] Liste ve zaman akışı yapıları semantik olarak okunabilir

### Görsel erişilebilirlik

- [ ] Odak göstergeleri görünür
- [ ] Renk kontrastı kritik aksiyonlarda yeterli
- [ ] Buton ve bağlantı metinleri açık
- [ ] Mobil görünümde içerik taşmıyor veya kaybolmuyor

## 5. İçerik ve Metin Kontrolü

- [ ] Aynı kavramlar tüm ekranlarda aynı terimlerle geçiyor
- [ ] Türkçe karakterler tüm arayüzde doğru görünüyor
- [ ] İşlem sonrası başarı ve hata mesajları kısa ve anlaşılır
- [ ] Boş durum metinleri kullanıcıya sonraki adımı söylüyor
- [ ] Pilot katılımcısının anlayamayacağı geliştirme dili veya demo ifadesi kalmadı

## 6. Kenar Durumlar ve Güvenli Davranış

- [ ] Yetkisiz kullanıcı ilgili yönetim ekranına giremez
- [ ] Yetkisiz girişte kullanıcı açıklayıcı bir erişim ekranı görür
- [ ] Bulunamayan sayfalar için yönlendirici 404 ekranı var
- [ ] Sunucu hatası durumunda sade ve güvenli 500 ekranı var
- [ ] Pasif kullanıcı kritik alanlara erişemez
- [ ] Tamamlanmış veya iptal edilmiş taleplerde kapalı durum açıkça gösterilir
- [ ] Bildirim filtresinde boş sonuç varsa kullanıcı nedenini anlayabilir

## 7. Koordinasyon ve Operasyon Kontrolü

- [ ] Koordinatör panelindeki özet metrikler doğru çalışıyor
- [ ] Kritik talepler görünür biçimde öne çıkıyor
- [ ] Son talep aksiyonları görüntülenebiliyor
- [ ] Son kullanıcı yönetimi aksiyonları görüntülenebiliyor
- [ ] Müdahale notları kaydediliyor ve listeleniyor
- [ ] Talep filtreleri beklenen sonuçları veriyor
- [ ] Kullanıcı filtreleri beklenen sonuçları veriyor

## 8. Pilot Günü İçin Minimum Senaryolar

Pilot başlamadan önce aşağıdaki senaryolar en az bir kez uçtan uca doğrulanmalı:

### Senaryo 1: Öğrenci talep açar

- [ ] Öğrenci giriş yapar
- [ ] Profilini tamamlar
- [ ] Akademik destek talebi açar
- [ ] Bir materyal yükler

### Senaryo 2: Gönüllü talebi üstlenir

- [ ] Gönüllü açık talepleri görür
- [ ] Talebi üstlenir
- [ ] Öğrenci ile mesajlaşır
- [ ] Süreci tamamlandı durumuna getirir

### Senaryo 3: Koordinatör müdahale eder

- [ ] Koordinatör eşleşmemiş bir talebi görür
- [ ] Talebe gönüllü atar
- [ ] Öncelik günceller
- [ ] Müdahale notu ekler

### Senaryo 4: Bildirimler çalışır

- [ ] Talep oluşturulduğunda ilgili rollere bildirim gider
- [ ] Eşleşme olduğunda ilgili rollere bildirim gider
- [ ] Mesaj veya materyal eklendiğinde ilgili kullanıcı bildirim alır

## 9. Pilot İçin Karar Kapısı

Faz 1, aşağıdaki koşullar sağlanıyorsa pilot kullanıma hazır kabul edilebilir:

- [ ] Kritik akışlarda engelleyici hata yok
- [ ] Erişilebilirlik açısından temel akışlar tamamlanabiliyor
- [ ] Demo veri temizlenmiş durumda
- [ ] Koordinatör süreci yönetebiliyor
- [ ] Talep, eşleşme, mesajlaşma ve materyal paylaşımı uçtan uca çalışıyor
- [ ] Pilotta kullanılacak kullanıcı ve destek planı netleşti

## 10. Önerilen Son Hazırlık Sırası

1. `python manage.py seed_demo_users --dataset pilot --reset`
2. Pilot kullanıcılarını aç
3. Senaryo 1-2-3-4'ü elle doğrula
4. Metin ve görünümde kalan küçük pürüzleri kapat
5. Pilot başlangıç onayı ver

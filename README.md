# ERP-Management-System-Python
PyQt6 ve SQLite kullanılarak geliştirilen, TCMB döviz entegrasyonlu modern ERP yazılımı
#  ERP Lite v2.0 - İşletme Yönetim Sistemi

Bu proje; küçük ve orta ölçekli işletmelerin (KOBİ) cari hesaplarını, stok durumlarını ve faturalama süreçlerini tek bir merkezden yönetmeleri için geliştirilmiş, Python tabanlı bir masaüstü uygulamasıdır.

## Öne Çıkan Özellikler
- **Döviz Entegrasyonu:** TCMB (Merkez Bankası) üzerinden anlık kur çekme ve dövizli işlemler.
- **Stok Takibi:** Ürünlerin giriş-çıkış hareketleri ve kritik stok seviyesi uyarıları.
- **Cari Hesap Yönetimi:** Müşteri ve tedarikçi bazlı borç/alacak takibi.
- **Modern Arayüz:** PyQt6 ile tasarlanmış, göz yormayan Dark Mode (Koyu Tema) desteği.
- **Güvenli Veritabanı:** Verilerin yerel olarak saklandığı hızlı SQLite altyapısı.
- **Ekran Görüntüsü**![ERP Lite v2.0 Ekran Görüntüsü](ekran_goruntusu.png)
##  Kullanılan Teknolojiler
- **Dil:** Python 3.10+
- **Arayüz Framework:** PyQt6
- **Veri Yönetimi:** SQLite3 & Pandas
- **API/Veri Çekme:** Requests & ElementTree (TCMB XML)

##  Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için şu adımları izleyin:

1. Bu depoyu klonlayın veya .zip olarak indirin.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install PyQt6 pandas requests
3. Uygulamayı başlatın:
   python erp.py

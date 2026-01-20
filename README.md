# 🛡️ FORTICAM - FortiManager Dashboard & Controller (v1.6.0)

**FORTICAM**, FortiManager sistemlerini merkezi olarak yönetmek, port durumlarını kontrol etmek ve güvenli, rol tabanlı erişim sağlamak için geliştirilmiş ölçeklenebilir bir dashboard çözümüdür. Modern tasarımı ve yüksek güvenilirlikli kontrol mekanizmaları ile kurumsal ağ yönetimini basitleştirir.

## 🌟 Öne Çıkan Özellikler

*   **📈 Ölçeklenebilir Dashboard:** 200+ cihazı destekleyen **Arama (Search)** ve **Sayfalama (Pagination)** özellikli görsel arayüz.
*   **⚡ Hızlı ve Güvenilir Kontrol:** Standart FMG DB Update yöntemine ek olarak, doğrudan cihaz API'sine erişen **Direct Proxy (REST API)** kontrolü.
*   **🛡️ Gelişmiş Güvenlik:** `bcrypt` ile şifrelenmiş yerel hesaplar ve kapsamlı LDAP (Active Directory) entegrasyonu.
*   **👥 Granüler Yetkilendirme (RBAC):** Cihaz ve port bazlı erişim kısıtlamaları, modül bazlı kullanıcı profilleri.
*   **🔄 Gerçek Zamanlı Senkronizasyon:** Optimistic UI ve Monitor API entegrasyonu ile port değişikliklerinin anlık takibi.
*   **🛡️ SIEM Entegrasyonu:** Tüm işlemlerin gerçek zamanlı olarak Syslog üzerinden SIEM sistemlerine aktarılması ve test araçları.
*   **🚀 Konteyner Uyumluluğu:** Docker ve OpenShift (Rootless) ortamları için optimize edilmiş mimari.

## 🛠️ Kurulum

### Docker ile Çalıştırma (Önerilen)

1.  **Repoyu Klonlayın:**
    ```bash
    git clone https://github.com/mhmmtctnn/FORTICAM.git
    cd FORTICAM
    ```

2.  **İmajı Oluşturun ve Başlatın:**
    ```bash
    docker-compose up -d --build
    ```

3.  **Erişim:**
    `http://localhost:8501` adresinden giriş yapabilirsiniz. (Varsayılan: `admin` / `admin`)

## ☁️ OpenShift Deployment

Uygulama, OpenShift'in güvenlik politikalarına (SCC restricted) tam uyumludur:
- `/app/data` dizini persistence için Volume olarak bağlanabilir.
- Arbitrary User ID desteği ile root olmayan kullanıcılar tarafından çalıştırılabilir.

## ⚙️ Yapılandırma

Ayarlar paneli üzerinden şunları yönetebilirsiniz:
- **Port Kontrol Yöntemi:** "Standart" veya "Hızlı (Direct Proxy)" seçimi.
- **LDAP Kümeleme:** Birden fazla LDAP sunucusu tanımı ve SSL desteği.
- **Bağlantı Sağlık Kontrolleri:** FMG ve LDAP servis durumlarının anlık izlenimi.

## 📂 Proje Yapısı

```
FORTICAM/
├── src/                # Kaynak Kodlar
│   ├── app.py          # Dashboard ve Navigasyon
│   ├── api_client.py   # FortiManager API Logic
│   ├── auth_service.py # Kimlik Doğrulama (Bcrypt/LDAP)
│   ├── log_service.py  # Audit & SIEM Logging
│   └── ui_components.py# Glassmorphism UI Tasarımı
├── data/               # Kalıcı Veritabanı (JSON/CSV)
├── MFA Logo/           # Branding Varlıkları
├── Dockerfile          # Container Tanımı
└── requirements.txt    # Bağımlılıklar
```

## 📝 Lisans

Bu proje [MIT](LICENSE) lisansı ile lisanslanmıştır.
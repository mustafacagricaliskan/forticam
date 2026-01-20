# 🛡️ FORTICAM - FortiManager Interface Controller

**FORTICAM**, FortiManager sistemlerini yönetmek, port durumlarını kontrol etmek ve güvenli erişim sağlamak için geliştirilmiş, kullanıcı dostu bir arayüzdür. Modern tasarımı, rol tabanlı yetkilendirme sistemi ve loglama özellikleri ile ağ yöneticilerinin işini kolaylaştırır.

## 🌟 Özellikler

*   **🛡️ Güvenli Giriş:** Yerel veritabanı ve LDAP (Active Directory) entegrasyonu ile güvenli kimlik doğrulama.
*   **📊 Dashboard:** Yönetilen cihazların ve VDOM'ların anlık durumunu görüntüleme.
*   **🔌 Port Yönetimi:** Yetki seviyelerine göre portları açma/kapama (Enable/Disable) imkanı.
*   **👥 Rol Tabanlı Erişim (RBAC):** Kullanıcı rolleri ve granüler yetkilendirme (Global ve Cihaz bazlı port izinleri).
*   **📝 Audit Logs:** Yapılan tüm işlemlerin (Kullanıcı, Tarih, İşlem, Cihaz) kayıt altına alınması ve CSV olarak indirilmesi.
*   **🚀 Docker & OpenShift Desteği:** Konteyner mimarisi ile kolay kurulum ve taşınabilirlik. OpenShift rootless deployment uyumluluğu.
*   **⚡ Performans:** Önbellekleme (Caching) mekanizması ile hızlı veri erişimi.
*   **🎨 Modern Arayüz:** Streamlit tabanlı, özelleştirilebilir ve şık kullanıcı arayüzü.

## 🛠️ Kurulum

Bu proje Docker kullanılarak kolayca çalıştırılabilir.

### Gereksinimler

*   Docker Desktop (Windows/Mac/Linux)

### Adım Adım Çalıştırma

1.  **Repoyu Klonlayın:**
    ```bash
    git clone https://github.com/mhmmtctnn/FORTICAM.git
    cd FORTICAM
    ```

2.  **Uygulamayı Başlatın:**
    Windows kullanıcıları için hazır script:
    ```bash
    run_app.bat
    ```
    
    Veya manuel olarak Docker Compose ile:
    ```bash
    docker-compose up -d --build
    ```

3.  **Erişim:**
    Tarayıcınızdan `http://localhost:8501` adresine gidin.

## ☁️ OpenShift / Kubernetes Deployment

Bu proje, OpenShift üzerinde **rootless** (root olmayan kullanıcı) olarak çalışacak şekilde yapılandırılmıştır.

`Dockerfile`, OpenShift'in rastgele UID atama politikasına (Arbitrary UID Support) uyumludur.
*   Uygulama dizini `/app` ve alt dizinleri `root` grubuna (GID 0) aittir ve yazma iznine sahiptir.
*   Container varsayılan olarak `USER 1001` ile çalışır.

## ⚙️ Yapılandırma

Uygulama ayarları `Ayarlar` menüsü üzerinden yönetilebilir. 

*   **FMG Bağlantısı:** FortiManager IP adresi ve API Token bilgileri arayüzden girilebilir.
*   **LDAP Ayarları:** Active Directory sunucu bilgileri ve grup eşleştirmeleri yapılabilir.

## 📂 Proje Yapısı

```
FORTICAM/
├── src/                # Kaynak kodlar (Python/Streamlit)
│   ├── app.py          # Ana uygulama dosyası
│   ├── api_client.py   # FortiManager API istemcisi
│   ├── auth_service.py # Kimlik doğrulama servisi
│   └── ui_components.py# UI bileşenleri
├── MFA Logo/           # Logo dosyaları
├── MFA Background/     # Arka plan görselleri
├── docker-compose.yml  # Docker servis tanımı
├── Dockerfile          # Docker imaj tanımı
└── requirements.txt    # Python bağımlılıkları
```

## 📝 Lisans

Bu proje [MIT](LICENSE) lisansı ile lisanslanmıştır.
# 🛡️ FORTICAM - FortiManager Interface Controller

**FORTICAM**, FortiManager sistemlerini yönetmek, port durumlarını kontrol etmek ve güvenli erişim sağlamak için geliştirilmiş, kullanıcı dostu bir arayüzdür.

![Login Screen](login_page.png)

## ☁️ OpenShift / Kubernetes Deployment

Bu proje, OpenShift (veya diğer Kubernetes ortamları) üzerinde **rootless** (root olmayan kullanıcı) olarak çalışacak şekilde yapılandırılmıştır.

`Dockerfile`, OpenShift'in rastgele UID atama politikasına (Arbitrary UID Support) uyumludur.
*   Uygulama dizini `/app` ve alt dizinleri `root` grubuna (GID 0) aittir ve yazma iznine sahiptir.
*   Container varsayılan olarak `USER 1001` ile çalışır, ancak OpenShift bunu dinamik bir UID ile ezebilir.
*   `fmg_config.json` gibi çalışma anında oluşturulan dosyalar için gerekli izinler ayarlanmıştır.

**Deployment Örneği (YAML) - Ayarlar Dahil:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forticam
spec:
  replicas: 1
  selector:
    matchLabels:
      app: forticam
  template:
    metadata:
      labels:
        app: forticam
    spec:
      containers:
      - name: forticam
        image: quay.mfa.gov.tr/admin/forti/fortimanager:v1.1.0
        ports:
        - containerPort: 8501
        env:
        # Uygulama Ayarlari (Environment Variables ile Kalicilik)
        - name: FMG_IP
          value: "10.10.10.10" # FortiManager IP
        - name: FMG_TOKEN
          value: "S3cretT0ken!" # API Token
        - name: CONNECTIVITY_HOST
          value: "mfa.gov.tr"   # Baglanti Testi Hedefi
        - name: LDAP_ENABLED
          value: "true"
        - name: LDAP_SERVER
          value: "dc01.mfa.gov.tr"
        - name: LDAP_BASE_DN
          value: "DC=mfa,DC=gov,DC=tr"
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
```

## ⚙️ Yapılandırma
Uygulama ayarları `config_service.py` ve arayüz üzerinden yönetilebilir. İlk çalıştırıldığında `fmg_config.json` dosyası oluşturulur.

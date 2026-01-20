FROM python:3.9-slim

# OpenShift icin gerekli izin ayarlari
# Uygulama dizinini olustur
WORKDIR /app

# Gerekli dosyalari kopyala (Bosluklu klasorler icin JSON array syntax kullanilmali)
COPY requirements.txt .
COPY src/ ./src/
<<<<<<< HEAD
COPY ["MFA Logo/", "./MFA Logo/"]
COPY ["MFA Background/", "./MFA Background/"]
COPY .streamlit/ ./.streamlit/
=======
COPY ["MFA Background/", "./MFA Background/"]
COPY ["MFA Logo/", "./MFA Logo/"]
>>>>>>> 319bca179de9f662d0468990c36635055a14ec1e

# Bagimliliklari yukle
RUN pip install --no-cache-dir -r requirements.txt

# OpenShift uyumlulugu icin izinleri ayarla
# OpenShift rastgele bir UID ile calisir ancak GID 0 (root) grubuna dahildir.
# Bu nedenle dizinlerin root grubuna yazma izni olmalidir.
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

# Streamlit config dizini icin izinler
RUN mkdir -p /app/.streamlit && \
    mkdir -p /app/data && \
    chgrp -R 0 /app/.streamlit /app/data && \
    chmod -R g=u /app/.streamlit /app/data

# Streamlit portunu disari ac
EXPOSE 8501

# Container'i non-root user (1001) olarak calistir
# Ancak OpenShift bunu ezecektir, onemli olan dosya izinleridir.
USER 1001

# Uygulamayi baslat
CMD ["streamlit", "run", "src/app.py", "--server.address=0.0.0.0"]

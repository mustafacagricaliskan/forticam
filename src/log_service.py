import csv
import os
import datetime
import pytz
import sys
import socket
import json
import streamlit as st
import pandas as pd
from config_service import ConfigService

# Data directory for OpenShift persistence
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

LOG_FILE = os.path.join(DATA_DIR, "audit_logs.csv")

class LogService:
    """Merkezi loglama servisi."""
    
    @staticmethod
    def check_siem_connection(server: str, port: int, protocol: str):
        """SIEM Sunucusuna bağlantı durumunu kontrol eder."""
        if not server or not port:
            return False, "Sunucu veya Port bilgisi eksik."
        
        try:
            if protocol == "TCP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2) # 2 saniye timeout
                result = sock.connect_ex((server, int(port)))
                sock.close()
                
                if result == 0:
                    return True, "Erişilebilir (TCP)"
                else:
                    return False, f"Erişilemedi (Hata Kodu: {result})"
            else:
                # UDP Connectionless oldugu icin kesin 'baglandi' diyemeyiz
                # Ancak DNS cozumleme hatasi var mi diye bakabiliriz
                try:
                    socket.gethostbyname(server)
                    return True, "UDP Modu (Stateless) - Hazır"
                except socket.gaierror:
                    return False, "Sunucu Adresi Çözülemedi (DNS Hatası)"
                    
        except Exception as e:
            return False, f"Bağlantı Hatası: {str(e)}"

    @staticmethod
    def send_to_siem(log_data: dict, siem_config: dict = None):
        """Log verisini Syslog üzerinden SIEM'e gönderir.
        
        Args:
            log_data (dict): Gönderilecek log verisi.
            siem_config (dict, optional): Önceden yüklenmiş SIEM ayarları. 
                                          Verilmezse diskten okunur. Performans için loop içinde verilmeli.
        """
        if siem_config is None:
            cfg = ConfigService.load_config()
            siem_config = cfg.get("siem_settings", {})
        
        if not siem_config.get("enabled"):
            return
            
        server = siem_config.get("server")
        port = siem_config.get("port", 514)
        protocol = siem_config.get("protocol", "UDP")
        
        if not server:
            return

        try:
            # CEF benzeri veya JSON formatında log oluştur
            # SIEM sistemleri genellikle JSON'u kolay parse eder
            message = json.dumps(log_data)
            
            if protocol == "UDP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(message.encode('utf-8'), (server, int(port)))
            else: # TCP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((server, int(port)))
                sock.sendall((message + "\n").encode('utf-8'))
                sock.close()
        except Exception as e:
            print(f"SIEM Send Error: {e}")

    @staticmethod
    def send_test_message(user_name: str, server: str, port: int, protocol: str):
        """Test amaçlı SIEM logu gönderir (CSV'ye yazmaz)."""
        from typing import Tuple
        
        # Timezone handled in log_action usually, repeated here or we can skip strictly
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "Timestamp": timestamp,
            "User": user_name,
            "Action": "SIEM_TEST",
            "Device": "SYSTEM",
            "Details": "Connection Test Message"
        }
        
        # Gecici config
        temp_config = {
            "enabled": True,
            "server": server,
            "port": port,
            "protocol": protocol
        }
        
        try:
            LogService.send_to_siem(log_entry, siem_config=temp_config)
            return True, "Test logu gönderildi."
        except Exception as e:
            return False, f"Gönderim Hatası: {e}"

    @staticmethod
    def log_action(user_name: str, action: str, device: str, details: str):
        """Kullanıcı işlemini loglar, dosyaya yazar ve konsola basar."""
        tz_name = st.session_state.get('user_timezone', 'Europe/Istanbul')
        try:
            tz = pytz.timezone(tz_name)
        except:
            tz = pytz.utc
            
        timestamp = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # Log verisi (Hem CSV hem SIEM için ortak)
        log_entry = {
            "Timestamp": timestamp,
            "User": user_name,
            "Action": action,
            "Device": device,
            "Details": str(details)
        }

        # 1. KONSOL LOGU (Container Logs icin)
        log_msg = f"[{timestamp}] [{user_name}] [{action}] Device:{device} - {details}"
        print(log_msg, file=sys.stdout, flush=True)

        # 2. DOSYA LOGU (CSV)
        file_exists = os.path.exists(LOG_FILE)
        try:
            with open(LOG_FILE, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Timestamp", "User", "Action", "Device", "Details"])
                
                writer.writerow([timestamp, user_name, action, device, str(details)])
                f.flush()
                os.fsync(f.fileno())
                
            # 3. SIEM GÖNDERİMİ
            LogService.send_to_siem(log_entry)

        except Exception as e:
            print(f"Log Error: {e}")

    @staticmethod
    def export_past_logs_to_siem():
        """Mevcut CSV'deki tüm geçmiş logları SIEM'e gönderir."""
        logs = LogService.get_logs()
        if logs.empty:
            return False, "Gönderilecek geçmiş log bulunamadı."
        
        cfg = ConfigService.load_config()
        siem_cfg = cfg.get("siem_settings", {})
        
        if not siem_cfg.get("enabled"):
            return False, "SIEM entegrasyonu aktif değil. Lütfen önce ayarları yapıp kaydedin."

        count = 0
        try:
            # Dataframe'i dict listesine cevir
            records = logs.to_dict(orient='records')
            for record in records:
                # OPTIMIZATION: Config'i tekrar tekrar okumamak icin parametre olarak geciyoruz
                LogService.send_to_siem(record, siem_config=siem_cfg)
                count += 1
                # Cok hizli gonderip UDP bufferi sisirmemek icin minik bekleme
                if count % 10 == 0: 
                    import time
                    time.sleep(0.05)
            
            return True, f"{count} adet geçmiş log kaydı SIEM'e aktarıldı."
        except Exception as e:
            return False, f"Aktarım sırasında hata: {e}"

    @staticmethod
    def get_logs() -> pd.DataFrame:
        """Logları okur."""
        if not os.path.exists(LOG_FILE):
            return pd.DataFrame(columns=["Timestamp", "User", "Action", "Device", "Details"])
        
        try:
            return pd.read_csv(LOG_FILE, on_bad_lines='skip')
        except Exception:
            return pd.DataFrame(columns=["Timestamp", "User", "Action", "Device", "Details"])

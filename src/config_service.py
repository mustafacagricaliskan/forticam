import json
import os
import streamlit as st

# Data directory for OpenShift persistence
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "fmg_config.json")

class ConfigService:
    """Uygulama ayarlarını yöneten servis."""
    
    @staticmethod
    def load_config():
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except:
                pass
        
        # --- Environment Variables Override ---
        # Eger Ortam Degiskeni varsa, config dosyasini ezer.
        
        # 1. FMG Ayarlari
        if os.getenv("FMG_IP"):
            config["fmg_ip"] = os.getenv("FMG_IP")
        if os.getenv("FMG_TOKEN"):
            config["api_token"] = os.getenv("FMG_TOKEN")
            
        # 2. Connectivity Host
        if os.getenv("CONNECTIVITY_HOST"):
            config["connectivity_check_host"] = os.getenv("CONNECTIVITY_HOST")
        elif "connectivity_check_host" not in config:
            config["connectivity_check_host"] = "mfa.gov.tr"

        # 3. LDAP Ayarlari (Basit)
        if "ldap_settings" not in config:
            config["ldap_settings"] = {
                "enabled": False,
                "servers": ["192.168.1.10"],
                "port": 636,
                "use_ssl": True,
                "base_dn": "dc=example,dc=com",
                "mappings": []
            }
            
        if os.getenv("LDAP_ENABLED"):
            config["ldap_settings"]["enabled"] = str(os.getenv("LDAP_ENABLED")).lower() == "true"
        if os.getenv("LDAP_SERVER"):
            config["ldap_settings"]["servers"] = [os.getenv("LDAP_SERVER")]
        if os.getenv("LDAP_BASE_DN"):
            config["ldap_settings"]["base_dn"] = os.getenv("LDAP_BASE_DN")

        # --- Default Values Init (Geri Kalanlar) ---
        if "admin_profiles" not in config:
            config["admin_profiles"] = [
                {
                    "name": "Super_User", 
                    "permissions": {
                        "Dashboard": 2, "System": 2, "Logs": 2
                    }
                },
                {
                    "name": "Standard_User", 
                    "permissions": {
                        "Dashboard": 2, "System": 0, "Logs": 1
                    }
                },
                {
                    "name": "Read_Only", 
                    "permissions": {
                        "Dashboard": 1, "System": 0, "Logs": 1
                    }
                }
            ]
            
        if "local_accounts" not in config:
            config["local_accounts"] = [
                {"user": "admin", "password": "admin", "profile": "Super_User"},
                {"user": "operator", "password": "operator", "profile": "Standard_User"}
            ]

        if "email_settings" not in config:
            config["email_settings"] = {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "receiver_emails": []
            }
        
        if "siem_settings" not in config:
            config["siem_settings"] = {
                "enabled": False,
                "server": "",
                "port": 514,
                "protocol": "UDP"
            }
        
        if "connectivity_check_host" not in config:
            config["connectivity_check_host"] = "mfa.gov.tr"
            
        return config

    @staticmethod
    def save_config(data: dict):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            st.error(f"Config Save Error: {e}")

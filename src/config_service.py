import json
import os
import streamlit as st
import logging
from typing import Any, Dict

# Logger
logger = logging.getLogger(__name__)

# Data directory for OpenShift persistence
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "fmg_config.json")

class ConfigService:
    """Uygulama ayarlarını yöneten servis."""
    
    @staticmethod
    def get_env_or_config(config: Dict[str, Any], key: str, env_var: str, default: Any = None) -> Any:
        """Önce Environment Variable, sonra config, en son default döner."""
        val = os.getenv(env_var)
        if val is not None:
            # Boolean donusumu
            if isinstance(default, bool):
                return str(val).lower() == "true"
            return val
        return config.get(key, default)

    @staticmethod
    def load_config() -> Dict[str, Any]:
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Config Load Error: {e}")
        
        # --- MIGRATION: FMG Settings Grouping ---
        if "fmg_settings" not in config:
            config["fmg_settings"] = {
                "ip": config.pop("fmg_ip", ""),
                "token": config.pop("api_token", "")
            }
            # Kaydetmeye gerek yok, save_config cagirildiginda veya bellekten kullanildiginda duzelir.
            # Ancak kalicilik icin hemen kaydetmek daha iyi olabilir ama burada IO yapmayalim.
        
        # --- Environment Variables & Defaults ---
        fmg = config["fmg_settings"]
        
        # 1. FMG Ayarlari (Yeni Yapi)
        fmg["ip"] = ConfigService.get_env_or_config(fmg, "ip", "FMG_IP", "")
        fmg["token"] = ConfigService.get_env_or_config(fmg, "token", "FMG_TOKEN", "")
            
        # 2. Connectivity Host
        config["connectivity_check_host"] = ConfigService.get_env_or_config(config, "connectivity_check_host", "CONNECTIVITY_HOST", "mfa.gov.tr")

        # 3. LDAP Ayarlari
        if "ldap_settings" not in config:
            config["ldap_settings"] = {
                "enabled": False,
                "servers": ["192.168.1.10"],
                "port": 636,
                "use_ssl": True,
                "base_dn": "dc=example,dc=com",
                "mappings": []
            }
            
        ldap = config["ldap_settings"]
        ldap["enabled"] = ConfigService.get_env_or_config(ldap, "enabled", "LDAP_ENABLED", ldap.get("enabled", False))
        
        env_ldap_server = os.getenv("LDAP_SERVER")
        if env_ldap_server:
            ldap["servers"] = [env_ldap_server]
            
        ldap["base_dn"] = ConfigService.get_env_or_config(ldap, "base_dn", "LDAP_BASE_DN", ldap.get("base_dn", ""))

        # 4. Admin Profiles (Defaults)
        if "admin_profiles" not in config:
            config["admin_profiles"] = [
                {"name": "Super_User", "permissions": {"Dashboard": 2, "System": 2, "Logs": 2}},
                {"name": "Standard_User", "permissions": {"Dashboard": 2, "System": 0, "Logs": 1}},
                {"name": "Read_Only", "permissions": {"Dashboard": 1, "System": 0, "Logs": 1}}
            ]
            
        # 5. Local Accounts (Defaults)
        if "local_accounts" not in config:
            config["local_accounts"] = [
                {"user": "admin", "password": "admin", "profile": "Super_User"},
                {"user": "operator", "password": "operator", "profile": "Standard_User"}
            ]

        # 6. SIEM Settings
        if "siem_settings" not in config:
            config["siem_settings"] = {
                "enabled": False,
                "server": "",
                "port": 514,
                "protocol": "UDP"
            }
            
        # 7. Port Toggle Method (Default: db_update)
        if "toggle_method" not in config:
            config["toggle_method"] = "db_update"
            
        return config

    @staticmethod
    def save_config(data: Dict[str, Any]):
        """Atomic write ile konfigürasyonu kaydeder."""
        tmp_file = f"{CONFIG_FILE}.tmp"
        try:
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno()) # Diske yazildigindan emin ol
            
            # Basariliysa asil dosyanin uzerine yaz
            if os.path.exists(CONFIG_FILE):
                os.replace(tmp_file, CONFIG_FILE)
            else:
                os.rename(tmp_file, CONFIG_FILE)
                
        except Exception as e:
            logger.error(f"Config Save Error: {e}")
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            st.error(f"Ayarlar kaydedilemedi: {e}")
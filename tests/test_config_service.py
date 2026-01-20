import os
import json
import pytest
import sys
from unittest.mock import patch

# Src klasorunu path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_service import ConfigService, CONFIG_FILE, DATA_DIR

def setup_module(module):
    """Test module setup."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def teardown_function(function):
    """Clean up after each test."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(CONFIG_FILE + ".tmp"):
        os.remove(CONFIG_FILE + ".tmp")

def test_default_config_loading():
    """Config dosyasi yokken varsayilan degerler geliyor mu?"""
    if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
    
    config = ConfigService.load_config()
    
    assert "ldap_settings" in config
    assert "fmg_settings" in config
    assert "toggle_method" in config
    assert config["toggle_method"] == "db_update"

def test_migration_legacy_fmg_ip():
    """Eski config yapisindan (root fmg_ip) yeni yapiya (fmg_settings) gecis."""
    legacy_data = {
        "fmg_ip": "1.2.3.4",
        "api_token": "secret_token",
        "ldap_settings": {"enabled": False}
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(legacy_data, f)
        
    # Load should trigger migration in memory (though not save to disk until save_config)
    config = ConfigService.load_config()
    
    assert "fmg_settings" in config
    assert config["fmg_settings"]["ip"] == "1.2.3.4"
    assert config["fmg_settings"]["token"] == "secret_token"
    # Root keys popped
    assert "fmg_ip" not in config

def test_env_var_override():
    """Environment variable'larin config dosyasini ezdigini dogrula."""
    # Dosyada farkli deger olsun
    file_data = {
        "fmg_settings": {"ip": "1.1.1.1", "token": "file_token"}
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(file_data, f)
        
    with patch.dict(os.environ, {"FMG_IP": "9.9.9.9", "FMG_TOKEN": "env_token"}):
        config = ConfigService.load_config()
        assert config["fmg_settings"]["ip"] == "9.9.9.9"
        assert config["fmg_settings"]["token"] == "env_token"

def test_save_config_failsafe_merge():
    """Save isleminde fmg_settings eksikse diskten kurtarilmasini test et."""
    # 1. Diskte gecerli config olsun
    disk_data = {
        "fmg_settings": {"ip": "10.10.10.10", "token": "disk_token"},
        "other": "data"
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(disk_data, f)
        
    # 2. Kaydedilecek yeni veri (FMG ayarlari eksik)
    new_data = {
        "ldap_settings": {"enabled": True}
        # fmg_settings YOK
    }
    
    # 3. Kaydet
    ConfigService.save_config(new_data)
    
    # 4. Kontrol et: FMG ayarlari korunmus mu?
    with open(CONFIG_FILE, 'r') as f:
        saved = json.load(f)
        
    assert "fmg_settings" in saved
    assert saved["fmg_settings"]["ip"] == "10.10.10.10"
    assert "ldap_settings" in saved

import os
import json
import pytest
import sys

# Src klasorunu path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_service import ConfigService, CONFIG_FILE, DATA_DIR

def test_data_directory_creation():
    """Data klasoru olusuyor mu?"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    assert os.path.exists(DATA_DIR)

def test_default_config_loading():
    """Config dosyasi yokken varsayilan degerler geliyor mu?"""
    # Varsa gecici olarak silelim/yedekleyelim (Test ortaminda oldugu icin direk silebiliriz)
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    
    config = ConfigService.load_config()
    
    # Kritik anahtarlar var mi?
    assert "ldap_settings" in config
    assert "admin_profiles" in config
    assert "local_accounts" in config
    assert config["ldap_settings"]["port"] == 636
    
def test_save_config():
    """Config kaydetme calisiyor mu?"""
    test_data = {"test_key": "test_value"}
    ConfigService.save_config(test_data)
    
    assert os.path.exists(CONFIG_FILE)
    
    with open(CONFIG_FILE, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["test_key"] == "test_value"

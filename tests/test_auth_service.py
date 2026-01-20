import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from auth_service import User, AuthService

def test_user_permissions_admin():
    """Admin her yere erisebilmeli"""
    admin = User("admin", "Super_User")
    # Rastgele bir cihaz ve port
    assert admin.has_access_to_port("FGT-Test", "port1") == True

def test_user_permissions_whitelist():
    """Standart kullanici sadece izin verilen porta erisebilmeli"""
    # Senaryo: User sadece FGT-1 cihazinda port2'ye yetkili
    global_ports = []
    device_ports = {"FGT-1": ["port2"]}
    
    user = User("testuser", "Standard_User", global_allowed_ports=global_ports, device_allowed_ports=device_ports)
    
    # Yetkili oldugu port
    assert user.has_access_to_port("FGT-1", "port2") == True
    
    # Yetkili OLMADIGI port
    assert user.has_access_to_port("FGT-1", "port3") == False
    
    # Baska cihaz
    assert user.has_access_to_port("FGT-2", "port2") == False

def test_user_permissions_global():
    """Global izinler her cihazda calismali"""
    global_ports = ["mgmt"]
    user = User("globaluser", "Standard_User", global_allowed_ports=global_ports)
    
    assert user.has_access_to_port("AnyDevice1", "mgmt") == True
    assert user.has_access_to_port("AnyDevice2", "mgmt") == True
    assert user.has_access_to_port("AnyDevice1", "port1") == False

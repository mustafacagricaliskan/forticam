import pytest
from unittest.mock import MagicMock, patch
from src.auth_service import AuthService, User

class TestAuthServiceConnectivity:

    @patch('src.auth_service.socket')
    def test_check_ldap_connectivity_success(self, mock_socket):
        mock_socket.socket.return_value.__enter__.return_value.connect.return_value = None
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "ldap_settings": {
                    "enabled": True,
                    "servers": ["10.0.0.2"],
                    "port": 636
                }
            }
            status, message = AuthService.check_ldap_connectivity()
            assert status is True
            assert "LDAP Reachable" in message

    @patch('src.auth_service.socket')
    def test_check_ldap_connectivity_failure(self, mock_socket):
        mock_socket.socket.return_value.__enter__.return_value.connect.side_effect = Exception("Timeout")
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "ldap_settings": {
                    "enabled": True,
                    "servers": ["10.0.0.2"],
                    "port": 636
                }
            }
            status, message = AuthService.check_ldap_connectivity()
            assert status is False
            assert "LDAP Unreachable" in message

    def test_check_ldap_connectivity_disabled(self):
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {"ldap_settings": {"enabled": False}}
            status, message = AuthService.check_ldap_connectivity()
            assert status is False
            assert "LDAP Disabled" in message

class TestAuthServiceLogin:
    @patch('src.auth_service.bcrypt')
    @patch('src.auth_service.st')
    def test_login_local_success(self, mock_st, mock_bcrypt):
        # Setup mock session state
        mock_st.session_state = {}
        
        # Setup mock config
        fake_hash = b'$2b$12$fakehash'
        mock_bcrypt.checkpw.return_value = True
        
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "local_accounts": [
                    {"user": "admin", "password": "hashed_secret", "profile": "Super_User"}
                ],
                "ldap_settings": {"enabled": False}
            }
            
            # Action
            success, msg = AuthService.login("admin", "secret")
            
            # Verify
            assert success is True
            # AuthService.login sets session_state['current_user']
            assert mock_st.session_state['current_user'].username == "admin"

    @patch('src.auth_service.bcrypt')
    def test_login_local_fail_password(self, mock_bcrypt):
        mock_bcrypt.checkpw.return_value = False
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "local_accounts": [{"user": "admin", "password": "hashed_secret", "profile": "Super_User"}],
                "ldap_settings": {"enabled": False}
            }
            success, msg = AuthService.login("admin", "wrong")
            assert success is False
            assert "Kullanıcı bulunamadı veya LDAP kapalı" in msg

    def test_login_local_user_not_found(self):
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "local_accounts": [],
                "ldap_settings": {"enabled": False}
            }
            success, msg = AuthService.login("ghost", "secret")
            assert success is False
            # Generic message when user not found locally and LDAP disabled
            assert "bulunamadı" in msg.lower() or "kapalı" in msg.lower()

class TestUserRBAC:
    def test_has_access_to_port_admin(self):
        u = User("admin", "Super_User")
        assert u.has_access_to_port("any_device", "any_port") is True

    def test_has_access_to_port_whitelist(self):
        # User logic reloads config, so we must mock it
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "local_accounts": [
                    {
                        "user": "operator", 
                        "profile": "Standard_User",
                        "global_allowed_ports": ["lan1", "wan1"],
                        "device_allowed_ports": {"FW01": ["dmz"]}
                    }
                ],
                "ldap_settings": {"enabled": False}
            }
            
            u = User("operator", "Standard_User")
            
            # Check logic
            assert u.has_access_to_port("FW01", "lan1") is True # Global match
            assert u.has_access_to_port("FW01", "dmz") is True # Device match
            assert u.has_access_to_port("FW01", "lan2") is False # No match
            assert u.has_access_to_port("FW02", "dmz") is False # Device mismatch
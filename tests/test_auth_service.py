import pytest
from unittest.mock import MagicMock, patch
from src.auth_service import AuthService

class TestAuthServiceConnectivity:

    @patch('src.auth_service.socket')
    def test_check_ldap_connectivity_success(self, mock_socket):
        # Setup mock for socket connection (success)
        mock_socket.socket.return_value.__enter__.return_value.connect.return_value = None
        
        # Mock ConfigService to return valid config
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "ldap_settings": {
                    "enabled": True,
                    "servers": ["10.0.0.2"],
                    "port": 636
                }
            }
            
            # Test
            status, message = AuthService.check_ldap_connectivity()
            
            # Verify
            assert status is True
            assert "LDAP Reachable" in message

    @patch('src.auth_service.socket')
    def test_check_ldap_connectivity_failure(self, mock_socket):
        # Setup mock for socket connection (failure)
        mock_socket.socket.return_value.__enter__.return_value.connect.side_effect = Exception("Timeout")
        
        # Mock ConfigService
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "ldap_settings": {
                    "enabled": True,
                    "servers": ["10.0.0.2"],
                    "port": 636
                }
            }
            
            # Test
            status, message = AuthService.check_ldap_connectivity()
            
            # Verify
            assert status is False
            assert "LDAP Unreachable" in message

    def test_check_ldap_connectivity_disabled(self):
        # Mock ConfigService
        with patch('src.auth_service.ConfigService.load_config') as mock_config:
            mock_config.return_value = {
                "ldap_settings": {
                    "enabled": False
                }
            }
            
            # Test
            status, message = AuthService.check_ldap_connectivity()
            
            # Verify
            assert status is False
            assert "LDAP Disabled" in message
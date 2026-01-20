import pytest
from unittest.mock import MagicMock, patch
from src.system_service import SystemService
from src.api_client import FortiManagerAPI

class TestSystemServiceConnectivity:

    @patch('src.system_service.FortiManagerAPI')
    def test_check_fmg_connectivity_success(self, MockAPI):
        # Setup mock
        mock_api_instance = MockAPI.return_value
        mock_api_instance.login.return_value = True
        
        # Test
        status, message = SystemService.check_fmg_connectivity("10.0.0.1", "fake-token")
        
        # Verify
        assert status is True
        assert "Successful" in message
        MockAPI.assert_called_with(fmg_ip="10.0.0.1", api_token="fake-token", verify_ssl=False, timeout=5)
        mock_api_instance.login.assert_called_once()

    @patch('src.system_service.FortiManagerAPI')
    def test_check_fmg_connectivity_failure(self, MockAPI):
        # Setup mock
        mock_api_instance = MockAPI.return_value
        mock_api_instance.login.return_value = False
        
        # Test
        status, message = SystemService.check_fmg_connectivity("10.0.0.1", "fake-token")
        
        # Verify
        assert status is False
        assert "Failed" in message
        mock_api_instance.login.assert_called_once()

    @patch('src.system_service.FortiManagerAPI')
    def test_check_fmg_connectivity_exception(self, MockAPI):
        # Setup mock to raise exception
        MockAPI.side_effect = Exception("Connection Refused")
        
        # Test
        status, message = SystemService.check_fmg_connectivity("10.0.0.1", "fake-token")
        
        # Verify
        assert status is False
        assert "Connection Refused" in message

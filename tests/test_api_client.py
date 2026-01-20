import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from api_client import FortiManagerAPI

@pytest.fixture
def mock_api():
    """API Client ornegi, requestler mocklanmis."""
    with patch('api_client.requests.post') as mock_post:
        # Token ile baslat, boylece login() metodu token kontrolune girer
        api = FortiManagerAPI("1.1.1.1", api_token="dummy_token", verify_ssl=False)
        yield api, mock_post

def test_login_success(mock_api):
    api, mock_post = mock_api
    
    # Mock Response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [{"status": {"code": 0, "message": "OK"}}]
    }
    mock_post.return_value = mock_response
    
    result = api.login()
    assert result == True

def test_get_devices(mock_api):
    api, mock_post = mock_api
    
    # Cihaz listesi donen API yaniti
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "data": [
                    {"name": "Firewall-A", "os_ver": "7.0"},
                    {"name": "Firewall-B", "os_ver": "7.2"}
                ],
                "status": {"code": 0}
            }
        ]
    }
    mock_post.return_value = mock_response
    
    devices = api.get_devices()
    assert devices is not None
    assert len(devices) == 2
    assert devices[0]['name'] == "Firewall-A"

def test_toggle_interface(mock_api):
    api, mock_post = mock_api
    
    # 1. Adim: DB Update Basarili Yaniti
    mock_update_resp = MagicMock()
    mock_update_resp.status_code = 200
    mock_update_resp.json.return_value = {
        "result": [{"status": {"code": 0}, "data": {}}]
    }

    # 2. Adim: Install Config Basarili Yaniti
    mock_install_resp = MagicMock()
    mock_install_resp.status_code = 200
    mock_install_resp.json.return_value = {
        "result": [{"status": {"code": 0}, "data": {"task": 999}}]
    }
    
    # Mock side_effect: Sirasiyla response don
    mock_post.side_effect = [mock_update_resp, mock_install_resp]
    
    success, msg = api.toggle_interface("FGT-1", "port1", "up")
    
    assert success == True
    assert "Task: 999" in msg
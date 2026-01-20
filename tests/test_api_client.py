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
    # We need to mock requests.Session.post because the client uses a session object
    with patch('requests.Session.post') as mock_post:
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
    
    # Check GET calls first (path discovery), then UPDATE, then VERIFY GET, then INSTALL EXEC
    # This logic in toggle_interface is complex with multiple calls.
    
    # Simplified mock sequence for a successful path found on first try:
    # 1. GET (Check path) -> Success
    # 2. UPDATE -> Success
    # 3. GET (Verify) -> Success with new status
    # 4. EXEC (Install) -> Success
    
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {
        "result": [{"status": {"code": 0}, "data": {"status": 1}}] # 1 = up
    }
    
    mock_update_resp = MagicMock()
    mock_update_resp.status_code = 200
    mock_update_resp.json.return_value = {
        "result": [{"status": {"code": 0}, "data": {}}]
    }

    mock_install_resp = MagicMock()
    mock_install_resp.status_code = 200
    mock_install_resp.json.return_value = {
        "result": [{"status": {"code": 0}, "data": {"task": 999}}]
    }
    
    # Order of calls:
    # 1. GET (Path 1 check)
    # 2. UPDATE
    # 3. GET (Verify)
    # 4. EXEC (Install)
    
    mock_post.side_effect = [mock_get_resp, mock_update_resp, mock_get_resp, mock_install_resp]
    
    success, msg = api.toggle_interface("FGT-1", "port1", "up")
    
    assert success == True
    assert "Task: 999" in msg

def test_get_interfaces_with_adom(mock_api):
    api, mock_post = mock_api
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "data": [
                    {"name": "lan2", "status": 1}
                ],
                "status": {"code": 0}
            }
        ]
    }
    mock_post.return_value = mock_response
    
    # Call with ADOM
    ifaces = api.get_interfaces("FGT-1", vdom="root", adom="MyAdom")
    
    assert len(ifaces) == 1
    assert ifaces[0]['name'] == "lan2"
    
    # Verify that the correct URL with ADOM was called
    # The first call should be to the ADOM path
    args, kwargs = mock_post.call_args
    request_json = kwargs['json']
    assert "/pm/config/adom/MyAdom/device/FGT-1/vdom/root/system/interface" in request_json['params'][0]['url']

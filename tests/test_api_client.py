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

def test_proxy_update_interface(mock_api):
    api, mock_post = mock_api
    
    # Mock proxy success response
    # FMG Proxy returns a nested structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "status": {"code": 0},
                "data": [
                    {
                        "response": {
                            "http_status": 200,
                            "results": {"status": "success"}
                        }
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_response
    
    success, msg = api.proxy_update_interface("FGT-1", "lan2", "down")
    
    assert success is True
    assert "Direct Update Success" in msg
    
    # Verify payload
    args, kwargs = mock_post.call_args
    req = kwargs['json']
    assert req['params'][0]['url'] == "/sys/proxy/json"
    assert req['params'][0]['data']['action'] == "put"
    assert req['params'][0]['data']['resource'] == "/api/v2/cmdb/system/interface/lan2"

def test_get_interfaces_realtime(mock_api):
    api, mock_post = mock_api
    
    # Mock Monitor API response via Proxy
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "status": {"code": 0},
                "data": [
                    {
                        "response": {
                            "results": [
                                {"name": "port1", "status": "up", "link_status": "up", "ip": "1.1.1.1"},
                                {"name": "port2", "status": "down", "link_status": "down"}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_response
    
    ifaces = api.get_interfaces_realtime("FGT-1", "root", "root")
    
    assert ifaces is not None
    assert len(ifaces) == 2
    # Check mapping logic
    assert ifaces[0]['name'] == "port1"
    assert ifaces[0]['status'] == 1 # up -> 1
    assert ifaces[1]['status'] == 0 # down -> 0

def test_toggle_interface_script_mode(mock_api):
    """Test toggle_interface with use_script=True (which triggers Proxy mode)."""
    api, mock_post = mock_api
    
    # Reuse proxy success response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "status": {"code": 0},
                "data": [
                    {
                        "response": {
                            "http_status": 200,
                            "results": {}
                        }
                    }
                ]
            }
        ]
    }
    mock_post.return_value = mock_response
    
    success, msg = api.toggle_interface("FGT-1", "lan2", "down", use_script=True)
    
    assert success is True
    # Should call proxy_update_interface internally
    args, kwargs = mock_post.call_args
    req = kwargs['json']
    assert req['params'][0]['url'] == "/sys/proxy/json"
    assert req['params'][0]['data']['action'] == "put"

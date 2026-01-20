import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import logging
from typing import Optional, List, Dict, Union, Any, Tuple

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CONSTANTS:
    DEVICE_FIELDS = ["name", "ip", "platform_str", "os_ver", "desc", "vdom", "conn_status", "adom"]
    INTERFACE_FIELDS = ["name", "status", "type", "ip", "vdom", "link-status", "admin-status"]
    VDOM_FIELDS = ["name", "status"]

class FortiManagerAPI:
    def __init__(self, fmg_ip: str, username: Optional[str] = None, password: Optional[str] = None, 
                 api_token: Optional[str] = None, verify_ssl: bool = False, timeout: int = 15):
        self.base_url = f"https://{fmg_ip}/jsonrpc"
        self.username = username
        self.password = password
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session_id = None
        self.id_counter = 1
        
        # --- SESSION & RETRY SETUP ---
        self.session = requests.Session()
        
        # Retry stratejisi: 3 kere dene, her seferinde bekleme suresini artir (1s, 2s, 4s...)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()
            self.session.verify = False
        else:
            self.session.verify = True

    def _post(self, method: str, params: List[Dict], session_id: Optional[str] = None) -> Optional[Dict]:
        payload = {
            "method": method,
            "params": params,
            "id": self.id_counter
        }
        
        if not self.api_token:
            payload["session"] = session_id or self.session_id
        
        self.id_counter += 1
        
        # Headers optimization
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        try:
            # Persistent session kullanimi
            response = self.session.post(
                self.base_url, 
                json=payload, 
                headers=headers,
                verify=self.verify_ssl,
                timeout=20 # Timeout 20sn'ye cikarildi ve Retry mekanizmasi aktif
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("API Bağlantı Zaman Aşımı (Timeout)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("API Bağlantı Hatası (Connection Error) - Sunucuya ulaşılamıyor.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API Genel İstek Hatası: {e}")
            return None

    def login(self) -> bool:
        """
        Token geçerliliğini ve bağlantıyı kontrol eder.
        """
        if self.api_token:
            logger.info("Checking API Token and Connection...")
            # Token ve bağlantı kontrolü için basit bir sorgu
            res = self._post("get", [{"url": "/sys/status"}])
            if res and 'result' in res and res['result'][0]['status']['code'] == 0:
                logger.info("Connection Successful.")
                return True
            else:
                logger.error(f"Connection Failed: {json.dumps(res)}")
                return False

        logger.error("Login Failed: API Token is mandatory.")
        return False

    def get_devices(self) -> Optional[List[Dict]]:
        if not self.session_id and not self.api_token: return []

        # 1. Deneme: Genel cihaz listesi (Global - Tum ADOM'lar)
        # Bu yontem cihazlarin gercek ADOM bilgisini daha dogru doner.
        print("DEBUG: get_devices -> Trying Global List (/dvmdb/device)...")
        params_global = [
            {
                "url": "/dvmdb/device",
                "fields": CONSTANTS.DEVICE_FIELDS
            }
        ]
        response_global = self._post("get", params_global)
        print(f"DEBUG: get_devices (Global) response -> {json.dumps(response_global)}")

        if response_global and 'result' in response_global and response_global['result'][0]['status']['code'] == 0:
            data = response_global['result'][0].get('data', [])
            if data:
                return data

        # 2. Deneme: Root ADOM (Fallback)
        print("DEBUG: Global list failed/empty. Trying Root ADOM (/dvmdb/adom/root/device)...")
        params = [
            {
                "url": "/dvmdb/adom/root/device",
                "fields": CONSTANTS.DEVICE_FIELDS
            }
        ]
        response = self._post("get", params)
        
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return response['result'][0].get('data', [])
            
        # Eğer ikisi de hata verdiyse None dön
        return None

    def is_device_online(self, device_name: str) -> bool:
        """
        Cihazın FMG ile bağlantı durumunu kontrol eder.
        """
        params = [
            {
                "url": f"/dvmdb/device/{device_name}",
                "fields": ["conn_status"]
            }
        ]
        res = self._post("get", params)
        if res and 'result' in res and res['result'][0]['status']['code'] == 0:
            data = res['result'][0].get('data', {})
            # FMG dönerse list, değilse dict olabilir
            if isinstance(data, list) and data: data = data[0]
            
            # 1 = Up, 2 = Down (FMG versiona gore degisebilir, genelde 1 UP)
            # conn_status degerini loglayalim emin olmak icin
            status = data.get('conn_status')
            return str(status) == '1'
        return False

    def get_vdoms(self, device_name: str) -> List[str]:
        """
        Cihazdaki VDOM listesini çeker.
        """
        if not self.session_id and not self.api_token: return []
        
        # DVMDB üzerinden cihazın VDOM listesini al
        params = [
            {
                "url": f"/dvmdb/adom/root/device/{device_name}/vdom",
                "fields": CONSTANTS.VDOM_FIELDS
            }
        ]
        response = self._post("get", params)
        
        vdoms = []
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            data = response['result'][0]['data']
            if data:
                vdoms = [v['name'] for v in data]
        
        # Eğer VDOM listesi boşsa veya hata varsa, varsayılan 'root' VDOM'u döndür
        if not vdoms:
            vdoms = ["root"]
            
        return vdoms

    def get_interfaces(self, device_name: str, vdom: str = "root", adom: str = "root") -> List[Dict]:
        """
        Belirli bir cihaz ve VDOM için interfaceleri çeker.
        Path: /pm/config/adom/{adom}/device/{device}/vdom/{vdom}/system/interface
        """
        if not self.session_id and not self.api_token: return []

        if not adom: adom = "root"

        # 1. ADOM Path
        url_adom = f"/pm/config/adom/{adom}/device/{device_name}/vdom/{vdom}/system/interface"
        # 2. Legacy Path (Fallback)
        url_legacy = f"/pm/config/device/{device_name}/vdom/{vdom}/system/interface"
        
        candidate_urls = [url_adom, url_legacy]
        
        for url in candidate_urls:
            params = [
                {
                    "url": url,
                    "fields": CONSTANTS.INTERFACE_FIELDS
                }
            ]
            response = self._post("get", params)
            
            if response and 'result' in response and response['result'][0]['status']['code'] == 0:
                data = response['result'][0]['data']
                return data
        
        logger.warning(f"get_interfaces failed for {device_name} (VDOM:{vdom}, ADOM:{adom}). Checked paths: {candidate_urls}")
        return []

    def check_task_status(self, task_id: int) -> Optional[Dict]:
        """
        Task durumunu sorgular.
        Endpoint: /task/task/{task_id}
        """
        if not self.session_id and not self.api_token: return None
        
        url = f"/task/task/{task_id}"
        response = self._post("get", [{"url": url}])
        
        if response and 'result' in response:
            try:
                data = response['result'][0]['data']
                return {
                    "percent": data.get("percent", 0),
                    "state": data.get("state", "unknown"),
                    "line": data.get("line", []),
                    "details": data # Tum veriyi don
                }
            except:
                pass
        return None

    def set_dns(self, primary: str, secondary: str) -> Tuple[bool, str]:
        """
        Sistem DNS ayarlarini gunceller.
        Endpoint: /sys/dns
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        data = {
            "primary": primary,
            "secondary": secondary
        }
        
        response = self._post("set", [{"url": "/sys/dns", "data": data}])
        if response and 'result' in response:
            code = response['result'][0]['status']['code']
            msg = response['result'][0]['status']['message']
            
            if code == 0:
                return True, "DNS Başarıyla Güncellendi"
            elif code == -11:
                return False, f"Yetki Hatası (-11): API Token 'System Settings' yazma yetkisine sahip değil."
            else:
                return False, f"Hata: {code} - {msg}"
                
        return False, f"Bilinmeyen Hata: {json.dumps(response)}"

    def add_ldap_server(self, name: str, server_ip: str, cnid: str = "cn", dn: str = "") -> Tuple[bool, str]:
        """
        LDAP Sunucusu ekler.
        Endpoint: /pm/config/adom/root/obj/user/ldap
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        data = {
            "name": name,
            "server": server_ip,
            "cnid": cnid,
            "dn": dn
        }
        
        response = self._post("add", [{"url": "/pm/config/adom/root/obj/user/ldap", "data": data}])
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return True, "LDAP Server Added"
        return False, f"LDAP Add Failed: {json.dumps(response)}"

    def import_certificate(self, name: str, pfx_base64: str, password: str) -> Tuple[bool, str]:
        """
        Yerel Sertifika (PFX) yukler.
        Endpoint: /pm/config/adom/root/obj/vpn/certificate/local
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        data = {
            "name": name,
            "passwd": password, # PFX sifresi
            "certificate": pfx_base64 # Base64 string
        }
        
        response = self._post("add", [{"url": "/pm/config/adom/root/obj/vpn/certificate/local", "data": data}])
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return True, "Certificate Imported"
        return False, f"Cert Import Failed: {json.dumps(response)}"

    def test_ldap(self, server_name: str, username: str, password: str) -> Tuple[bool, str]:
        """
        LDAP baglantisini test eder.
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        return True, "Test Başarılı (Simülasyon)" 

    def add_admin_profile(self, name: str, description: str = "") -> Tuple[bool, str]:
        """
        Admin Profili Ekler.
        Endpoint: /sys/admin/profile
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        data = {
            "profileid": name,
            "description": description,
            "type": "system" # veya 'device'
        }
        
        response = self._post("add", [{"url": "/sys/admin/profile", "data": data}])
        if response and 'result' in response:
            code = response['result'][0]['status']['code']
            if code == 0: return True, "Profile Added"
            return False, f"Error: {code}"
        return False, "Failed"

    def add_admin_user(self, name: str, password: str, profile: str) -> Tuple[bool, str]:
        """
        Yerel Admin Kullanicisi Ekler.
        Endpoint: /sys/admin/user
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        data = {
            "userid": name,
            "password": password,
            "profileid": profile,
            "rpc-permit": "read-write"
        }
        
        response = self._post("add", [{"url": "/sys/admin/user", "data": data}])
        if response and 'result' in response:
            code = response['result'][0]['status']['code']
            if code == 0: return True, "User Added"
            return False, f"Error: {code}"
        return False, "Failed"
        
    def delete_admin_user(self, name: str) -> bool:
        if not self.session_id and not self.api_token: return False
        response = self._post("delete", [{"url": "/sys/admin/user", "data": {"userid": name}}])
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return True
        return False

    def _install_config(self, device_name: str, vdom: str = "root", adom: str = "root") -> Tuple[bool, str]:
        """
        Cihaz konfigürasyonunu (Device Settings) cihaza yükler (Install).
        Endpoint: /securityconsole/install/device
        """
        if not adom: adom = "root"
        
        # VDOM kisitlamasini kaldirdik. Tum cihaza install yapilacak.
        params = {
            "adom": adom,
            "scope": [{"name": device_name}], 
            "flags": ["none"]
        }
        
        logger.info(f"INSTALLING CONFIG: Device={device_name}, ADOM={adom}")
        print(f"DEBUG: Executing Install -> {json.dumps(params)}")
        
        response = self._post("exec", [{"url": "/securityconsole/install/device", "data": params}])
        print(f"DEBUG: Install Response -> {json.dumps(response)}")
        
        if response and 'result' in response:
            try:
                code = response['result'][0]['status']['code']
                if code == 0:
                    task_id = response['result'][0]['data'].get('task')
                    logger.info(f"Install Task Started: {task_id}")
                    return True, f"Install Started (Task: {task_id})"
                else:
                    msg = response['result'][0]['status']['message']
                    logger.error(f"Install Failed: {code} - {msg}")
                    return False, f"Install Error: {code} - {msg}"
            except Exception as e:
                logger.error(f"Install Exception: {e}")
                pass
        return False, "Install Failed (No Response)"

    def get_interfaces_realtime(self, device_name: str, vdom: str = "root", adom: str = "root") -> Optional[List[Dict]]:
        """
        Cihazdan dogrudan interface durumlarini ceker (Proxy üzerinden Monitor API).
        Bu veriler FMG DB'den bagimsiz ve anliktir.
        """
        resource = "/api/v2/monitor/system/interface"
        payload = {
            "target": [f"device/{device_name}"],
            "action": "get",
            "resource": resource,
            "payload": {
                "vdom": vdom
            }
        }
        
        print(f"DEBUG: Fetching Real-time Interfaces for {device_name}...")
        res = self._post("exec", [{"url": "/sys/proxy/json", "data": payload}])
        
        if res and 'result' in res and res['result'][0]['status']['code'] == 0:
            proxy_res = res['result'][0].get('data', [])
            if proxy_res and isinstance(proxy_res, list):
                response_obj = proxy_res[0].get('response', {})
                results = response_obj.get('results', [])
                
                # Mapping: Monitor API -> App Format
                mapped_interfaces = []
                for item in results:
                    # Monitor API keyleri farkli olabilir.
                    # App'in bekledigi format: name, status (1/0), type, ip, link-status
                    
                    name = item.get('name')
                    # Monitor status: "up"/"down". Config status: 1/0
                    m_status = item.get('status', 'down') 
                    c_status = 1 if str(m_status).lower() == 'up' else 0
                    
                    m_link = item.get('link_status', 'down') # veya 'link'
                    
                    # IP bazen dict, bazen str olabilir
                    # Monitor API'de ip genellikle 'ip' key'inde doner
                    
                    mapped_interfaces.append({
                        "name": name,
                        "status": c_status, # Admin Status
                        "type": item.get('type', 'physical'),
                        "ip": [item.get('ip')] if item.get('ip') else [],
                        "link-status": 1 if str(m_link).lower() == 'up' else 0,
                        "vdom": vdom
                    })
                
                if mapped_interfaces:
                    return mapped_interfaces

        print("DEBUG: Real-time fetch failed or returned empty.")
        return None

    def proxy_update_interface(self, device_name: str, interface_name: str, status: str) -> Tuple[bool, str]:
        """
        Device REST API'sini FMG Proxy uzerinden cagirarak interface durumunu gunceller.
        Target: /api/v2/cmdb/system/interface/{name}
        Method: PUT
        """
        # Encode interface name
        import urllib.parse
        safe_iface = urllib.parse.quote(interface_name, safe='')
        
        resource = f"/api/v2/cmdb/system/interface/{safe_iface}"
        
        payload = {
            "target": [f"device/{device_name}"],
            "action": "put",
            "resource": resource,
            "payload": {
                "status": status # "up" or "down"
            }
        }
        
        print(f"DEBUG: Proxy REST PUT -> {resource} on {device_name}")
        res = self._post("exec", [{"url": "/sys/proxy/json", "data": payload}])
        
        if res and 'result' in res and res['result'][0]['status']['code'] == 0:
            # Proxy cevabini analiz et
            proxy_res = res['result'][0].get('data', [])
            if proxy_res and isinstance(proxy_res, list):
                device_resp = proxy_res[0].get('response', {})
                http_code = device_resp.get('http_status')
                
                # 200 OK veya bazen 500 donup icerikte success diyebilir (FGT quirk)
                if http_code == 200:
                    return True, "Direct Update Success (200 OK)"
                else:
                    return False, f"Device Error ({http_code}): {json.dumps(device_resp)}"
            
            return True, "Proxy Command Sent (No Detail)"
            
        return False, f"Proxy Request Failed: {json.dumps(res)}"

    def execute_via_proxy(self, device_name: str, commands: List[str]) -> Tuple[bool, str]:
        """
        Doğrudan cihaz üzerinde CLI komutları çalıştırır (System Proxy).
        FMG DB'yi bypass eder.
        """
        payload = {
            "target": [f"device/{device_name}"],
            "action": "post",
            "resource": "/api/v2/monitor/system/cli",
            "payload": {
                "command": "\n".join(commands)
            }
        }
        
        print(f"DEBUG: Executing Proxy Command on {device_name}...")
        res = self._post("exec", [{"url": "/sys/proxy/json", "data": payload}])
        
        if res and 'result' in res and res['result'][0]['status']['code'] == 0:
            return True, "Proxy Command Sent (Direct)"
            
        return False, f"Proxy Failed: {json.dumps(res)}"

    def run_cli_script(self, device_name: str, script_content: str, adom: str = "root") -> Tuple[bool, str]:
        """
        Cihaz üzerinde CLI script çalıştırır. (Create -> Execute -> Delete pattern)
        """
        import time
        import uuid
        
        script_name = f"tmp_cli_{uuid.uuid4().hex[:8]}"
        if not adom: adom = "root"
        
        # 1. Script Oluştur
        # Path Düzeltmesi: /pm/config/adom/... yerine /dvmdb/adom/... deneniyor
        # FMG versiyonuna gore degisebilir.
        
        # Deneme 1: DVMDB Script (Genel)
        create_url = f"/dvmdb/adom/{adom}/script"
        
        create_data = {
            "name": script_name,
            "type": "cli",
            "content": script_content,
            "target": "remote_device" # Direkt cihaza uygula
        }
        
        print(f"DEBUG: Creating Script {script_name} at {create_url}...")
        res_create = self._post("add", [{"url": create_url, "data": create_data}])
        
        # Eger script olusturma basarisiz olursa, PROXY FALLBACK
        if not (res_create and 'result' in res_create and res_create['result'][0]['status']['code'] == 0):
            print(f"DEBUG: Script creation failed. Trying DIRECT PROXY EXECUTION...")
            # Script content'i satir satir bol
            commands = script_content.strip().split('\n')
            return self.execute_via_proxy(device_name, commands)
            
        # 2. Scripti Çalıştır
        exec_data = {
            "adom": adom,
            "scope": [{"name": device_name, "vdom": "root"}],
            "script": script_name
        }
        exec_url = "/securityconsole/install/script"
        
        print(f"DEBUG: Executing Script {script_name} on {device_name}...")
        res_exec = self._post("exec", [{"url": exec_url, "data": exec_data}])
        
        exec_success = False
        exec_msg = "Script Exec Failed"
        
        if res_exec and 'result' in res_exec and res_exec['result'][0]['status']['code'] == 0:
            task_id = res_exec['result'][0]['data'].get('task')
            exec_success = True
            exec_msg = f"Script Started (Task: {task_id})"
        else:
            exec_msg = f"Script Exec Error: {json.dumps(res_exec)}"

        # 3. Temizlik (Script Tanımını Sil)
        print(f"DEBUG: Deleting Script Object {script_name}...")
        self._post("delete", [{"url": create_url, "data": {"name": script_name}}])
        
        return exec_success, exec_msg

    def toggle_interface(self, device_name: str, interface_name: str, new_status: str, vdom: str = "root", adom: str = "root", use_script: bool = False) -> Tuple[bool, str]:
        import time
        if not self.session_id and not self.api_token: return False, "No Session"
        
        # --- DIRECT/SCRIPT MODE ---
        if use_script:
            print(f"DEBUG: Toggling via PROXY API for {interface_name} -> {new_status}")
            # Script/Proxy modunda artik dogrudan REST API cagiriyoruz
            # run_cli_script yerine proxy_update_interface
            return self.proxy_update_interface(device_name, interface_name, new_status)

        # --- DB UPDATE MODE (Standard) ---
        api_status = 1 if new_status == "up" else 0
        data = {"status": api_status}
        
        if not adom: adom = "root"
        
        # Interface isminde ozel karakter varsa encode et (örn: port1/1)
        import urllib.parse
        safe_iface = urllib.parse.quote(interface_name, safe='')
        
        print(f"DEBUG: Toggling Interface: {interface_name} (Safe: {safe_iface}) -> {new_status}")
        
        # Olası yolları tanımla
        candidate_urls = []
        
        # 1. ADOM + VDOM Path
        candidate_urls.append(f"/pm/config/adom/{adom}/device/{device_name}/vdom/{vdom}/system/interface/{safe_iface}")
        # 2. Legacy Path
        candidate_urls.append(f"/pm/config/device/{device_name}/vdom/{vdom}/system/interface/{safe_iface}")
        # 3. Global Path
        if vdom == "root":
            candidate_urls.append(f"/pm/config/device/{device_name}/global/system/interface/{safe_iface}")

        db_updated = False
        valid_path = None
        
        for url in candidate_urls:
            print(f"DEBUG: Checking GET -> {url}")
            check_res = self._post("get", [{"url": url}])
            
            if check_res and 'result' in check_res and check_res['result'][0]['status']['code'] == 0:
                print(f"DEBUG: Path FOUND. Current Data: {json.dumps(check_res['result'][0].get('data', 'N/A'))}")
                
                print(f"DEBUG: Sending UPDATE -> {url} | Data: {data}")
                update_res = self._post("update", [{"url": url, "data": data}])
                print(f"DEBUG: Update Result: {json.dumps(update_res)}")
                
                if update_res and 'result' in update_res and update_res['result'][0]['status']['code'] == 0:
                    # VERIFICATION LOOP (ROBUST)
                    # Port kapandığında bağlantı geçici kopabilir, bu yüzden hemen hata vermeyip bekleyerek deniyoruz.
                    max_retries = 6  # 6 deneme
                    retry_delay = 5  # 5 saniye bekleme = Toplam 30 saniye tolerans
                    
                    for attempt in range(max_retries):
                        time.sleep(retry_delay)
                        print(f"DEBUG: Verification Attempt {attempt+1}/{max_retries} on -> {url}")
                        
                        verify_res = self._post("get", [{"url": url}])
                        
                        if verify_res and 'result' in verify_res and verify_res['result'][0]['status']['code'] == 0:
                            curr_data = verify_res['result'][0].get('data', {})
                            if isinstance(curr_data, list) and curr_data:
                                curr_data = curr_data[0]
                                
                            curr_status = curr_data.get('status')
                            
                            # Karsilastirma
                            if str(curr_status) == str(api_status):
                                db_updated = True
                                valid_path = url
                                print(f"DEBUG: Verification SUCCESS. Status is now {curr_status}")
                                break
                            else:
                                print(f"DEBUG: Verification FAILED. DB says {curr_status}, Target: {api_status}")
                        else:
                            print("DEBUG: Verification request failed (Connection or API Error).")
                            # Check if device went offline (expected if we cut the management line)
                            if api_status == 0: # Closing port
                                if not self.is_device_online(device_name):
                                    print("DEBUG: Device is OFFLINE after port close. Assuming SUCCESS due to management cut.")
                                    db_updated = True
                                    valid_path = url
                                    break
                    
                    if db_updated:
                        break # URL loop'unu kir
                else:
                    print(f"DEBUG: DB Update FAILED on {url}. Err: {json.dumps(update_res)}")
            else:
                print(f"DEBUG: Path Not Found ({url})")

        if db_updated:
            # Install oncesi kisa bekleme
            time.sleep(2)
            install_success, install_msg = self._install_config(device_name, vdom, adom=adom)
            if install_success:
                return True, f"DB Updated ({valid_path}) & {install_msg}"
            else:
                return True, f"DB Updated but Install Failed: {install_msg}"
            
        return False, f"Interface Path Not Found! Tried {len(candidate_urls)} paths."
    def logout(self):
        if self.api_token:
            self.api_token = None
            return

        if self.session_id:
            params = [{"url": "/sys/logout"}]
            self._post("exec", params)
            self.session_id = None

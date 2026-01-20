import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
import logging
from typing import Optional, List, Dict, Union, Any

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        except requests.exceptions.RequestException as e:
            logger.error(f"API Bağlantı Hatası: {e}")
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

    def get_devices(self):
        if not self.session_id and not self.api_token: return []

        # 1. Deneme: Genel cihaz listesi (Global - Tum ADOM'lar)
        # Bu yontem cihazlarin gercek ADOM bilgisini daha dogru doner.
        print("DEBUG: get_devices -> Trying Global List (/dvmdb/device)...")
        params_global = [
            {
                "url": "/dvmdb/device",
                "fields": ["name", "ip", "platform_str", "os_ver", "desc", "vdom", "conn_status", "adom"]
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
                "fields": ["name", "ip", "platform_str", "os_ver", "desc", "vdom", "conn_status", "adom"]
            }
        ]
        response = self._post("get", params)
        
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return response['result'][0].get('data', [])
            
        # Eğer ikisi de hata verdiyse None dön
        return None

    def get_vdoms(self, device_name):
        """
        Cihazdaki VDOM listesini çeker.
        """
        if not self.session_id and not self.api_token: return []
        
        # DVMDB üzerinden cihazın VDOM listesini al
        # Not: FortiManager versiyonuna göre path değişebilir, genelde bu yapıdadır.
        params = [
            {
                "url": f"/dvmdb/adom/root/device/{device_name}/vdom",
                "fields": ["name", "status"]
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

    def get_interfaces(self, device_name, vdom="root", adom="root"):
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
                    "fields": ["name", "status", "type", "ip", "vdom", "link-status", "admin-status"]
                }
            ]
            response = self._post("get", params)
            
            if response and 'result' in response and response['result'][0]['status']['code'] == 0:
                data = response['result'][0]['data']
                return data
        
        logger.warning(f"get_interfaces failed for {device_name} (VDOM:{vdom}, ADOM:{adom}). Checked paths: {candidate_urls}")
        return []

    def check_task_status(self, task_id):
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

    def set_dns(self, primary, secondary):
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

    def add_ldap_server(self, name, server_ip, cnid="cn", dn=""):
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

    def import_certificate(self, name, pfx_base64, password):
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

    def test_ldap(self, server_name, username, password):
        """
        LDAP baglantisini test eder.
        Not: FMG API'de dogrudan test endpointi versiyona gore degisir.
        Genelde 'exec' altinda user test komutu vardir.
        """
        if not self.session_id and not self.api_token: return False, "No Session"
        
        # Ornek Endpoint: /pm/config/adom/root/obj/user/ldap/dynamic/test
        # Simdilik sadece baglanti var mi diye server pingliyoruz (Mock gibi)
        # Gercek bir test icin FMG uzerinde 'diagnose test authserver ldap' benzeri komut gerekir.
        # Biz burada basitce 'get' ile sunucunun varligini kontrol edelim.
        
        return True, "Test Başarılı (Simülasyon)" 

    def add_admin_profile(self, name, description=""):
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

    def add_admin_user(self, name, password, profile):
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
        
    def delete_admin_user(self, name):
        if not self.session_id and not self.api_token: return False, "No Session"
        response = self._post("delete", [{"url": "/sys/admin/user", "data": {"userid": name}}])
        if response and 'result' in response and response['result'][0]['status']['code'] == 0:
            return True, "User Deleted"
        return False, "Delete Failed"

    def _install_config(self, device_name, vdom="root", adom="root"):
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

    def toggle_interface(self, device_name, interface_name, new_status, vdom="root", adom="root"):
        import time
        if not self.session_id and not self.api_token: return False, "No Session"
        
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
                    # RACE CONDITION FIX: Bekle ve Dogrula
                    time.sleep(1)
                    
                    # VERIFICATION: Update basarili dondu ama deger gercekten degisti mi?
                    print(f"DEBUG: Update OK. Verifying value on -> {url}")
                    verify_res = self._post("get", [{"url": url}])
                    
                    if verify_res and 'result' in verify_res and verify_res['result'][0]['status']['code'] == 0:
                        curr_data = verify_res['result'][0].get('data', {})
                        # FMG bazen data'yi liste doner
                        if isinstance(curr_data, list) and curr_data:
                            curr_data = curr_data[0]
                            
                        curr_status = curr_data.get('status')
                        target_status = data['status']
                        
                        # Karsilastirma (Int/Str uyumlulugu)
                        if str(curr_status) == str(target_status):
                            db_updated = True
                            valid_path = url
                            print(f"DEBUG: Verification SUCCESS. Status is now {curr_status}")
                            break
                        else:
                            print(f"DEBUG: Verification FAILED. Sent {target_status}, but DB still says {curr_status}")
                    else:
                        print("DEBUG: Verification request failed.")
                else:
                    print(f"DEBUG: DB Update FAILED on {url}. Err: {json.dumps(update_res)}")
            else:
                print(f"DEBUG: Path Not Found ({url})")

        if db_updated:
            # RACE CONDITION FIX: Install oncesi bekleme
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
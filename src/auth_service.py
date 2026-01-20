import streamlit as st
import datetime
import ssl
import logging
import uuid
import socket
import bcrypt
from typing import Optional, List, Dict, Union, Any, Tuple
from ldap3 import Server, Connection, SCHEMA, Tls
from config_service import ConfigService

# Logger Yapilandirmasi
logger = logging.getLogger(__name__)

# Basit In-Memory Session Store (Tek Pod icin yeterli)
# Token -> SessionData
SESSION_STORE = {}
# Username -> [Token1, Token2] (Ters indeks)
USER_SESSIONS = {}

class User:
    def __init__(self, username: str, role: str, user_groups: Optional[List[str]] = None):
        self.username = username
        self.role = role
        self.user_groups = user_groups or [] # LDAP Gruplarini sakla
        self.login_time = datetime.datetime.now()

    def has_access_to_port(self, device_name: str, port_name: str) -> bool:
        """
        Check access dynamically by reloading config.
        """
        # 1. Super User / Admin check (Static)
        if self.username == "admin" or self.role == "Super_User":
            return True
            
        # 2. Load latest config
        cfg = ConfigService.load_config()
        
        # 3. Determine Permission Source
        global_allowed = []
        device_allowed = {}
        
        # A. Local User Check
        local_acc = next((u for u in cfg.get("local_accounts", []) if u['user'] == self.username), None)
        if local_acc:
            global_allowed = local_acc.get("global_allowed_ports", [])
            device_allowed = local_acc.get("device_allowed_ports", local_acc.get("allowed_ports", {}))
        
        # B. LDAP User Check (if not local and has groups)
        elif self.user_groups:
            mappings = cfg.get("ldap_settings", {}).get("mappings", [])
            # Re-evaluate mapping with cached groups but NEW config
            _, g_ports, d_ports = AuthService._get_profile_by_ldap_groups(self.user_groups, mappings)
            global_allowed = g_ports or []
            device_allowed = d_ports or {}
            
        # 4. Global Check
        if port_name in global_allowed:
            return True
            
        # 5. Device Specific Check
        if port_name in device_allowed.get(device_name, []):
            return True
            
        return False

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Şifreyi bcrypt ile hashler."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Şifre doğruluğunu kontrol eder."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            # Geriye dönük uyumluluk: Eğer şifre hashli değilse düz metin kontrolü yap
            return password == hashed

    @staticmethod
    def create_session_token(user_obj: User) -> str:
        """Kullanici icin unique token olusturur ve saklar."""
        token = str(uuid.uuid4())
        SESSION_STORE[token] = {
            "user": user_obj,
            "created_at": datetime.datetime.now()
        }
        
        # Kullaniciya ait tokenlari kaydet
        if user_obj.username not in USER_SESSIONS:
            USER_SESSIONS[user_obj.username] = []
        USER_SESSIONS[user_obj.username].append(token)
        
        return token

    @staticmethod
    def validate_session_token(token: str) -> Optional[User]:
        """Token gecerli mi kontrol eder, gecerliyse user objesini doner."""
        if token in SESSION_STORE:
            return SESSION_STORE[token]["user"]
        return None

    @staticmethod
    def logout_user(username: str):
        """Kullanicinin TUM aktif oturumlarini (tokenlarini) sunucudan siler."""
        if username in USER_SESSIONS:
            tokens = USER_SESSIONS[username]
            for t in tokens:
                if t in SESSION_STORE:
                    del SESSION_STORE[t]
            # Listeyi temizle
            del USER_SESSIONS[username]

    @staticmethod
    def remove_session_token(token: str):
        """Token'i session store'dan siler (Server-side logout)."""
        if token in SESSION_STORE:
            del SESSION_STORE[token]

    @staticmethod
    def _get_profile_by_ldap_groups(user_groups: List[str], mappings: List[Dict]) -> Tuple[Optional[str], Optional[List[str]], Optional[Dict]]:
        """
        Matches user's LDAP groups against configured mappings.
        Returns: (profile_name, global_ports, device_ports) or (None, None, None)
        """
        if not user_groups or not mappings:
            return None, None, None
        
        user_groups_lower = {g.lower().strip() for g in user_groups}
        
        for mapping in mappings:
            map_dn = mapping.get('group_dn', '').lower().strip()
            if not map_dn: continue
            
            match = False
            for grp in user_groups_lower:
                if map_dn == grp or map_dn in grp:
                    match = True
                    break
            
            if match:
                logger.info(f"LDAP Group Match: {map_dn} -> {mapping.get('profile')}")
                g_ports = mapping.get('global_allowed_ports', mapping.get('allowed_ports', []))
                d_ports = mapping.get('device_allowed_ports', {})
                return mapping.get('profile'), g_ports, d_ports
                
        return None, None, None

    @staticmethod
    def login(username, password) -> Tuple[bool, str]:
        cfg = ConfigService.load_config()
        
        # 1. YEREL KULLANICI KONTROLU
        local_accounts = cfg.get("local_accounts", [])
        for acc in local_accounts:
            if acc['user'] == username:
                if AuthService.check_password(password, acc.get('password')):
                    role = acc.get('profile', 'Standard_User')
                    st.session_state['current_user'] = User(username, role)
                    return True, "Başarılı"

        # 2. LDAP CHECK
        ldap_cfg = cfg.get("ldap_settings", {})
        if ldap_cfg.get("enabled"):
            return AuthService._check_ldap_credentials(username, password, ldap_cfg, cfg)
                
        return False, "Kullanıcı bulunamadı veya LDAP kapalı."

    @staticmethod
    def _check_ldap_credentials(username, password, ldap_config, full_config) -> Tuple[bool, str]:
        # Format Username for Bind
        if chr(92) not in username and "@" not in username: # chr(92) is backslash
            bind_user = f"MFA{chr(92)}{username}"
        else:
            bind_user = username
        
        servers_list = ldap_config.get('servers', [])
        if not servers_list: return False, "Sunucu tanımlı değil."

        port = ldap_config.get('port', 636)
        use_ssl = ldap_config.get('use_ssl', True)
        base_dn = ldap_config.get('base_dn', '')
        tls_config = Tls(validate=ssl.CERT_NONE) if use_ssl else None

        for server_host in servers_list:
            if not server_host: continue
            
            server_host = str(server_host).strip()
            for prefix in ["ldaps://", "ldap://", "http://", "https://"]:
                if server_host.startswith(prefix):
                    server_host = server_host.replace(prefix, "")
            
            try:
                # Connection Setup - get_info=SCHEMA is lighter than ALL
                server = Server(server_host, port=port, use_ssl=use_ssl, tls=tls_config, get_info=SCHEMA, connect_timeout=4)
                
                # Determine possible Bind DNs
                possible_dns = [bind_user]
                if chr(92) not in username and "@" not in username and base_dn:
                    domain_parts = [p.split('=')[1] for p in base_dn.lower().split(',') if p.strip().startswith('dc=')]
                    if domain_parts:
                        possible_dns.append(f"{username}@{'.'.join(domain_parts)}")

                # Attempt Bind
                conn = None
                for test_dn in possible_dns:
                    try:
                        c = Connection(server, user=test_dn, password=password, auto_bind=True)
                        if c.bound: 
                            conn = c
                            break
                    except: continue
                
                if conn and conn.bound:
                    logger.info(f"LDAP Bind Successful: {username}")
                    
                    # Fetch User Groups
                    user_groups = []
                    short_user = username.split('\\')[-1].split('@')[0]
                    search_filter = f"( |(sAMAccountName={short_user})(uid={short_user})(cn={short_user}))"
                    
                    conn.search(base_dn, search_filter, attributes=['memberOf'])
                    if len(conn.entries) > 0:
                        entry = conn.entries[0]
                        if 'memberOf' in entry:
                            user_groups = [str(g) for g in entry['memberOf'].values]
                    
                    conn.unbind()
                    
                    # Map Groups to Profile
                    mappings = ldap_config.get("mappings", [])
                    profile_name, _, _ = AuthService._get_profile_by_ldap_groups(user_groups, mappings)
                    
                    if not profile_name:
                        group_list_str = ", ".join([g.split(',')[0].replace('CN=', '') for g in user_groups])
                        return False, f"Yetki grubu bulunamadı. AD Gruplarınız: {group_list_str if group_list_str else 'Yok'}"
                    
                    st.session_state['current_user'] = User(username, profile_name, user_groups=user_groups)
                    return True, "Başarılı"
                    
            except Exception as e:
                logger.error(f"LDAP Connection Error ({server_host}): {e}")
                continue
                
        return False, "LDAP Bağlantı Hatası veya Kimlik Bilgileri Yanlış."

    @staticmethod
    def is_ldap_reachable(server_host: str, port: int, timeout: int = 2) -> bool:
        try:
            server_host = str(server_host).strip()
            for prefix in ["ldaps://", "ldap://"]:
                if server_host.startswith(prefix):
                    server_host = server_host.replace(prefix, "")
            
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_host, int(port)))
            return True
        except:
            return False

    @staticmethod
    def check_ldap_connectivity() -> Tuple[bool, str]:
        """
        Checks LDAP connectivity based on configuration.
        """
        try:
            cfg = ConfigService.load_config()
            ldap_cfg = cfg.get("ldap_settings", {})
            
            if not ldap_cfg.get("enabled"):
                return False, "LDAP Disabled"
                
            servers = ldap_cfg.get("servers", [])
            port = ldap_cfg.get("port", 636)
            
            for server in servers:
                if AuthService.is_ldap_reachable(server, port):
                    return True, f"LDAP Reachable ({server})"
                    
            return False, "LDAP Unreachable"
        except Exception as e:
            return False, f"LDAP Check Error: {e}"

    @staticmethod
    def test_connection(server_host: str, port: int, use_ssl: bool, username: str, password: str) -> Tuple[bool, str]:
        try:
            server_host = str(server_host).strip()
            for prefix in ["ldaps://", "ldap://", "http://", "https://"]:
                if server_host.startswith(prefix):
                    server_host = server_host.replace(prefix, "")
            
            if chr(92) not in username and "@" not in username:
                username = f"MFA{chr(92)}{username}"
                
            tls = Tls(validate=ssl.CERT_NONE) if use_ssl else None
            server = Server(server_host, port=port, use_ssl=use_ssl, tls=tls, get_info=SCHEMA, connect_timeout=5)
            conn = Connection(server, user=username, password=password, auto_bind=True)
            if conn.bound:
                conn.unbind()
                return True, f"Bağlantı Başarılı! ({username})"
            return False, "Bind Başarısız."
        except Exception as e:
            return False, f"Hata ({server_host}): {str(e)}"

    @staticmethod
    def logout():
        if 'current_user' in st.session_state:
            del st.session_state['current_user']
        if 'api' in st.session_state:
            try:
                if st.session_state.api:
                    st.session_state.api.logout()
            except: pass
            st.session_state.api = None
            st.session_state.fmg_connected = False

    @staticmethod
    def get_current_user() -> Optional[User]:
        return st.session_state.get('current_user')

    @staticmethod
    def is_authenticated() -> bool:
        return 'current_user' in st.session_state
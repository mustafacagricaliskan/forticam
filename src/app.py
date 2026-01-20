import streamlit as st
# Force Rebuild
import time
import datetime
import pytz
import pandas as pd
import logging

# Suppress asyncio and tornado network noise
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('tornado.access').setLevel(logging.WARNING)
logging.getLogger('tornado.application').setLevel(logging.WARNING)
logging.getLogger('tornado.general').setLevel(logging.WARNING)

# Servisler ve Bilesenler
from auth_service import AuthService
from log_service import LogService
from config_service import ConfigService
from ui_components import UI
from api_client import FortiManagerAPI
from system_service import SystemService
from settings_view import render_settings

# --- CACHED DATA FUNCTIONS ---
@st.cache_data(ttl=60, show_spinner=False)
def get_cached_devices(_api):
    """Caches device list for 60 seconds."""
    if not _api: return []
    return _api.get_devices() or []

@st.cache_data(ttl=30, show_spinner=False)
def get_cached_vdoms(_api, device_name):
    """Caches VDOM list for 30 seconds."""
    if not _api: return ["root"]
    return _api.get_vdoms(device_name)

@st.cache_data(ttl=1, show_spinner=False)
def get_cached_interfaces(_api, device_name, vdom, adom="root"):
    """Caches interface list for 1 second. Tries Real-time first."""
    if not _api: return []
    
    # 1. Try Real-time (Direct from Device via Proxy)
    try:
        realtime_data = _api.get_interfaces_realtime(device_name, vdom=vdom, adom=adom)
        if realtime_data:
            return realtime_data
    except Exception as e:
        print(f"Realtime Fetch Error: {e}")
        
    # 2. Fallback to FMG DB
    return _api.get_interfaces(device_name, vdom=vdom, adom=adom)

# --- INITIALIZATION ---
UI.init_page()
# UI.set_bg_image moved to authenticated section

# Global State Init
if 'fmg_connected' not in st.session_state: st.session_state.fmg_connected = False
if 'api' not in st.session_state: st.session_state.api = None
if 'devices' not in st.session_state: st.session_state.devices = []
if 'user_timezone' not in st.session_state: st.session_state.user_timezone = "Europe/Istanbul"
if 'vdoms_cache' not in st.session_state: st.session_state.vdoms_cache = {}
if 'optimistic_updates' not in st.session_state: st.session_state.optimistic_updates = {} # {dev_vdom_iface: {status: 1/0, expire: ts}}

if 'health_checks' not in st.session_state:
    st.session_state.health_checks = {
        "fmg": {"status": "pending", "message": "Not Checked"},
        "ldap": {"status": "pending", "message": "Not Checked"}
    }

if 'saved_config' not in st.session_state: 
    st.session_state.saved_config = ConfigService.load_config()
    
    # --- AUTO APPLY DNS ---
    # Eger konfigde DNS varsa, uygulama acilisinda (ilk yuklemede) sisteme uygula
    cfg = st.session_state.saved_config
    p_dns = cfg.get("primary_dns")
    s_dns = cfg.get("secondary_dns")
    if p_dns:
        # Sessizce uygula (Hata olursa loga duser ama UI'i bloklamaz)
        try:
            SystemService.update_dns(p_dns, s_dns)
            print(f"Startup DNS Applied: {p_dns}, {s_dns}")
        except Exception as e:
            print(f"Startup DNS Error: {e}")

# --- PERFORM STARTUP HEALTH CHECKS ---
if st.session_state.health_checks["fmg"]["status"] == "pending":
    cfg = st.session_state.saved_config
    fmg_s = cfg.get("fmg_settings", {})
    ip = fmg_s.get("ip")
    token = fmg_s.get("token")
    
    if ip and token:
        try:
            success, msg = SystemService.check_fmg_connectivity(ip, token)
            st.session_state.health_checks["fmg"] = {"status": "success" if success else "error", "message": msg}
        except:
            st.session_state.health_checks["fmg"] = {"status": "error", "message": "Check Failed"}
    else:
        st.session_state.health_checks["fmg"] = {"status": "warning", "message": "FMG Not Configured"}

if st.session_state.health_checks["ldap"]["status"] == "pending":
    try:
        success, msg = AuthService.check_ldap_connectivity()
        status = "success" if success else ("warning" if "Disabled" in msg else "error")
        st.session_state.health_checks["ldap"] = {"status": status, "message": msg}
    except:
        st.session_state.health_checks["ldap"] = {"status": "error", "message": "Check Failed"}

# --- AUTO CONNECT ---
if not st.session_state.fmg_connected:
    cfg = st.session_state.saved_config
    fmg_s = cfg.get("fmg_settings", {})
    ip = fmg_s.get("ip")
    token = fmg_s.get("token")
    
    if ip and token:
        try:
            # Hizli baslangic icin kisa timeout
            api = FortiManagerAPI(ip, None, None, token, timeout=2)
            if api.login():
                st.session_state.api = api
                st.session_state.fmg_connected = True
                st.session_state.fmg_ip = ip
        except Exception as e:
            print(f"Auto-connect failed: {e}")

# --- CONSTANTS ---
PHYSICAL_TYPES = ['physical', 'hard-switch', 'fsw', 'root', '0', '4']

def filter_interfaces_for_display(interfaces, user, device_name, show_sub_ifaces):
    """
    Interfaces listesini hem yetki hem de gorunum ayarlarin gore filtreler.
    Clean Code: Logic UI'dan ayrildi.
    """
    if not interfaces: return []
    
    # 1. Yetki Filtresi (Strict Whitelist Check)
    # User objesindeki merkezi kontrol metodunu kullan
    if user:
        interfaces = [i for i in interfaces if user.has_access_to_port(device_name, i['name'])]
    
    if not interfaces: return []

    # 2. Gorunum Filtresi (Tip ve Gizlilik)
    filtered_interfaces = []
    for i in interfaces:
        itype = str(i.get('type', 'unknown'))
        iname = str(i.get('name', '')).lower()
        
        # Manager arayuzunde gizli olan 'modem' vb. arayuzleri filtrele
        # Eger 'Sanal ve Alt Arayüzleri Göster' secili DEGILSE
        if not show_sub_ifaces:
            # Modem gibi sistem arayuzlerini isimden yakala ve gizle
            if "modem" in iname or "ssl." in iname:
                continue
                
            if itype in PHYSICAL_TYPES:
                filtered_interfaces.append(i)
        else:
            # Aciksa hepsini goster
            filtered_interfaces.append(i)
            
    return filtered_interfaces

# --- PAGES ---

def render_dashboard():
    st.header("Dashboard")
    
    # Versiyon Bilgisi
    app_version = ConfigService.get_version()
    
    tz = pytz.timezone(st.session_state.user_timezone)
    current_time = datetime.datetime.now(tz).strftime("%H:%M:%S")
    
    c1, c2 = st.columns([1, 1])
    c1.caption(f"🕒 {current_time} ({st.session_state.user_timezone})")
    c2.markdown(f"<div style='text-align:right; color:gray; font-size:0.8em;'>v{app_version}</div>", unsafe_allow_html=True)

    if not st.session_state.fmg_connected:
        # --- RETRY AUTO CONNECT (LAZY LOAD) ---
        # Dashboard acildiginda baglanti yoksa, tekrar config okuyup baglanmayi dene.
        try:
            cfg = ConfigService.load_config()
            fmg_s = cfg.get("fmg_settings", {})
            r_ip = fmg_s.get("ip")
            r_token = fmg_s.get("token")
            
            if r_ip and r_token:
                # Baglanti denemesi (Sessiz modda)
                print(f"DEBUG: Dashboard Retry Connect -> {r_ip}")
                api = FortiManagerAPI(r_ip, None, None, r_token)
                if api.login():
                    st.session_state.api = api
                    st.session_state.fmg_connected = True
                    st.session_state.fmg_ip = r_ip
                    st.session_state.saved_config = cfg
                    st.rerun()
        except Exception as e:
            print(f"Dashboard Retry Connect Error: {e}")

    if not st.session_state.fmg_connected:
        st.warning("⚠️ FortiManager bağlantısı yok. Lütfen 'FMG Bağlantısı' menüsünden bağlanın.")
        
        # DEBUG BILGISI (Sorun tespiti icin)
        with st.expander("🛠️ Bağlantı Sorun Giderme"):
            cfg = ConfigService.load_config()
            fmg_s = cfg.get("fmg_settings", {})
            debug_ip = fmg_s.get("ip")
            debug_token = fmg_s.get("token")
            
            st.write(f"**Yüklü IP:** {debug_ip if debug_ip else 'YOK ❌'}")
            st.write(f"**Yüklü Token:** {'***' + debug_token[-4:] if debug_token and len(debug_token)>4 else 'YOK ❌'}")
            
            if debug_ip and debug_token:
                st.info("Ayarlar mevcut ancak bağlantı kurulamıyor. Lütfen IP erişimini ve Token geçerliliğini kontrol edin.")
                # Manuel Test Butonu
                if st.button("Tekrar Dene (Manuel)"):
                    try:
                        api = FortiManagerAPI(debug_ip, None, None, debug_token)
                        if api.login():
                            st.session_state.api = api
                            st.session_state.fmg_connected = True
                            st.session_state.fmg_ip = debug_ip
                            st.success("Bağlantı Başarılı! Sayfa yenileniyor...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Login Başarısız. API Token yetkilerini kontrol edin.")
                    except Exception as e:
                        st.error(f"Bağlantı Hatası: {e}")
            else:
                st.error("Konfigürasyon dosyasında IP veya Token eksik.")
        return

    api = st.session_state.api
    
    with st.spinner("Cihazlar getiriliyor..."):
        devices_res = get_cached_devices(api)
            
    if not devices_res:
        st.info("Yönetilen cihaz bulunamadı.")
        return

    # --- DEVICE SELECTION GRID ---
    st.markdown("### 🖥️ Yönetilen Cihazlar")
    
    # Search Bar
    search_query = st.text_input("🔍 Cihaz Ara (İsim, IP, Model)", "", placeholder="Örn: Ankara, 10.1.1.1, 60F").lower()
    
    filtered_devices = devices_res
    if search_query:
        filtered_devices = [
            d for d in devices_res 
            if search_query in d['name'].lower() 
            or search_query in d.get('ip', '').lower()
            or search_query in d.get('platform_str', '').lower()
        ]
        
    if not filtered_devices:
        st.warning("Arama kriterlerine uygun cihaz bulunamadı.")
        # Eger cihaz yoksa asagiya devam etmemeli, ancak selected_device varsa belki gosterilebilir.
        # Simdilik return ediyoruz.
        return

    # State management for selected device
    if 'selected_device_name' not in st.session_state:
        st.session_state.selected_device_name = filtered_devices[0]['name'] if filtered_devices else None

    # --- PAGINATION ---
    ITEMS_PER_PAGE = 18
    if 'device_page' not in st.session_state: st.session_state.device_page = 0
    
    total_items = len(filtered_devices)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    # Reset page if filter changes reduces count
    if st.session_state.device_page >= total_pages: st.session_state.device_page = 0
    
    start_idx = st.session_state.device_page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    
    paginated_devices = filtered_devices[start_idx:end_idx]

    # Grid Layout: 3 columns
    cols = st.columns(3)
    for idx, d in enumerate(paginated_devices):
        with cols[idx % 3]:
            name = d['name']
            ip = d.get('ip', '-')
            platform = d.get('platform_str', 'FortiGate')
            version = d.get('os_ver', '-')
            conn_status = str(d.get('conn_status', '0'))
            
            status_color = "green" if conn_status == '1' else "red"
            status_text = "BAĞLI" if conn_status == '1' else "KOPUK"
            
            # Highlight selected device
            is_selected = st.session_state.selected_device_name == name
            
            # Icon selection
            icon = "🔥" # Default
            if "40F" in platform: icon = "⚡"
            elif "60F" in platform: icon = "🚀"
            elif "VM" in platform: icon = "☁️"

            with st.container(border=True):
                # Custom Card Header with Icon
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <span style="font-size: 1.5rem;">{icon}</span>
                        <h4 style="margin: 0; padding: 0;">{name}</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"📍 {ip}")
                st.write(f"**Model:** {platform} (v{version})")
                
                # Inline Status
                st.markdown(f":{status_color}[● {status_text}]")
                
                if st.button("Seç", key=f"sel_dev_{name}", use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state.selected_device_name = name
                    st.rerun()

    # Pagination Controls
    if total_pages > 1:
        c_prev, c_info, c_next = st.columns([1, 4, 1])
        if c_prev.button("⬅️ Önceki", disabled=(st.session_state.device_page == 0)):
            st.session_state.device_page -= 1
            st.rerun()
            
        c_info.markdown(f"<div style='text-align:center; padding-top:10px; color:gray;'>Sayfa {st.session_state.device_page + 1} / {total_pages} (Toplam: {total_items})</div>", unsafe_allow_html=True)
        
        if c_next.button("Sonraki ➡️", disabled=(st.session_state.device_page >= total_pages - 1)):
            st.session_state.device_page += 1
            st.rerun()

    # Get active device object
    target_device = next((d for d in devices_res if d['name'] == st.session_state.selected_device_name), None)
    if not target_device: target_device = devices_res[0] # Fallback
    sel_dev = target_device['name']
    
    # Cihaz baglanti ve ADOM durumunu kontrol et
    is_dev_connected = str(target_device.get('conn_status', '0')) == '1'
    target_adom = target_device.get('adom', 'root')

    st.divider()
    
    # VDOM ve Arayüzler
    vdoms = ["root"]
    if sel_dev:
        vdoms = get_cached_vdoms(api, sel_dev)
    
    col_vdom, col_spacer = st.columns([1, 2])
    with col_vdom:
        sel_vdom = st.selectbox("📂 Aktif VDOM", vdoms)

    # Kullanici Yetki Seviyesini Al
    user = AuthService.get_current_user()
    cfg = ConfigService.load_config()
    target_profile = next((p for p in cfg.get("admin_profiles", []) if p['name'] == user.role), None)
    
    # Dashboard yetki seviyesi (Default 0)
    dash_perm = 2 if user.username == "admin" else (target_profile.get("permissions", {}).get("Dashboard", 0) if target_profile else 0)

    # Baglanti uyarisi
    if not is_dev_connected:
        st.error(f"❌ **{sel_dev}** cihazı şu anda FortiManager'a bağlı değil (Disconnected). Port işlemleri yapılamaz.")

    st.subheader(f"🔌 Port Yönetimi: {sel_dev} [{sel_vdom}]")
    
    # Filtreleme Secenegi
    show_sub_ifaces = st.sidebar.checkbox("Sanal ve Alt Arayüzleri Göster (VLAN vb.)", value=False)
    
    raw_interfaces = get_cached_interfaces(api, sel_dev, sel_vdom, target_adom)
    
    # Clean Code: Logic helper fonksiyonuna tasindi
    filtered_interfaces = filter_interfaces_for_display(raw_interfaces, user, sel_dev, show_sub_ifaces)

    if not filtered_interfaces:
        if not raw_interfaces:
            st.warning("Cihazdan port bilgisi alınamadı.")
        else:
            st.warning("Görüntülenecek port bulunamadı (Yetkiniz olmayabilir veya filtre kriterlerine uymuyor).")
        
    for iface in filtered_interfaces:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5], gap="medium")
                
                # Column 1: Name and Type
                itype = iface.get('type', 'physical')
                c1.markdown(f"**{iface['name']}**")
                c1.caption(f"🏷️ {str(itype).capitalize()}")
                
                # Column 2: IP Address
                ip_val = iface.get('ip', '0.0.0.0 0.0.0.0')
                if isinstance(ip_val, list) and ip_val: ip_val = ip_val[0]
                c2.write("🌐 IP Adresi")
                c2.code(ip_val, language="bash")
                
                # Column 3: Status Badges (OPTIMISTIC UI LOGIC)
                
                # 1. API'den gelen gercek durum
                admin_stat = iface.get('status')
                if admin_stat is None: admin_stat = iface.get('admin-status')
                raw_stat = str(admin_stat if admin_stat is not None else 'down').lower()
                is_up = raw_stat in ['1', 'up', 'enable', 'true']
                
                # 2. Optimistic Override (Gecici Gorsel Guncelleme)
                opt_key = f"{sel_dev}_{sel_vdom}_{iface['name']}"
                opt_data = st.session_state.get('optimistic_updates', {}).get(opt_key)
                
                is_optimistic = False
                if opt_data and time.time() < opt_data['expire']:
                    # Eger optimistic durum API ile ayniysa artik override etmeye gerek yok
                    # (API yetismis demektir). Ancak garanti olsun diye sure bitene kadar tutabiliriz.
                    # Bizim senaryoda API geciktigi icin override ediyoruz.
                    target_state = (opt_data['status'] == 1)
                    if is_up != target_state:
                        is_up = target_state
                        is_optimistic = True
                
                admin_cls = "status-up" if is_up else "status-down"
                admin_lbl = "AÇIK" if is_up else "KAPALI"
                
                # Link Status
                link_stat = iface.get('link-status')
                link_html = ""
                if link_stat is not None:
                    is_link_up = str(link_stat).lower() in ['1', 'up', 'true']
                    # Link status override edilmez, fiziksel durumdur.
                    link_cls = "status-up" if is_link_up else "status-down"
                    link_lbl = "LINK: UP" if is_link_up else "LINK: DOWN"
                    link_html = f'<div class="status-badge {link_cls}" style="margin-top:5px;">{link_lbl}</div>'
                
                c3.markdown(f"""
                    <div class="status-badge {admin_cls}">{admin_lbl}</div>
                    {link_html}
                """, unsafe_allow_html=True)
                
                # Column 4: Action Button
                btn_lbl, btn_type, target = ("Kapat", "secondary", "down") if is_up else ("Aç", "primary", "up")
                can_edit = (dash_perm == 2) and is_dev_connected
                btn_key = f"{sel_dev}_{sel_vdom}_{iface['name']}"
                
                if c4.button(btn_lbl, key=btn_key, type=btn_type, use_container_width=True, disabled=not can_edit):
                    with st.spinner("İşleniyor..."):
                        # Global ayarı oku (db_update veya direct_proxy)
                        g_cfg = st.session_state.saved_config
                        global_method = g_cfg.get("toggle_method", "db_update")
                        use_script_method = (global_method == "direct_proxy")
                        
                        success, msg = api.toggle_interface(sel_dev, iface['name'], target, vdom=sel_vdom, adom=target_adom, use_script=use_script_method)
                        
                        user_name = AuthService.get_current_user().username
                        LogService.log_action(user_name, f"Port {target.upper()}", f"{sel_dev}[{sel_vdom}]", msg)
                        
                        # Cache temizle (Initial)
                        get_cached_interfaces.clear()
                        
                        if success:
                            # OPTIMISTIC UPDATE SET
                            st.session_state.optimistic_updates[opt_key] = {
                                "status": 1 if target == "up" else 0,
                                "expire": time.time() + 20 # 20 saniye boyunca bu durumu goster
                            }
                            
                            if "Task:" in msg:
                                # Task ID'yi al ve dogrulama bilgilerini gonder
                                tid = msg.split("Task:")[1].strip().replace(")", "")
                                track_task(api, tid, device_name=sel_dev, vdom=sel_vdom, interface_name=iface['name'], target_status=target, adom=target_adom)
                            elif use_script_method and ("Direct Update Success" in msg or "Proxy" in msg):
                                # Proxy/Direct modu icin ozel mesaj
                                st.success("⚡ Doğrudan komut cihaz üzerine başarıyla gönderildi.")
                                
                                # AGGRESSIVE CACHE CLEAR
                                get_cached_interfaces.clear()
                                # st.cache_data.clear() # Tum app cache'ini silmek performansi etkiler ama gerekirse acilabilir
                                
                                time.sleep(1) # Hissedilir bir islem suresi birak, sonra hemen yenile
                                st.rerun()
                            else:
                                st.toast("Başarılı", icon="✅")
                                get_cached_interfaces.clear()
                                time.sleep(1); st.rerun()
                        else:
                            st.error(f"İşlem Başarısız! \nDetay: {msg}")
                

def track_task(api, task_id, device_name=None, vdom=None, interface_name=None, target_status=None, adom="root"):
    p_bar = st.progress(0, "Başlatılıyor...")
    status_text = st.empty()
    
    while True:
        status = api.check_task_status(task_id)
        if not status: 
            status_text.error("Task durumu alınamadı.")
            break
            
        pct = int(status.get("percent", 0))
        state = str(status.get("state", "processing")).lower()
        
        p_bar.progress(pct, f"İlerleme: %{pct} ({state.upper()})")
        
        if pct >= 100 or state in ["done", "completed", "failed", "error"]:
            # Task loglarini detayli al
            lines = status.get("line", [])
            log_content = []
            if isinstance(lines, list):
                for l in lines:
                    if isinstance(l, dict):
                        log_content.append(l.get("detail", str(l)))
                    else:
                        log_content.append(str(l))
            
            log_text = "\n".join(log_content) if log_content else "Detay bulunamadı."
            
            if state in ["failed", "error"]: 
                status_text.error(f"❌ Task Başarısız! \n{log_text}")
                time.sleep(5)
            else: 
                status_text.success("✅ İşlem Kuyruğu Tamamlandı. Durum doğrulanıyor...")
                
                # --- FINAL VERIFICATION ---
                if device_name and interface_name:
                    time.sleep(3) # FMG sync icin bekleme
                    try:
                        fresh_ifaces = []
                        # 1. Realtime Dene
                        rt_data = api.get_interfaces_realtime(device_name, vdom=vdom, adom=adom)
                        if isinstance(rt_data, list):
                            fresh_ifaces = rt_data
                        
                        # 2. DB Dene (Eger Realtime bos veya hataliysa)
                        if not fresh_ifaces:
                            db_data = api.get_interfaces(device_name, vdom=vdom, adom=adom)
                            if isinstance(db_data, list):
                                fresh_ifaces = db_data
                        
                        target_iface = None
                        for i in fresh_ifaces:
                            if isinstance(i, dict) and i.get('name') == interface_name:
                                target_iface = i
                                break
                        
                        if target_iface:
                            admin_stat = target_iface.get('status')
                            if admin_stat is None: admin_stat = target_iface.get('admin-status')
                            is_now_up = str(admin_stat).lower() in ['1', 'up', 'enable', 'true']
                            
                            current_label = "UP" if is_now_up else "DOWN"
                            
                            if (target_status == "up" and is_now_up) or (target_status == "down" and not is_now_up):
                                status_text.success(f"🎯 DOĞRULAMA BAŞARILI: Port şu an fiziksel olarak **{current_label}** durumunda.")
                            else:
                                status_text.warning(f"⚠️ DOĞRULAMA: İşlem bitti ancak port henüz **{current_label}** görünüyor (Gecikme olabilir).")
                        else:
                            # Sessiz gec
                            pass
                    except Exception as e:
                        # Logla ama UI'da hata gosterme
                        print(f"Verification Logic Error: {e}")
                
                with st.expander("İşlem Detayları (Log)", expanded=True):
                    st.code(log_text)
                
            break
        time.sleep(2)
    
    if st.button("Listeyi Güncelle & Kapat", type="primary"):
        st.rerun()

def render_fmg_connection():
    st.header("🔗 FortiManager Bağlantısı")
    
    user = AuthService.get_current_user()
    cfg = ConfigService.load_config()
    target_profile = next((p for p in cfg.get("admin_profiles", []) if p['name'] == user.role), None)
    fmg_perm = 2 if user.username == "admin" else (target_profile.get("permissions", {}).get("FMG_Conn", 0) if target_profile else 0)
    can_edit = (fmg_perm == 2)
    
    if st.session_state.fmg_connected:
        st.success(f"✅ Bağlı: **{st.session_state.fmg_ip}**")
        if st.button("Bağlantıyı Kes", type="secondary", disabled=not can_edit):
            if st.session_state.api: st.session_state.api.logout()
            st.session_state.fmg_connected = False
            st.session_state.api = None
            st.session_state.devices = []
            st.rerun()
    else:
        st.info("FortiManager'a bağlanmak için API Token girin.")
        with st.form("fmg_conn"):
            # Safe access to nested settings
            fmg_s = cfg.get("fmg_settings", {})
            ip = st.text_input("IP Adresi", value=fmg_s.get("ip", ""), disabled=not can_edit)
            token = st.text_input("API Token", type="password", value=fmg_s.get("token", ""), disabled=not can_edit)
            
            if st.form_submit_button("Bağlan", type="primary", disabled=not can_edit):
                api = FortiManagerAPI(ip, None, None, token)
                if api.login():
                    st.session_state.api, st.session_state.fmg_connected, st.session_state.fmg_ip = api, True, ip
                    
                    # Update config structure
                    if "fmg_settings" not in cfg: cfg["fmg_settings"] = {}
                    cfg["fmg_settings"]["ip"] = ip
                    cfg["fmg_settings"]["token"] = token
                    
                    ConfigService.save_config(cfg)
                    st.rerun()
                else:
                    st.error("Bağlantı başarısız.")

def render_logs():
    st.header("Audit Logs")
    # Anti-cache: Her renderda taze veri oku
    if st.button("🔄 Logları Yenile"):
        st.rerun()
        
    df = LogService.get_logs()
    if not df.empty:
        df = df.sort_values(by="Timestamp", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Logları İndir (CSV)", df.to_csv(index=False).encode('utf-8'), 'audit_logs.csv', 'text/csv')
    else: st.info("Kayıt yok.")

def render_guide():
    st.header("📚 Kullanım Kılavuzu")
    st.markdown(r"""
    ### 1. Dashboard
    **İşlev:** Yönetilen cihazların ve portların durumunu anlık olarak izleyebilir, port açma/kapama işlemleri yapabilirsiniz.
    *   **Firewall & VDOM Seçimi:** İşlem yapmak istediğiniz cihazı ve sanal alanı (VDOM) seçin.
    *   **Port Listesi:** Yetkiniz dahilindeki portlar listelenir.
    *   **Durum Göstergeleri:** 
        *   :green[● ADMIN: UP] -> Port yönetici tarafından açık.
        *   :red[● ADMIN: DOWN] -> Port yönetici tarafından kapalı.
        *   Link Durumu (Parantez içinde): Fiziksel kablo bağlantısını gösterir.
    *   **Aç/Kapa Butonları:** Port durumunu değiştirmek için kullanılır. (Sadece yazma yetkisi olanlar görebilir).

    ### 2. FMG Bağlantısı
    **İşlev:** FortiManager sunucusu ile bağlantı kurmanızı sağlar.
    *   **IP Adresi:** FortiManager IP adresi.
    *   **API Token:** Erişim için gerekli yetkili anahtar.
    *   Bağlantı kurulduğunda cihaz listesi otomatik çekilir.

    ### 3. Ayarlar
    **İşlev:** Sistem ve kullanıcı yapılandırması. (Sadece Admin yetkisi ile görünür).
    *   **Kullanıcılar:** Yeni kullanıcı ekleyebilir, şifre sesirlayabilir ve yetki profili atayabilirsiniz.
    *   **Port Yetkilendirme:** 
        *   **Global Yetkiler:** Kullanıcının tüm cihazlarda görebileceği ortak portlar.
        *   **Cihaz Bazlı Yetkiler:** Belirli bir cihaz için özel port izinleri.
    *   **E-posta Bildirimleri:** İşlem yapıldığında otomatik e-posta gönderimi ayarları.
    *   **LDAP:** Active Directory entegrasyon ayarları.

    ### 4. Audit Logs
    **İşlev:** Sistemde yapılan tüm kritik işlemlerin (Port açma/kapama, ayar değişimi vb.) kayıtlarını tutar.
    *   Tarih, Kullanıcı, İşlem Tipi ve Cihaz bilgisi içerir.
    *   Logları CSV formatında indirebilirsiniz.
    """)

def main():
    if not AuthService.is_authenticated(): UI.login_screen()
    else:
        UI.set_bg_image("MFA Background/Background_B.jpg")
        page = UI.sidebar_menu()
        if page == "Dashboard": render_dashboard()
        elif page == "FMG Bağlantısı": render_fmg_connection()
        elif page == "Ayarlar": render_settings()
        elif page == "Audit Logs": render_logs()
        elif page == "Kullanım Kılavuzu": render_guide()

if __name__ == "__main__": main()
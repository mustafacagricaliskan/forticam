import streamlit as st
import pandas as pd
import json
import time
import base64
from config_service import ConfigService
from auth_service import AuthService
from system_service import SystemService

def render_permission_manager(data_obj, unique_key):
    """
    Ortak izin yonetim arayuzu (Hem Local hem LDAP icin).
    data_obj: Duzenlenen sozluk (Local user dict veya LDAP mapping dict)
    unique_key: UI elementleri icin unique key suffix
    """
    st.markdown("### 🛠️ Port İzinleri Yönetimi")
    
    # --- STANDARDIZATION & MIGRATION ---
    # Global Ports: 'global_allowed_ports' (Eski: 'allowed_ports' for LDAP)
    if "global_allowed_ports" not in data_obj:
        data_obj["global_allowed_ports"] = data_obj.pop("allowed_ports", []) if isinstance(data_obj.get("allowed_ports"), list) else []
    
    # Device Ports: 'device_allowed_ports' (Eski: 'allowed_ports' for Local)
    if "device_allowed_ports" not in data_obj:
        # Local userlarda 'allowed_ports' dict idi
        old_device_ports = data_obj.pop("allowed_ports", {}) if isinstance(data_obj.get("allowed_ports"), dict) else {}
        data_obj["device_allowed_ports"] = old_device_ports

    # -- MEVCUT YETKILER --
    with st.expander("Mevcut Yetkileri Görüntüle / Düzenle", expanded=True):
        # A. Global
        global_ports = data_obj.get("global_allowed_ports", [])
        st.markdown("**🌍 Global İzinler (Tüm Cihazlar)**")
        if global_ports:
            c1, c2 = st.columns([4, 1])
            c1.info(", ".join(global_ports))
            if c2.button("Temizle", key=f"clr_glob_{unique_key}"):
                data_obj["global_allowed_ports"] = []
                ConfigService.save_config(st.session_state.saved_config)
                st.rerun()
        else:
            st.caption("Tanımlı global izin yok.")
        
        st.markdown("---")
        
        # B. Cihaz Bazlı
        st.markdown("**🔌 Cihaz Bazlı İzinler**")
        current_perms = data_obj.get("device_allowed_ports", {})
        if current_perms:
            for dev_name, ports in list(current_perms.items()):
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.text(f"{dev_name}: {', '.join(ports)}")
                    if c2.button("Sil", key=f"del_perm_{unique_key}_{dev_name}"):
                        del current_perms[dev_name]
                        data_obj["device_allowed_ports"] = current_perms
                        ConfigService.save_config(st.session_state.saved_config)
                        st.rerun()
        else:
            st.caption("Tanımlı cihaz bazlı izin yok.")

    st.divider()
    st.markdown("#### ➕ Yeni Yetki Ekle")
    
    if st.session_state.get("fmg_connected"):
        api = st.session_state.api
        if not st.session_state.get("devices"):
            st.session_state.devices = api.get_devices()
        
        if st.session_state.get("devices"):
            dev_opts = [d['name'] for d in st.session_state.devices]
            s_dev = st.selectbox("Kaynak Cihaz (Port Listesi İçin)", dev_opts, key=f"perm_dev_{unique_key}")
            
            if s_dev:
                if s_dev not in st.session_state.get("vdoms_cache", {}):
                    vdoms = api.get_vdoms(s_dev)
                else:
                    vdoms = st.session_state.vdoms_cache[s_dev]
                    
                s_vdom = st.selectbox("VDOM", vdoms, key=f"perm_vdom_{unique_key}")
                
                if s_vdom:
                    try:
                        # Portlari al ve filtrele
                        raw_ifaces = api.get_interfaces(s_dev, vdom=s_vdom)
                        filtered_names = [i['name'] for i in raw_ifaces if "modem" not in i['name'].lower() and "ssl." not in i['name'].lower()]
                                
                        s_ports = st.multiselect("İzin Verilecek Portları Seçin", filtered_names, key=f"perm_ports_{unique_key}")
                        
                        is_global = st.checkbox("🌍 Bu port iznini TÜM CİHAZLAR için (Global) uygula", key=f"perm_glob_{unique_key}", help="İşaretlenirse, seçilen port isimleri sistemdeki tüm cihazlarda yetkili kılınır.")
                        
                        if st.button("Yetkiyi Ekle", key=f"save_perm_btn_{unique_key}", type="primary"):
                            if not s_ports:
                                st.warning("Lütfen en az bir port seçin.")
                            else:
                                if is_global:
                                    # Global Merge
                                    current = data_obj.get("global_allowed_ports", [])
                                    updated = list(set(current + s_ports))
                                    data_obj["global_allowed_ports"] = updated
                                    msg = "Global yetkiler güncellendi!"
                                else:
                                    # Device Merge
                                    if "device_allowed_ports" not in data_obj: data_obj["device_allowed_ports"] = {}
                                    current_dev_ports = data_obj["device_allowed_ports"].get(s_dev, [])
                                    updated_dev_ports = list(set(current_dev_ports + s_ports))
                                    data_obj["device_allowed_ports"][s_dev] = updated_dev_ports
                                    msg = f"{s_dev} için yetki eklendi!"
                                
                                ConfigService.save_config(st.session_state.saved_config)
                                st.success(msg)
                                time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
    else:
        st.warning("⚠️ Port listesi için FortiManager bağlantısı gereklidir.")


def render_settings():
    st.header("⚙️ Sistem Yapılandırması")
    
    # --- HEALTH CHECK SECTION ---
    with st.container(border=True):
        st.markdown("### 🏥 Uygulama Bağlantı Durumu")
        h_fmg, h_ldap = st.columns(2)
        
        # FMG Status
        f_health = st.session_state.get("health_checks", {}).get("fmg", {"status": "pending", "message": "N/A"})
        f_col = "green" if f_health["status"] == "success" else "red" if f_health["status"] == "error" else "orange"
        h_fmg.markdown(f"**FortiManager:** :{f_col}[{f_health['status'].upper()}]")
        h_fmg.caption(f_health["message"])
        
        # LDAP Status
        l_health = st.session_state.get("health_checks", {}).get("ldap", {"status": "pending", "message": "N/A"})
        l_col = "green" if l_health["status"] == "success" else "red" if l_health["status"] == "error" else "orange"
        h_ldap.markdown(f"**LDAP Server:** :{l_col}[{l_health['status'].upper()}]")
        h_ldap.caption(l_health["message"])
        
        if st.button("🔄 Durumu Yenile", use_container_width=True):
            with st.spinner("Kontrol ediliyor..."):
                st.session_state.health_checks = {
                    "fmg": {"status": "pending", "message": "Refreshing..."},
                    "ldap": {"status": "pending", "message": "Refreshing..."}
                }
                st.rerun()

    user = AuthService.get_current_user()
    cfg = st.session_state.saved_config
    profiles = cfg.get("admin_profiles", [])
    target_profile = next((p for p in profiles if p['name'] == user.role), None)
    
    # Yetki Seviyeleri (System modülü için)
    sys_perm = 2 if user.username == "admin" else (target_profile.get("permissions", {}).get("System", 0) if target_profile else 0)
    can_edit = (sys_perm == 2)

    # --- USER EDIT DIALOG ---
    @st.dialog("Kullanıcı Düzenle", width="large")
    def show_user_edit(username):
        accounts_ref = cfg.get("local_accounts", [])
        acc = next((x for x in accounts_ref if x['user'] == username), None)
        if not acc: st.error("Kullanıcı bulunamadı"); return
        
        st.caption(f"Düzenlenen: **{username}**")
        
        avail_profs = [p['name'] for p in cfg.get("admin_profiles", [])]
        cur_idx = avail_profs.index(acc['profile']) if acc['profile'] in avail_profs else 0
        new_prof = st.selectbox("Yetki Profili", avail_profs, index=cur_idx)
        acc['profile'] = new_prof
        
        # SIFRE DEGISTIRME ALANI
        st.divider()
        st.markdown("**🔐 Şifre Değiştir**")
        p_col1, p_col2 = st.columns(2)
        new_pass_1 = p_col1.text_input("Yeni Şifre", type="password", key=f"p1_{username}", placeholder="Boş bırakılırsa değişmez")
        new_pass_2 = p_col2.text_input("Şifre Tekrar", type="password", key=f"p2_{username}", placeholder="Aynı şifreyi tekrar girin")
        
        pass_update_ready = False
        if new_pass_1 or new_pass_2:
            if new_pass_1 == new_pass_2:
                if new_pass_1:
                    acc['password'] = new_pass_1
                    st.success("✅ Şifre güncellenecek.")
                    pass_update_ready = True
            else:
                st.error("❌ Şifreler eşleşmiyor!")
                pass_update_ready = False
        
        st.divider()
        # Refactored Permission Manager
        render_permission_manager(acc, f"user_{username}")

        st.divider()
        # Kaydet butonunu eger sifreler uyusmuyorsa disable etme veya uyari verme mantigi
        # Eger kullanici sifre alanlarina bisey yazdiysa ama eslesmediyse, kaydetme islemi eski sifreyle devam eder ama biz uyaralim.
        can_save = True
        if (new_pass_1 or new_pass_2) and not pass_update_ready:
            can_save = False
            st.warning("⚠️ Şifreler eşleşmediği için kaydedilemez. Lütfen düzeltin.")

        if st.button("Kaydet ve Kapat", use_container_width=True, disabled=not can_save):
            ConfigService.save_config(cfg)
            st.success("Kullanıcı güncellendi.")
            time.sleep(0.5)
            st.rerun()

    # --- MAPPING EDIT DIALOG ---
    @st.dialog("Grup Yetkilerini Düzenle", width="large")
    def show_mapping_edit(idx):
        if "temp_mappings" not in st.session_state or idx >= len(st.session_state.temp_mappings):
            st.error("Eşleşme bulunamadı"); return
            
        m = st.session_state.temp_mappings[idx]
        st.caption(f"Grup DN: **{m.get('group_dn')}**")
        
        avail_profs = [p['name'] for p in cfg.get("admin_profiles", [])]
        cur_idx = avail_profs.index(m['profile']) if m['profile'] in avail_profs else 0
        new_prof = st.selectbox("Yetki Profili", avail_profs, index=cur_idx, key=f"m_edit_prof_{idx}")
        m['profile'] = new_prof
        
        st.divider()
        # Refactored Permission Manager
        render_permission_manager(m, f"map_{idx}")

        st.divider()
        if st.button("Kapat", use_container_width=True, key=f"m_close_{idx}"):
            # Sync back to main config
            cfg.get("ldap_settings", {})["mappings"] = st.session_state.temp_mappings
            ConfigService.save_config(cfg)
            st.rerun()

    tab_auth, tab_sys, tab_siem = st.tabs([
        "🔐 Kimlik Doğrulama & Yetkilendirme", 
        "🛠️ Sistem Servisleri (DNS/SSL)",
        "🛡️ SIEM Ayarları"
    ])
    
    # --- TAB 1: AUTH & RBAC ---
    with tab_auth:
        col_ldap, col_profiles = st.columns([1.2, 1], gap="large")
        
        with col_ldap:
            ldap_cfg = cfg.get("ldap_settings", {})
            enabled = ldap_cfg.get("enabled", False)
            
            # --- DURUM KONTROLU ---
            current_status = "DISABLED"
            if enabled:
                servers = ldap_cfg.get("servers", [])
                if servers and servers[0]:
                    is_ok = AuthService.is_ldap_reachable(servers[0], ldap_cfg.get("port", 636))
                    current_status = "ONLINE" if is_ok else "OFFLINE"
                else:
                    current_status = "NO_SERVER"
            
            status_color = "green" if current_status == "ONLINE" else "red" if current_status in ["OFFLINE", "ERROR"] else "grey"
            st.markdown(f"### 📂 LDAP / Active Directory :{status_color}[● {current_status}]")
            
            new_enabled = st.toggle("LDAP Girişini Aktif Et", value=enabled, disabled=not can_edit)
            if new_enabled != enabled:
                ldap_cfg["enabled"] = new_enabled
                cfg["ldap_settings"] = ldap_cfg
                ConfigService.save_config(cfg); st.rerun()
            
            with st.container(border=True):
                st.markdown("**1. Sunucu Kümesi (Cluster)**")
                if "temp_servers" not in st.session_state: st.session_state.temp_servers = ldap_cfg.get("servers", [])
                
                for i, srv in enumerate(st.session_state.temp_servers):
                    c_in, c_bt = st.columns([6, 1])
                    st.session_state.temp_servers[i] = c_in.text_input(f"LDAP Sunucu {i+1}", value=srv, label_visibility="collapsed", key=f"srv_u_{i}", disabled=not can_edit)
                    if c_bt.button("🗑️", key=f"del_srv_u_{i}", disabled=not can_edit): 
                        st.session_state.temp_servers.pop(i)
                        st.rerun()
                
                if st.button("➕ Sunucu Ekle", disabled=not can_edit): 
                    st.session_state.temp_servers.append("")
                    st.rerun()
                
                st.divider()
                st.markdown("**2. Bağlantı Parametreleri**")
                c_ssl, c_pi = st.columns([2, 1])
                use_ssl = c_ssl.toggle("SSL Kullan", value=ldap_cfg.get("use_ssl", True), disabled=not can_edit)
                port = 636 if use_ssl else 389
                c_pi.info(f"Port: {port}")
                base_dn = st.text_input("Base DN", value=ldap_cfg.get("base_dn", ""), disabled=not can_edit)
                
                if st.button("💾 LDAP Ayarlarını Kaydet", type="primary", use_container_width=True, disabled=not can_edit):
                    final_servers = [s.strip() for s in st.session_state.temp_servers if s.strip()]
                    # RELOAD-MODIFY-SAVE Pattern
                    disk_cfg = ConfigService.load_config()
                    disk_cfg.get("ldap_settings", {}).update({
                        "enabled": new_enabled, 
                        "servers": final_servers, 
                        "port": port, 
                        "use_ssl": use_ssl, 
                        "base_dn": base_dn
                    })
                    ConfigService.save_config(disk_cfg)
                    st.session_state.saved_config = disk_cfg
                    st.success("Kaydedildi."); time.sleep(0.5); st.rerun()

            st.markdown("##### 🔗 Grup & Rol Eşleştirmeleri")
            with st.container(border=True):
                mappings = ldap_cfg.get("mappings", [])
                if "temp_mappings" not in st.session_state: st.session_state.temp_mappings = mappings.copy()
                
                if not st.session_state.temp_mappings: st.info("Eşleşme yok.")
                
                for i, m in enumerate(st.session_state.temp_mappings):
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                        st.session_state.temp_mappings[i]["group_dn"] = c1.text_input("DN", value=m.get("group_dn", ""), key=f"m_dn_{i}", label_visibility="collapsed", disabled=not can_edit, placeholder="Group DN")
                        
                        avail_profs = [p['name'] for p in cfg.get("admin_profiles", [])]
                        st.session_state.temp_mappings[i]["profile"] = c2.selectbox("Prof", options=avail_profs, index=avail_profs.index(m.get("profile")) if m.get("profile") in avail_profs else 0, key=f"m_pr_{i}", label_visibility="collapsed", disabled=not can_edit)
                        
                        if c3.button("⚙️", key=f"m_edit_btn_{i}", disabled=not can_edit, help="Grup Yetkilerini Düzenle"):
                            show_mapping_edit(i)
                        
                        if c4.button("🗑️", key=f"m_del_{i}", disabled=not can_edit):
                            st.session_state.temp_mappings.pop(i)
                            st.rerun()
                
                c_a1, c_a2 = st.columns(2)
                if c_a1.button("➕ Ekle", disabled=not can_edit): 
                    st.session_state.temp_mappings.append({"group_dn": "", "profile": "Standard_User", "global_allowed_ports": [], "device_allowed_ports": {}})
                    st.rerun()
                if c_a2.button("💾 Mappings Kaydet", disabled=not can_edit):
                    disk_cfg = ConfigService.load_config()
                    if "ldap_settings" not in disk_cfg:
                        disk_cfg["ldap_settings"] = {}
                    disk_cfg["ldap_settings"]["mappings"] = st.session_state.temp_mappings
                    
                    ConfigService.save_config(disk_cfg)
                    st.session_state.saved_config = disk_cfg
                    st.success("Kaydedildi."); time.sleep(0.5); st.rerun()

            with st.expander("🧪 Bağlantı Testi", expanded=True):
                st.caption("Girilen ayarlarla bir kullanıcının LDAP bağlantısını doğrulayın.")
                tu, tp = st.columns(2)
                t_u = tu.text_input("Test Kullanıcı", placeholder="kullaniciadi", key="test_u_final")
                t_p = tp.text_input("Şifre  ", type="password", key="test_p_final")
                
                if st.button("Şimdi Test Et", use_container_width=True, type="secondary"):
                    # Mevcut state'deki sunucuyu al
                    if "temp_servers" in st.session_state and st.session_state.temp_servers:
                        srv = st.session_state.temp_servers[0].strip()
                        if srv:
                            with st.spinner(f"Sorgulanıyor: {srv}..."):
                                s, m = AuthService.test_connection(srv, port, use_ssl, t_u, t_p)
                                if s: st.success(m)
                                else: st.error(m)
                        else:
                            st.error("Sunucu adresi boş olamaz.")
                    else:
                        st.warning("Lütfen önce bir sunucu adresi girin.")

        with col_profiles:
            st.subheader("🛡️ Admin Profiles")
            modules = ["Dashboard", "FMG_Conn", "System", "Audit Logs"] 
            mod_map = {"Dashboard": "Dashboard", "FMG_Conn": "FMG_Conn", "System": "System", "Audit Logs": "Logs"}
            levels = {0: "None", 1: "Read", 2: "Write"}
            level_rev = {"None": 0, "Read": 1, "Write": 2}

            @st.dialog("Edit Profile")
            def show_edit_profile_dialog(edit_name):
                p_obj = next((x for x in profiles if x['name'] == edit_name), None)
                if edit_name == "NEW_PROFILE": p_obj = {"name": "", "permissions": {m: 1 for m in mod_map.values()}}
                is_super = (edit_name == "Super_User")
                if is_super: st.warning("Super_User değiştirilemez.")
                new_n = st.text_input("Profil Adı", value=p_obj['name'], disabled=is_super)
                u_perms = {}
                for display_mod in modules:
                    st.markdown(f"**{display_mod}**")
                    curr_val = p_obj.get("permissions", {}).get(mod_map[display_mod], 0)
                    sel_val = st.segmented_control(label=display_mod, options=["None", "Read", "Write"], default=levels[curr_val], key=f"seg_dlg_{edit_name}_{display_mod}", label_visibility="collapsed", disabled=is_super)
                    u_perms[mod_map[display_mod]] = level_rev.get(sel_val, 0)
                if st.button("Save", type="primary", disabled=is_super):
                    disk_cfg = ConfigService.load_config()
                    if edit_name == "NEW_PROFILE": 
                        disk_cfg["admin_profiles"].append({"name": new_n, "permissions": u_perms})
                    else:
                        for prf in disk_cfg["admin_profiles"]:
                            if prf['name'] == edit_name: prf['permissions'] = u_perms; prf['name'] = new_n
                    ConfigService.save_config(disk_cfg)
                    st.session_state.saved_config = disk_cfg
                    st.rerun()

            with st.container(border=True):
                for p in profiles:
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{p['name']}**")
                    perms = p.get("permissions", {})
                    c2.caption(f"D:{perms.get('Dashboard',0)} S:{perms.get('System',0)} L:{perms.get('Logs',0)}")
                    if c3.button("📝", key=f"edit_p_{p['name']}", disabled=not can_edit): show_edit_profile_dialog(p['name'])
                if st.button("➕ Add Profile", disabled=not can_edit, use_container_width=True): show_edit_profile_dialog("NEW_PROFILE")

            st.subheader("👤 Local Accounts")
            with st.container(border=True):
                accounts = cfg.get("local_accounts", [])
                for acc in accounts:
                    c1, c2, c3, c4 = st.columns([2, 2, 0.5, 0.5])
                    c1.write(f"**{acc['user']}**")
                    c2.caption(acc['profile'])
                    
                    if c3.button("⚙️", key=f"u_edit_{acc['user']}", disabled=not can_edit, help="Yetkileri Düzenle"):
                        show_user_edit(acc['user'])
                        
                    if c4.button("🗑️", key=f"u_del_{acc['user']}", disabled=not can_edit):
                        disk_cfg = ConfigService.load_config()
                        disk_cfg["local_accounts"] = [x for x in disk_cfg.get("local_accounts", []) if x['user'] != acc['user']]
                        ConfigService.save_config(disk_cfg)
                        st.session_state.saved_config = disk_cfg
                        st.rerun()
                with st.expander("➕ Add User"):
                    un = st.text_input("Kullanıcı")
                    up = st.text_input("Şifre ", type="password")
                    upr = st.selectbox("Profil ", [p['name'] for p in cfg.get("admin_profiles", [])])
                    if st.button("Kullanıcıyı Kaydet"):
                        disk_cfg = ConfigService.load_config()
                        disk_cfg.get("local_accounts", []).append({"user": un, "profile": upr, "password": up})
                        ConfigService.save_config(disk_cfg)
                        st.session_state.saved_config = disk_cfg
                        st.rerun()

    # --- TAB 2: SYSTEM ---
    with tab_sys:
        c_dns, c_cert = st.columns(2, gap="large")
        with c_dns:
            with st.container(border=True):
                # Configden test hedefini al (Yoksa varsayilan mfa.gov.tr)
                test_host = cfg.get("connectivity_check_host", "mfa.gov.tr")
                
                # Belirlenen hosta gore kontrol et
                dns_ok = SystemService.check_dns_status(test_host)
                d_col, d_stat = ("green", "ONLINE") if dns_ok else ("red", "OFFLINE")
                
                st.markdown(f"### 🌐 DNS & Bağlantı :{d_col}[● {d_stat}]")
                st.caption(f"Test Hedefi: {test_host}")
                
                dns1 = st.text_input("DNS 1", value=cfg.get("primary_dns", "8.8.8.8"), disabled=not can_edit)
                dns2 = st.text_input("DNS 2", value=cfg.get("secondary_dns", "1.1.1.1"), disabled=not can_edit)
                
                st.markdown("---")
                st.markdown("### 🔌 Port Kontrol Yöntemi")
                toggle_opts = {
                    "db_update": "Standart (DB Update + Install)",
                    "direct_proxy": "Hızlı (Direct Proxy REST API)"
                }
                current_method = cfg.get("toggle_method", "db_update")
                # Find index
                method_keys = list(toggle_opts.keys())
                try:
                    def_idx = method_keys.index(current_method)
                except:
                    def_idx = 0
                    
                new_method = st.radio(
                    "Varsayılan Yöntem",
                    options=method_keys,
                    format_func=lambda x: toggle_opts[x],
                    index=def_idx,
                    help="Standart yöntem FMG veritabanını günceller. Hızlı yöntem doğrudan cihaza komut gönderir (Özellikle lan2 gibi bağlantı koparan portlar için önerilir).",
                    disabled=not can_edit
                )

                st.markdown("---")
                new_test_host = st.text_input("Bağlantı Testi Hedefi (FQDN)", value=test_host, help="Air-gap (Kapalı Devre) ağlarda 'Offline' hatası almamak için buraya iç ağınızdaki erişilebilir bir sunucu adresi (örn: internal.domain.local) girin.", disabled=not can_edit)
                
                if st.button("Uygula", disabled=not can_edit, type="primary"):
                    disk_cfg = ConfigService.load_config()
                    disk_cfg.update({
                        "primary_dns": dns1, 
                        "secondary_dns": dns2,
                        "connectivity_check_host": new_test_host,
                        "toggle_method": new_method
                    })
                    ConfigService.save_config(disk_cfg)
                    st.session_state.saved_config = disk_cfg
                    
                    # DNS guncelleme (OpenShift'te calismayabilir ama config kaydedilir)
                    s, m = SystemService.update_dns(dns1, dns2)
                    
                    if s: 
                        st.success(m)
                    elif "Permission denied" in str(m):
                        # Konteyner ortaminda beklenen durum
                        st.info(f"✅ Ayarlar veritabanına kaydedildi.\n\nℹ️ Not: Konteyner kısıtlamaları nedeniyle işletim sistemi DNS ayarları (/etc/resolv.conf) uygulama içinden değiştirilemedi. Bu normaldir. DNS ayarlarını Docker/OpenShift konfigürasyonundan (YAML) yapmanız gerekebilir.")
                    else: 
                        st.warning(f"Ayarlar kaydedildi ancak DNS dosyası güncellenemedi: {m}")
                    
                    time.sleep(3); st.rerun()
        with c_cert:
            with st.container(border=True):
                st.markdown("### 📜 SSL Sertifikası")
                upl = st.file_uploader("Dosya", type=["pfx"], disabled=not can_edit)
                pws = st.text_input("Şifre  ", type="password", disabled=not can_edit)
                if st.button("Sertifikayı Yükle", disabled=not can_edit):
                    if upl:
                        b64 = base64.b64encode(upl.getvalue()).decode('utf-8')
                        s, m = SystemService.apply_pfx_certificate(b64, pws)
                        st.success(m) if s else st.error(m)

    # --- TAB 4: SIEM ---
    with tab_siem:
        siem_cfg = cfg.get("siem_settings", {})
        enabled = siem_cfg.get("enabled", False)
        
        # Check Status
        status_color = "grey"
        status_text = "DISABLED"
        
        if enabled:
            from log_service import LogService
            s_host = siem_cfg.get("server")
            s_port = siem_cfg.get("port", 514)
            s_proto = siem_cfg.get("protocol", "UDP")
            
            is_ok, msg = LogService.check_siem_connection(s_host, s_port, s_proto)
            if is_ok:
                status_color = "green"
                status_text = "ONLINE" if s_proto == "TCP" else "READY (UDP)"
            else:
                status_color = "red"
                status_text = "OFFLINE"
        
        st.header(f"🛡️ SIEM / Syslog Ayarları :{status_color}[● {status_text}]")
        if enabled and status_color == "red":
            st.caption(f"⚠️ Hata Detayı: {msg if 'msg' in locals() else 'Bilinmiyor'}")
        else:
            st.caption("Uygulama audit loglarının gerçek zamanlı olarak bir SIEM ürününe (Syslog üzerinden) gönderilmesi.")
        
        is_siem_enabled = st.toggle("SIEM Gönderimini Aktif Et", value=enabled, disabled=not can_edit)
        
        with st.container(border=True):
            c_host, c_port, c_proto = st.columns([3, 1, 1])
            
            siem_host = c_host.text_input("Syslog Sunucu IP/Host", value=siem_cfg.get("server", ""), placeholder="192.168.1.100", disabled=not can_edit)
            siem_port = c_port.number_input("Port", value=siem_cfg.get("port", 514), step=1, disabled=not can_edit)
            siem_proto = c_proto.selectbox("Protokol", options=["UDP", "TCP"], index=0 if siem_cfg.get("protocol") == "UDP" else 1, disabled=not can_edit)
            
        if st.button("💾 SIEM Ayarlarını Kaydet", type="primary", disabled=not can_edit):
            disk_cfg = ConfigService.load_config()
            disk_cfg["siem_settings"] = {
                "enabled": is_siem_enabled,
                "server": siem_host,
                "port": int(siem_port),
                "protocol": siem_proto
            }
            ConfigService.save_config(disk_cfg)
            st.session_state.saved_config = disk_cfg
            st.success("SIEM ayarları kaydedildi!")
            time.sleep(1)
            st.rerun()
            
        col_test, col_export = st.columns(2)
        
        if col_test.button("🧪 Test Logu Gönder", disabled=not can_edit, use_container_width=True):
            if not siem_host:
                st.error("Lütfen önce sunucu adresini girin.")
            else:
                from log_service import LogService
                with st.spinner("SIEM'e test logu gönderiliyor..."):
                    LogService.log_action(user.username, "SIEM_TEST", "SYSTEM", "SIEM Bağlantı Test Mesajı")
                    st.toast("Test logu gönderildi. Lütfen SIEM tarafını kontrol edin.", icon="🛡️")

        if col_export.button("📤 Geçmiş Logları Aktar (CSV -> SIEM)", disabled=not can_edit, use_container_width=True, help="Sistemde kayıtlı olan tüm geçmiş logları (CSV) yapılandırılmış SIEM sunucusuna toplu olarak gönderir."):
            from log_service import LogService
            if not siem_cfg.get("enabled"):
                st.warning("Lütfen önce SIEM gönderimini aktif edip ayarları kaydedin.")
            else:
                with st.spinner("Geçmiş loglar aktarılıyor..."):
                    success, msg = LogService.export_past_logs_to_siem()
                    if success: st.success(msg)
                    else: st.error(msg)
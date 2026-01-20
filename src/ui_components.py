import streamlit as st
import os
import base64
import time
import datetime
import extra_streamlit_components as stx
from auth_service import AuthService

# Singleton Cookie Manager
# st.cache_resource KALDIRILDI: Widget iceren fonksiyonlar cache'lenmemeli.
def get_cookie_manager():
    return stx.CookieManager(key="cookie_manager")

@st.cache_data(show_spinner=False)
def get_base64_image(image_path):
    """Görüntüyü base64 olarak önbelleğe alıp döndürür."""
    if not image_path: return None
    
    # Normalize path safely using chr(92) for backslash to avoid SyntaxError
    backslash = chr(92)
    if backslash in image_path:
        image_path = image_path.replace(backslash, os.sep)
    # Replace forward slash with os.sep
    if "/" in image_path:
        image_path = image_path.replace("/", os.sep)
    
    if not os.path.exists(image_path):
        # Farklı çalışma dizinleri için bir üst dizini kontrol et
        parent_path = os.path.join("..", image_path)
        if os.path.exists(parent_path):
            image_path = parent_path
        else:
            return None

    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

class UI:
    """UI bilesenlerini ve sayfa duzenini yonetir."""

    @staticmethod
    def set_bg_image(image_path):
        """Arka plan resmini ayarlar."""
        bin_str = get_base64_image(image_path)
        if not bin_str:
            return

        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        
        # Safe string formatting
        page_bg_img = """
        <style>
            /* Air-gap optimization: Removed external font import */
            
            html, body, [class*="css"] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #171717;
            }

            .stApp {
                background-image: url("data:image/%s;base64,%s") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }
            
            /* Glassmorphism Container for Main App */
            .block-container {
                background-color: rgba(255, 255, 255, 0.82);
                padding: 2.5rem;
                border-radius: 24px;
                margin-top: 2rem;
                box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.18);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.45);
                max-width: 98% !important;
            }
            
            /* Enhanced Device Card Component */
            .device-card {
                background: rgba(255, 255, 255, 0.6);
                border-radius: 16px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.5);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
                margin-bottom: 1rem;
            }
            .device-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
                background: rgba(255, 255, 255, 0.8);
                border-color: #5D5FEF;
            }
            
            /* Status Badge Base */
            .status-badge {
                padding: 4px 12px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 0.85rem;
                display: inline-block;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .status-up {
                background-color: rgba(34, 197, 94, 0.15);
                color: #15803d;
                border: 1px solid rgba(34, 197, 94, 0.3);
                box-shadow: 0 0 15px rgba(34, 197, 94, 0.1);
            }
            .status-down {
                background-color: rgba(239, 68, 68, 0.15);
                color: #b91c1c;
                border: 1px solid rgba(239, 68, 68, 0.3);
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
            }
            
            /* Inputs */
            .stTextInput > div > div > input, .stSelectbox > div > div > div {
                border-radius: 8px !important;
                border: 1px solid #e2e8f0 !important;
                padding: 0.5rem 1rem !important;
            }
            .stTextInput > div > div > input:focus {
                border-color: #5D5FEF !important;
                box-shadow: 0 0 0 3px rgba(93, 95, 239, 0.1) !important;
            }
        </style>
        """
        
        # Inject dynamic values using f-string or replacement to avoid % formatting conflicts with CSS
        page_bg_img = page_bg_img.replace("data:image/%s;base64,%s", f"data:image/{ext};base64,{bin_str}")
        
        st.markdown(page_bg_img, unsafe_allow_html=True)

    @staticmethod
    def init_page():
        st.set_page_config(
            page_title="FortiCam - FMG Interface Controller",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        # Global Styles
        st.markdown("""
        <style>
            /* Hide Streamlit Default Elements (Footer & MainMenu) */
            #MainMenu { visibility: hidden; }
            footer { visibility: hidden; }
            
            /* HEADER DUZELTMESI */
            header { 
                visibility: visible !important; 
                background: transparent !important;
            }
            
            .stAppDeployButton, [data-testid="stHeaderActionElements"] {
                display: none !important;
            }

            [data-testid="stSidebar"] { 
                background-color: #f8fafc; 
                border-right: 1px solid #e2e8f0;
            }

            /* Global Glass Card */
            div[data-testid="stExpander"] {
                background: rgba(255, 255, 255, 0.4);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.5);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            }

            /* Button Styles */
            .stButton > button {
                border-radius: 10px;
                font-weight: 600;
                border: none;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                padding: 0.6rem 1.2rem;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.2);
            }
            
            /* Primary Button Glow */
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
                box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.3);
            }
            
            /* Secondary/Kapat Button */
            .stButton > button[kind="secondary"] {
                background: #f1f5f9;
                color: #475569;
            }
            .stButton > button[kind="secondary"]:hover {
                background: #e2e8f0;
                color: #1e293b;
            }
            
            /* Sidebar Navigation */
            section[data-testid="stSidebar"] .stRadio > label {
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 5px;
                transition: background-color 0.2s;
                cursor: pointer;
            }
            section[data-testid="stSidebar"] .stRadio > label:hover {
                background-color: #f1f5f9;
            }
            
            /* FIX: Sidebar Toggle Button (Hamburger Menu) Visibility */
            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
                visibility: visible !important;
                z-index: 1000000 !important;
                color: #334155 !important;
                background-color: transparent !important;
            }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def login_screen():
        """Modern Card Login Screen (Exact replica of login_page.png)."""
        
        cookie_manager = get_cookie_manager()
        
        # --- AUTO LOGIN CHECK ---
        # Cookie'den token oku
        auth_token = cookie_manager.get(cookie="forticam_auth_token")
        if auth_token:
            user = AuthService.validate_session_token(auth_token)
            if user:
                st.session_state['current_user'] = user
                st.rerun()
        
        logo_path = "MFA Logo/yeni_Bakanlık Logo.png"
        logo_data = get_base64_image(logo_path)
        
        # Background handling
        bg_path = "MFA Background/Background_B.jpg"
        bg_data = get_base64_image(bg_path)
        
        bg_css = ""
        if bg_data:
            bg_css = f"""
                background-image: url("data:image/jpeg;base64,{bg_data}") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            """
        else:
            bg_css = "background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;"

        # Logo handling
        logo_html = ""
        if logo_data:
            logo_html = f'<img src="data:image/png;base64,{logo_data}" style="height: 80px; width: auto; display: block; margin: 0 auto 20px auto;">'
        else:
            # Fallback icon if logo missing
            logo_html = '<div style="text-align: center; margin-bottom: 20px;"><svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="#007bff" stroke="none"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg></div>'

        # --- LOGIN SPECIFIC CSS ---
        # Note: Using .format() or f-string with double braces for CSS is tricky.
        # Ideally split css or use simple string concat.
        
        login_style = """
            <style>
                /* 1. HIDE SIDEBAR & DEFAULT ELEMENTS */
                [data-testid="stSidebar"], 
                [data-testid="collapsedControl"],
                #MainMenu, 
                footer, 
                header {
                    display: none !important; 
                }

                /* 2. PAGE BACKGROUND */
                .stApp {
                    %s
                }

                /* 3. CARD CONTAINER */
                .block-container {
                    background-color: rgba(255, 255, 255, 0.85);
                    width: 90%% !important; 
                    max-width: 450px !important;
                    padding: 40px !important; 
                    padding-bottom: 60px !important; 
                    margin-top: 8vh !important;
                    margin-left: auto !important;
                    margin-right: auto !important;
                    border-radius: 24px;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.6);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    box-sizing: border-box !important; 
                    overflow: hidden !important; 
                }
                
                /* Remove default padding */
                .element-container {
                    margin-bottom: 1rem;
                }

                /* 4. FORM BODY PADDING */
                [data-testid="stForm"] {
                    padding: 0 !important;
                    border: none !important;
                }

                /* 5. INPUTS */
                div[data-baseweb="input"], div[data-baseweb="base-input-container"] {
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    height: auto !important;
                    min-height: 54px !important;
                    overflow: visible !important;
                }

                .stTextInput > div > div > input {
                    background-color: rgba(255, 255, 255, 0.95) !important;
                    border: 1px solid #cbd5e1 !important;
                    color: #1e293b !important;
                    border-radius: 12px !important;
                    padding-left: 45px !important;
                    height: 50px !important;
                    line-height: normal !important;
                    font-size: 15px !important;
                    transition: all 0.2s ease-in-out;
                    box-shadow: inset 0 1px 2px rgba(0,0,0,0.05) !important;
                    width: 100% !important;
                }
                
                /* Ensure full width for password visibility container */
                .stTextInput > div {
                    width: 100% !important;
                }

                .stTextInput > div > div > input:focus {
                    border-color: #4f46e5 !important;
                    background-color: #ffffff !important;
                    box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1) !important;
                    outline: none !important;
                }

                /* Label Styling */
                .stTextInput label {
                    display: block !important;
                    color: #475569 !important;
                    font-size: 0.75rem !important;
                    font-weight: 700 !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                    margin-bottom: 0.5rem !important;
                    margin-left: 4px !important;
                }

                /* Input Icons - Updated to match Turkish labels */
                input[aria-label="Kullanıcı Adı"] {
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512' fill='%2364748b'%3E%3Cpath d='M224 256c70.7 0 128-57.3 128-128S294.7 0 224 0 96 57.3 96 128s57.3 128 128 128zm89.6 32h-16.7c-22.2 10.2-46.9 16-72.9 16s-50.6-5.8-72.9-16h-16.7C60.2 288 0 348.2 0 422.4V464c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48v-41.6c0-74.2-60.2-134.4-134.4-134.4z'/%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: 15px center;
                    background-size: 16px;
                }
                input[aria-label="Şifre"] {
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512' fill='%2364748b'%3E%3Cpath d='M400 224h-24v-72C376 68.2 307.8 0 224 0S72 68.2 72 152v72H48c-26.5 0-48 21.5-48 48v192c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V272c0-26.5-21.5-48-48-48zm-104 0H152v-72c0-39.7 32.3-72 72-72s72 32.3 72 72v72z'/%3E%3C/svg%3E"); 
                    background-repeat: no-repeat;
                    background-position: 15px center;
                    background-size: 14px;
                }

                /* Hide Streamlit form instructions */
                [data-testid="InputInstructions"] {
                    display: none !important;
                }

                /* Hide Password Visibility Toggle */
                [data-testid="stTextInputPasswordVisibility"] {
                    display: none !important;
                }

                .stButton > button {
                    width: 100%% !important;
                    background: linear-gradient(135deg, #4f46e5 0%%, #3b82f6 100%%) !important;
                    color: white !important;
                    border-radius: 12px !important;
                    height: 54px !important;
                    font-weight: 700 !important;
                    font-size: 1rem !important;
                    border: none !important;
                    margin-top: 20px !important;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
                    transition: all 0.3s ease;
                }
                .stButton > button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4) !important;
                    filter: brightness(1.1);
                }
                
                .stAlert {
                    background-color: rgba(254, 226, 226, 0.9) !important;
                    border: 1px solid #fecaca !important;
                    color: #991b1b !important;
                    border-radius: 8px !important;
                }

                [data-testid="InputInstructions"] { display: none !important; }

            </style>
        """
        
        # Inject background CSS safely without % formatting conflicts
        login_style = login_style.replace("%s", bg_css)
        
        st.markdown(login_style, unsafe_allow_html=True)

        # CARD CONTENT
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                {logo_html}
                <h1 style="font-size: 1.8rem; font-weight: 800; color: #1e293b; margin: 0; padding: 0;">FortiCam</h1>
                <p style="font-size: 1rem; color: #64748b; margin-top: 8px;">Güvenli Yönetim Paneli</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", border=False):
            # Using specific labels to match CSS
            username = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adınızı girin")
            password = st.text_input("Şifre", type="password", placeholder="Şifrenizi girin")
            submitted = st.form_submit_button("Giriş Yap")

            if submitted:
                if not username or not password:
                    st.warning("Lütfen kullanıcı adı ve şifrenizi giriniz.")
                else:
                    success, msg = AuthService.login(username, password)
                    if success:
                        # Session Token Olustur ve Cookie'ye yaz
                        user = AuthService.get_current_user()
                        token = AuthService.create_session_token(user)
                        cookie_manager.set("forticam_auth_token", token, expires_at=datetime.datetime.now() + datetime.timedelta(days=1))
                        
                        st.toast("Giriş Başarılı!", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)
        
        # FOOTER SECTION
        st.markdown("""
        <div style="margin-top: 40px; text-align: center; padding-bottom: 20px;">
            <p style="font-size: 0.75rem; color: #64748b; margin: 0;">T.C. Dışişleri Bakanlığı</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def sidebar_menu():
        """Rol ve Yetki tabanli sol menu."""
        user = AuthService.get_current_user()
        if not user: return None

        # Load Config for Permissions
        from config_service import ConfigService
        cfg = st.session_state.saved_config # App.py tarafindan yuklenmis olmali
        profiles = cfg.get("admin_profiles", [])

        user_rights = {}
        if user.username == "admin":
            user_rights = {"Dashboard": 2, "FMG_Conn": 2, "Auth": 2, "System": 2, "Logs": 2}
        else:
            target_profile = next((p for p in profiles if p['name'] == user.role), None)
            if target_profile:
                user_rights = target_profile.get("permissions", {})
            else:
                user_rights = {"Dashboard": 0, "FMG_Conn": 0, "Auth": 0, "System": 0, "Logs": 0}

        with st.sidebar:
            # Force Sidebar Visibility (Login ekranindan kalan gizlemeyi ezmek icin)
            st.markdown(
                """
                <style>
                    [data-testid="stSidebar"], [data-testid="collapsedControl"] { 
                        display: block !important; 
                        visibility: visible !important;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            logo_path = "MFA Logo/yeni_Bakanlık Logo.png"
            logo_data = get_base64_image(logo_path)
            if logo_data:
                 st.markdown(f'<img src="data:image/png;base64,{logo_data}" style="width: 140px; margin-bottom: 20px;">', unsafe_allow_html=True)

            st.title("🛡️ FortiCam")
            st.caption(f"👤 {user.username} ({user.role})")

            options = []
            # Fallback: Eger user_rights bos gelirse (profil bulunamazsa), varsayilan olarak Dashboard goster.
            if user_rights.get("Dashboard", 0) >= 1 or not user_rights: 
                options.append("Dashboard")
            
            if user_rights.get("FMG_Conn", 0) >= 1: options.append("FMG Bağlantısı")
            if user_rights.get("System", 0) >= 1 or user_rights.get("Auth", 0) >= 1: options.append("Ayarlar")
            if user_rights.get("Logs", 0) >= 1: options.append("Audit Logs")

            options.append("Kullanım Kılavuzu")

            if not options:
                st.warning("Erişim yetkiniz bulunmuyor.")
                if st.button("Çıkış Yap"):
                    AuthService.logout(); st.rerun()
                return None

            selection = st.radio("Menü", options, label_visibility="collapsed")
            
            st.divider()
            if st.button("Güvenli Çıkış"):
                # 1. Server-side logout (Kullanici adina bagli tum tokenlari sil)
                if user and user.username:
                    AuthService.logout_user(user.username)
                
                # 2. Browser cookie'sini silmeye calis (Hata verirse onemli degil, token zaten sunucuda silindi)
                try:
                    cm = get_cookie_manager()
                    cm.delete("forticam_auth_token")
                except:
                    pass
                
                AuthService.logout(); st.rerun()

            return selection
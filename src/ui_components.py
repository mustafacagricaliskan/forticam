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
    
    # Normalize path
    image_path = image_path.replace("\", os.sep).replace("/", os.sep)
    
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
        
        # Using f-string for interpolation of python variables. 
        # Double braces {{ }} are used to escape CSS braces.
        page_bg_img = f"""
        <style>
            /* Air-gap optimization: Removed external font import */
            
            html, body, [class*="css"] {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #171717;
            }}

            .stApp {{
                background-image: url("data:image/{ext};base64,{bin_str}") !important;
                background-size: cover !important;
                background-position: center center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            
            /* Glassmorphism Container for Main App */
            .block-container {{
                background-color: rgba(255, 255, 255, 0.85);
                padding: 2.5rem;
                border-radius: 20px;
                margin-top: 3rem;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.4);
                max-width: 95% !important;
            }}
            
            /* Inputs */
            .stTextInput > div > div > input, .stSelectbox > div > div > div {{
                border-radius: 8px !important;
                border: 1px solid #e2e8f0 !important;
                padding: 0.5rem 1rem !important;
            }}
            .stTextInput > div > div > input:focus {{
                border-color: #5D5FEF !important;
                box-shadow: 0 0 0 3px rgba(93, 95, 239, 0.1) !important;
            }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)

    @staticmethod
    def init_page():
        st.set_page_config(
            page_title="FortiManager Controller",
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
            
            /* HEADER DUZELTMESI: Header'i tamamen gizleme, seffaf yap. Yoksa sidebar butonu da gider. */
            header { 
                visibility: visible !important; 
                background: transparent !important;
            }
            
            /* Sadece Deploy butonu ve sag ustteki secenekleri gizle */
            .stAppDeployButton, [data-testid="stHeaderActionElements"] {
                display: none !important;
            }

            [data-testid="stSidebar"] { 
                background-color: #fcfcfc; 
                border-right: 1px solid #f1f5f9;
            }

            /* Button Styles */
            .stButton > button {
                border-radius: 8px;
                font-weight: 600;
                border: none;
                transition: all 0.2s ease-in-out;
                padding: 0.6rem 1rem;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.15);
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
        st.markdown(f"""
            <style>
                /* 1. HIDE SIDEBAR & DEFAULT ELEMENTS */
                [data-testid="stSidebar"], 
                [data-testid="collapsedControl"],
                #MainMenu, 
                footer, 
                header {{ 
                    display: none !important; 
                }}

                /* 2. PAGE BACKGROUND */
                .stApp {{
                    {bg_css}
                }}

                /* 3. CARD CONTAINER (Styling .block-container in 'centered' layout) */
                .block-container {{
                    background-color: rgba(255, 255, 255, 0.85);
                    width: 90% !important; /* Responsive width */
                    max-width: 450px !important;
                    padding: 40px !important; /* Balanced padding */
                    padding-bottom: 60px !important; /* Extra bottom space */
                    margin-top: 8vh !important;
                    margin-left: auto !important;
                    margin-right: auto !important;
                    border-radius: 24px;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.6);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    box-sizing: border-box !important; /* Prevent width calculation errors */
                    overflow: hidden !important; /* Clip any side overflow */
                }}
                
                /* Remove default padding */
                .element-container {{
                    margin-bottom: 1rem;
                }}

                /* 4. FORM BODY PADDING */
                [data-testid="stForm"] {{
                    padding: 0 !important;
                    border: none !important;
                }}

                /* 5. INPUTS */
                
                /* Remove Streamlit's default container styling to prevent double borders */
                /* Ensure container grows with input and doesn't clip */
                div[data-baseweb="input"], div[data-baseweb="base-input-container"] {{
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    height: auto !important;
                    min-height: 54px !important;
                    overflow: visible !important;
                }}

                .stTextInput > div > div > input {{
                    background-color: rgba(255, 255, 255, 0.95) !important;
                    border: 2px solid #cbd5e1 !important;
                    color: #1e293b !important;
                    border-radius: 26px !important;
                    padding-left: 50px !important; /* Space for icon */
                    height: 54px !important;
                    line-height: normal !important;
                    font-size: 16px !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: none !important;
                    box-sizing: border-box !important; /* Ensure borders are included in height/width */
                    width: 100% !important; /* Strict width constraint */
                    max-width: 100% !important;
                }}
                
                .stTextInput > div > div > input:focus {{
                    border-color: #cbd5e1 !important;
                    background-color: #ffffff !important;
                    box-shadow: none !important;
                    outline: none !important;
                }}

                /* Input Icons using aria-label selector */
                /* Username */
                input[aria-label="USERNAME"] {{
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512' fill='%2364748b'%3E%3Cpath d='M224 256c70.7 0 128-57.3 128-128S294.7 0 224 0 96 57.3 96 128s57.3 128 128 128zm89.6 32h-16.7c-22.2 10.2-46.9 16-72.9 16s-50.6-5.8-72.9-16h-16.7C60.2 288 0 348.2 0 422.4V464c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48v-41.6c0-74.2-60.2-134.4-134.4-134.4z'/%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: 18px center;
                    background-size: 18px;
                }}
                /* Password */
                input[aria-label="PASSWORD"] {{
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 448 512' fill='%2364748b'%3E%3Cpath d='M400 224h-24v-72C376 68.2 307.8 0 224 0S72 68.2 72 152v72H48c-26.5 0-48 21.5-48 48v192c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V272c0-26.5-21.5-48-48-48zm-104 0H152v-72c0-39.7 32.3-72 72-72s72 32.3 72 72v72z'/%3E%3C/svg%3E"); 
                    background-repeat: no-repeat;
                    background-position: 18px center;
                    background-size: 16px;
                }}

                /* Labels */
                .stTextInput label {{
                    display: none !important;
                }}

                /* 6. BUTTON */
                .stButton > button {{
                    width: 100% !important;
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
                    color: white !important;
                    border-radius: 12px !important;
                    height: 50px !important;
                    font-weight: 600 !important;
                    font-size: 1.1rem !important;
                    border: none !important;
                    margin-top: 10px !important;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
                    transition: all 0.3s ease;
                }}
                .stButton > button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4) !important;
                }}
                
                /* Error messages */
                .stAlert {{
                    background-color: rgba(254, 226, 226, 0.9) !important;
                    border: 1px solid #fecaca !important;
                    color: #991b1b !important;
                    border-radius: 8px !important;
                }}

                /* Hide 'Press Enter to submit' text */
                [data-testid="InputInstructions"] {{
                    display: none !important;
                }}

            </style>
        """, unsafe_allow_html=True)

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
            username = st.text_input("USERNAME", placeholder="Kullanıcı Adı")
            password = st.text_input("PASSWORD", type="password", placeholder="Şifre")
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

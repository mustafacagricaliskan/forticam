# FortiCam Project Documentation (v1.6.0)

## 1. Project Overview
**FortiCam** is a secure, role-based management dashboard for FortiManager, designed to simplify specific network operations (like toggling interface status) for varying levels of administrative users. It acts as a middleware between users and the FortiManager JSON-RPC API, providing a streamlined, scalable, and secure UI.

### Key Features
- **Scalable Dashboard:** Supports 200+ devices with integrated **Search** and **Pagination**.
- **Visual Interface Control:** Modern glassmorphism-inspired device cards with model-based icons.
- **Dual Toggle Methods:** Support for standard **DB Update** and high-reliability **Direct Proxy (REST API)** methods.
- **Optimistic UI:** Instant visual feedback on port status changes with background synchronization.
- **Secure Authentication:** LDAP (Active Directory) integration and Local accounts with `bcrypt` hashing.
- **Granular RBAC:** Permissions for Dashboard, Connectivity, System Settings, and Logs.
- **Audit & SIEM:** Detailed local CSV logging and real-time **Syslog/SIEM** integration with test utilities.
- **Container Optimized:** Fully compatible with Docker and OpenShift deployment environments.

## 2. Architecture & Tech Stack
The application follows a modular architecture using Python and Streamlit.

- **Frontend/UI:** Streamlit (Python-based web framework) with custom CSS injection.
- **Backend Logic:** Python 3.11+.
- **Database:** JSON-based local storage (`data/fmg_config.json`) with nested structure and CSV (`data/audit_log.csv`) for logs.
- **API Integration:** Custom `FortiManagerAPI` client supporting JSON-RPC and System Proxy requests.
- **Real-time Monitoring:** Direct device status fetching via FortiManager Proxy to ensure data freshness.

## 3. Directory Structure

```text
FORTICAM/
├── src/
│   ├── app.py              # Main controller, routing, and scalable dashboard logic
│   ├── api_client.py       # FortiManager API client (RPC, Proxy, Scripts)
│   ├── auth_service.py     # Authentication (Bcrypt, LDAP) and RBAC
│   ├── config_service.py   # Atomic configuration management
│   ├── log_service.py      # Audit logging (CSV & SIEM/Syslog)
│   ├── system_service.py   # Connectivity and health checks
│   ├── ui_components.py    # Reusable glassmorphism UI components
│   └── settings_view.py    # Admin settings implementation
├── data/                   # Persistent data (Mounted as Volume in Docker)
│   ├── fmg_config.json     # App configuration (users, fmg settings, profiles)
│   └── audit_log.csv       # User activity logs
├── conductor/              # Conductor Framework (Spec-driven development)
│   ├── archive/            # Completed and archived feature tracks
│   └── tracks/             # Active development tracks
├── MFA Background/         # Visual assets
├── MFA Logo/               # Branding assets
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

## 4. Modules Description

### `src/app.py`
The heart of the application. Handles:
- Scalable device grid with search and pagination logic.
- Optimistic UI state management (`st.session_state`).
- Interface management with real-time status synchronization.

### `src/api_client.py` (`FortiManagerAPI`)
Handles all communication with FortiManager.
- **Standard Mode:** Update DB -> Install Config workflow.
- **Direct Proxy Mode:** Executes REST API (PUT) calls directly to FortiGate via FMG Proxy.
- **Monitor API:** Fetches real-time physical status of interfaces.

### `src/auth_service.py` (`AuthService`)
- **Bcrypt:** Secure local password storage.
- **LDAP:** Robust AD integration with mapping support.
- **Session:** Secure token management and auto-login capabilities.

## 5. Setup & Installation

### Docker Deployment (Recommended)
1. Build the image:
   ```bash
   docker build -t forticam:v1.6.0 .
   ```
2. Run with persistence:
   ```bash
   docker run -d -p 8501:8501 -v $(pwd)/data:/app/data --name forticam forticam:v1.6.0
   ```

### Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Run app: `streamlit run src/app.py`

## 6. Configuration
Configuration is stored in `data/fmg_config.json`.
- **fmg_settings:** `ip`, `token` (Managed via 'FMG Bağlantısı' page).
- **toggle_method:** Choose between `db_update` or `direct_proxy` in Settings.
- **LDAP:** Cluster support, SSL, and Group-to-Profile mappings.

## 7. Version History
- **v1.6.0:** Scalability (Search/Pagination), Direct Proxy (REST), Optimistic UI.
- **v1.5.0:** Refactored Config, Aggressive Cache Clear, SIEM Test Utility.
- **v1.4.0:** Proxy-based Interface Toggling.
- **v1.2.0:** Bcrypt Security, Atomic Writes, ADOM support.

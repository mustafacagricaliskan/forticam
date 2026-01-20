# FortiCam Project Documentation

## 1. Project Overview
**FortiCam** is a secure, role-based management dashboard for FortiManager, designed to simplify specific network operations (like toggling interface status) for varying levels of administrative users. It acts as a middleware between users and the FortiManager JSON-RPC API, providing a streamlined and secure UI.

### Key Features
- **Role-Based Access Control (RBAC):** Granular permissions for Dashboard, System Settings, Logs, etc.
- **Secure Authentication:** Supports local users and LDAP (Active Directory) integration.
- **Device Management:** View managed devices, VDOMs, and interfaces.
- **Port Control:** Enable/Disable network interfaces with audit logging.
- **Audit Logging:** Tracks all critical actions (who, what, when).
- **Modern UI:** Responsive, glassmorphism-styled interface built with Streamlit.
- **Portable:** Can be packaged as a standalone executable.

## 2. Architecture & Tech Stack
The application follows a modular architecture using Python and Streamlit.

- **Frontend/UI:** Streamlit (Python-based web framework).
- **Backend Logic:** Python 3.11+.
- **Database:** JSON-based local storage (`data/config.json`) for configuration and CSV (`data/audit_log.csv`) for logs. In-memory session management.
- **API Integration:** Custom `FortiManagerAPI` client for JSON-RPC communication.
- **Authentication:** `ldap3` library for AD integration, custom session management.

## 3. Directory Structure

```text
FORTICAM/
├── src/
│   ├── app.py              # Main entry point and page routing
│   ├── api_client.py       # FortiManager JSON-RPC API client
│   ├── auth_service.py     # Authentication (Local & LDAP) and Session Management
│   ├── config_service.py   # Configuration persistence (JSON)
│   ├── log_service.py      # Audit logging to CSV
│   ├── system_service.py   # System-level operations (DNS, Certificates)
│   ├── ui_components.py    # Reusable UI components (Login screen, Styles)
│   └── settings_view.py    # Settings page implementation
├── data/                   # Runtime data storage
│   ├── config.json         # App configuration (users, fmg ip, profiles)
│   └── audit_log.csv       # User activity logs
├── MFA Background/         # Background images
├── MFA Logo/               # Branding assets
├── dist_portable/          # Portable distribution artifacts
├── requirements.txt        # Python dependencies
└── run_portable.py         # Launcher script for portable builds
```

## 4. Modules Description

### `src/app.py`
The main application controller. It handles:
- Initialization of session state.
- Routing between pages (Dashboard, Settings, Logs).
- Global error handling and logging configuration.

### `src/api_client.py` (`FortiManagerAPI`)
Handles all communication with FortiManager.
- **Methods:** `login`, `get_devices`, `get_interfaces`, `toggle_interface`, `_install_config`.
- **Logic:** Implements the "Update DB -> Install Config" workflow required by FortiManager to apply changes.

### `src/auth_service.py` (`AuthService`)
Manages security.
- **Authentication:** Validates credentials against Local DB or LDAP.
- **Session:** Manages secure tokens using `SessionState` and cookies.
- **Authorization:** `User` class checks permissions (Global vs Device-specific port access).

### `src/ui_components.py` (`UI`)
Contains visual elements.
- **Login Screen:** A custom-styled, card-based login form with glassmorphism effects.
- **Styling:** Injects custom CSS for a premium look (Bootstrap/Material inspired).
- **Sidebar:** Dynamic sidebar menu based on user permissions.

## 5. Setup & Installation

### Prerequisites
- Python 3.11+
- Access to a FortiManager instance.

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run src/app.py
   ```

### Portable Build
To create a standalone executable (Windows):
1. Ensure `pyinstaller` is installed.
2. Run the build script (if available) or use:
   ```bash
   pyinstaller --onefile --additional-hooks-dir=hooks run_portable.py
   ```

## 6. Configuration
Configuration is stored in `data/config.json`.
- **System:** `fmg_ip`, `api_token`.
- **Auth:** `ldap_settings` (Server, Port, Mappings).
- **Users:** `local_accounts` and `admin_profiles` (Permissions).

## 7. Troubleshooting
- **WebSocket Errors:** "Task exception was never retrieved" errors in console are harmless network noise from browser reloads.
- **Login Issues:** Check `data/config.json` for correct LDAP settings or use the default local admin (`admin` / `admin`).

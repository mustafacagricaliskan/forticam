# Specification: Global Interface Toggle Method Setting

## Overview
Currently, the interface toggle method is either standard (DB Update) or hardcoded to use Proxy/Script for specific ports (e.g., `lan2`). This track introduces a global configuration setting that allows administrators to select the preferred method for *all* interface operations across the application.

## Functional Requirements
1.  **Configuration Schema:**
    *   Add `toggle_method` to `config.json`.
    *   Options:
        *   `db_update` (Default): Update FMG DB -> Install Config.
        *   `direct_proxy` (Alternative): Use FMG System Proxy to call device REST API directly.
2.  **Settings UI:**
    *   In the "System" tab of the Settings page, add a selection control for "Port Kontrol Yöntemi".
    *   Only visible/editable by Super Admin users.
3.  **Application Logic:**
    *   In `src/app.py`, retrieving the global `toggle_method` from config.
    *   Pass this preference to `toggle_interface`.
    *   Remove hardcoded `lan2` logic; rely on the global setting (or per-device overrides if we were that granular, but global is the request).

## Acceptance Criteria
- [ ] Admin can change the toggle method in Settings.
- [ ] The change persists in `config.json`.
- [ ] `toggle_interface` respects the selected method for all ports.
- [ ] UI reflects the change immediately.

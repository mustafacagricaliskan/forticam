# Specification: Refactor Config Structure for FMG Settings

## Overview
Currently, `fmg_ip` and `api_token` are stored at the root level of `config.json`, while other settings like `ldap_settings` and `siem_settings` are grouped. This track aims to refactor the configuration structure to group FMG-related settings under a new `fmg_settings` object.

## Functional Requirements
1.  **New Config Structure:**
    ```json
    {
      "fmg_settings": {
        "ip": "...",
        "token": "..."
      },
      "ldap_settings": { ... },
      ...
    }
    ```
2.  **Migration Logic:**
    *   `ConfigService.load_config()` must detect if `fmg_ip` exists at root.
    *   If found, it should move them to `fmg_settings` and save the config (Migration).
3.  **Code Updates:**
    *   Update `src/config_service.py` to handle the new structure and environment variables.
    *   Update `src/app.py` to read/write from `fmg_settings`.
    *   Update `src/settings_view.py` (if applicable) to use the new structure.

## Acceptance Criteria
- [ ] Config file automatically migrates old root-level keys to `fmg_settings`.
- [ ] Application connects to FMG using the new structure.
- [ ] Environment variables `FMG_IP` and `FMG_TOKEN` still work and override the config.

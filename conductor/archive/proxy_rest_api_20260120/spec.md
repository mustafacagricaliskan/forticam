# Specification: Proxy-based REST API for Interface Control

## Overview
Previous attempts to use CLI scripts via FMG (both object creation and direct monitor/cli execution) have proven unreliable for configuration changes. The `/api/v2/monitor/system/cli` endpoint is likely read-only or restricted for config changes.

To solve this, we will use the **FortiManager System Proxy (`/sys/proxy/json`)** to send standard **REST API (CMDB)** requests directly to the managed device. This bypasses FMG's internal database synchronization logic and acts directly on the device configuration.

## Functional Requirements
1.  **New Method:** `proxy_update_interface(device_name, interface_name, status)` in `FortiManagerAPI`.
    *   **Endpoint:** `/sys/proxy/json` on FMG.
    *   **Target:** `device/{device_name}`.
    *   **Resource:** `/api/v2/cmdb/system/interface/{interface_name}`.
    *   **Action:** `PUT` (update).
    *   **Payload:** `{"status": "up"}` or `{"status": "down"}`.
2.  **Toggle Logic Update:**
    *   Update `toggle_interface` to utilize this new method when `use_script` (or a renamed flag) is True.
    *   Deprecate or remove the unreliable `run_cli_script` CLI injection logic for this use case.

## Acceptance Criteria
- [ ] `proxy_update_interface` successfully sends a PUT request to the device via FMG.
- [ ] The interface status on the physical device changes immediately.
- [ ] The application handles the response correctly (200 OK).

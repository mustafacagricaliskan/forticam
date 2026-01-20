# Specification: GUI Real-time Status Sync

## Overview
When using the Proxy REST API to toggle interfaces, the FortiManager database (DB) is bypassed. Consequently, the GUI, which relies on the FMG DB, does not reflect the change (e.g., interface shows "UP" even after being successfully closed). This track aims to fetch real-time interface status directly from the device via FMG Proxy to ensure the GUI displays the actual state.

## Functional Requirements
1.  **New API Method:** `get_interfaces_realtime(device_name, vdom, adom)` in `FortiManagerAPI`.
    *   Uses `/sys/proxy/json` to query `/api/v2/monitor/system/interface` on the device.
    *   Returns a list of interfaces with their *actual* status (link/admin).
    *   Falls back to standard `get_interfaces` (DB) if the device is unreachable or proxy fails.
2.  **App Integration:**
    *   Update `src/app.py` to use `get_interfaces_realtime` when listing interfaces.
    *   This ensures that even if FMG DB is stale, the user sees the correct status.

## Acceptance Criteria
- [ ] `get_interfaces_realtime` retrieves current status from the physical device.
- [ ] Dashboard displays "KAPALI" immediately after a successful Proxy toggle, even if FMG DB says "UP".
- [ ] Graceful fallback to FMG DB if the device is offline (e.g., after `lan2` closure).

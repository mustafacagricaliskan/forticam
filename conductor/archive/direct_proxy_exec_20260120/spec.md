# Specification: Direct Device Execution via Proxy

## Overview
Script creation on FortiManager is failing due to version/path inconsistencies. To reliably control interfaces (especially those that cut connection upon toggle), we will implement a direct execution method using FortiManager's `/sys/proxy/json` endpoint. This allows sending commands directly to the FortiGate device, bypassing the FMG database and script object creation.

## Functional Requirements
1.  **New Method:** `execute_via_proxy(device_name, commands)` in `FortiManagerAPI`.
    *   Uses `/sys/proxy/json` endpoint.
    *   Sends commands to the device's CLI or API.
    *   Preferred target: `/api/v2/monitor/system/cli` (to execute raw CLI commands) or direct CMDB path if applicable.
2.  **Fallback Strategy:**
    *   Update `toggle_interface` (and `run_cli_script`) to use this proxy method if script creation fails, or make it the primary method for "Script Mode".

## Acceptance Criteria
- [ ] `execute_via_proxy` successfully toggles the interface on the device.
- [ ] No "Object does not exist" errors.
- [ ] Works even if FMG DB sync is pending.

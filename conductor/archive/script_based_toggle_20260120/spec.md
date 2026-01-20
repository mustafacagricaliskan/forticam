# Specification: Script-based Interface Toggling

## Overview
The standard "Update DB -> Install Config" method for toggling interfaces fails for management ports (like `lan2`) because the connection drops immediately upon closure, causing the FMG verification/ACK to fail. This track implements an alternative method using FortiManager **Scripts**.

## Functional Requirements
1.  **New API Method:** `run_script(device_name, script_name, script_content, adom)`
    *   Creates (or executes ad-hoc) a CLI script on FMG targeting the specific device.
    *   Uses the `/dvmdb/adom/{adom}/script/execute` or similar endpoint.
2.  **Toggle Logic Update:**
    *   Update `toggle_interface` to support a `method="script"` parameter.
    *   Generate the CLI script dynamically:
        ```bash
        config system interface
          edit <interface_name>
            set status <up/down>
          next
        end
        ```
    *   Execute the script against the target device.
3.  **Fallback Strategy:**
    *   The application should ideally attempt the Script method for known problematic ports or allow the user (admin) to configure "Preferred Toggle Method" per device/port in settings. For now, we will make it the default retry mechanism or primary mechanism for `lan*` ports if desired.

## Acceptance Criteria
- [ ] `run_script` successfully pushes and executes a script on the FortiGate via FMG.
- [ ] Toggling `lan2` via script correctly changes the status on the physical device.
- [ ] The application reports success even if the connection drops post-script execution (fire-and-forget nature of scripts usually handles this better).

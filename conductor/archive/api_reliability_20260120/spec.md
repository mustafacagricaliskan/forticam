# Specification: API Reliability Improvements

## Overview
Improve the verification logic in `FortiManagerAPI` to use real-time device monitoring data instead of just the configuration database. This ensures that the interface status reported by the application reflects the actual physical/operational state of the FortiGate device.

## Functional Requirements
1.  **New Method:** `get_realtime_interface_status(device_name, interface_name, adom)`
    *   Queries the FMG Monitor API (e.g., `/monitor/system/interface` or similar under `/dvmdb`).
    *   Returns the actual status ('up'/'down').
2.  **Updated Verification:**
    *   In `toggle_interface`, after the configuration change is pushed, use the real-time status for final confirmation.
    *   This provides a double-check: DB is updated AND Device is updated.

## Acceptance Criteria
- [ ] `get_realtime_interface_status` successfully retrieves status from FMG.
- [ ] `toggle_interface` uses this status for verification.
- [ ] Logic gracefully handles cases where real-time monitoring is not supported or fails.

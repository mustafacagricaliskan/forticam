# Specification: Enhance SIEM Testing Utilities

## Overview
Currently, the "Send Test Log" feature in the Settings page writes a test entry to the production `audit_log.csv` file via `log_action`. This pollutes the audit trail with test data. This track aims to create a dedicated test message function that sends data *only* to the SIEM server without persisting it locally.

## Functional Requirements
1.  **New Method:** `send_test_message(user, server, port, protocol)` in `LogService`.
    *   Constructs a standard log payload.
    *   Sends it directly via socket (UDP/TCP).
    *   Does **not** write to CSV.
2.  **UI Update:**
    *   Update the "Test Logu Gönder" button in `src/settings_view.py` to use this new method.
    *   Allow testing even if SIEM is not "enabled" globally, using the values currently in the input fields (to test before saving).

## Acceptance Criteria
- [ ] Clicking "Test Logu Gönder" sends a packet to the specified IP/Port.
- [ ] No new entry appears in the Audit Logs table (`audit_logs.csv`).
- [ ] Users can test connection settings before saving them.

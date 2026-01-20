# Specification: Fix verification failure for "lan2" interface toggle

## Overview
A bug exists where toggling the status (Up/Down) of the "lan2" interface fails during the verification step, even though the command is successfully sent to and processed by FortiManager. Other interfaces work as expected.

## Functional Requirements
1.  Investigate the interface status verification logic in `src/api_client.py`.
2.  Identify why "lan2" specifically fails verification (potential name matching, ID issues, or response parsing errors).
3.  Ensure that after a status change command is sent and the FMG task completes, the app correctly verifies the new state of the interface.
4.  Resolve the "failed to connect fortimanager" error that appears during this specific flow.

## Acceptance Criteria
- [ ] Toggling "lan2" results in a successful UI update showing the new status.
- [ ] No "failed to connect" errors occur during the verification of "lan2".
- [ ] Verification logic is robust for all interface names.
- [ ] Unit tests (if possible) confirm successful verification.

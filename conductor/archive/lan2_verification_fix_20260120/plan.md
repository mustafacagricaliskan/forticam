# Implementation Plan - Fix "lan2" Verification Bug

## Phase 1: Investigation & Reproduction [checkpoint: investigation_complete]
- [x] Task: Review `src/api_client.py` implementation of `toggle_interface` and status verification.
    - [x] Read `src/api_client.py`.
- [x] Task: Add debug logging to capture the exact JSON-RPC responses from FMG for "lan2".
- [x] Task: Identify why verification fails and triggers a connection error.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Bug Fix [checkpoint: bug_fix_implemented]
- [x] Task: Update `FortiManagerAPI.get_interfaces` to accept `adom` and try ADOM-specific paths.
    - [x] Modify `src/api_client.py`.
- [x] Task: Update `track_task` in `src/app.py` to accept and use `adom`.
    - [x] Update function signature and call site.
- [x] Task: Update the call to `track_task` in `src/app.py` to pass the `target_adom`.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Final Verification [checkpoint: 361684b]
- [x] Task: Run existing tests to ensure no regressions.
    - [x] Run `python run_tests.py` (or targeted test).
- [x] Task: Conductor - User Manual Verification 'Bug Fix' (Protocol in workflow.md)

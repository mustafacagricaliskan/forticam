# Implementation Plan - Script-based Toggle

## Phase 1: API Implementation [checkpoint: phase1_api_complete]
- [x] Task: Implement `run_script` method in `src/api_client.py`.
    - [x] Research FMG Script Execution API endpoints.
    - [x] Implement `_execute_script` internal method (implemented as `run_cli_script`).
- [x] Task: Update `toggle_interface` to support script method.
    - [x] Add logic to generate CLI content.
    - [x] Add switch to choose between "db_update" (default) and "script".
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Integration & UI [checkpoint: 2ba9db3]
- [x] Task: Update `src/app.py` to use script method for `lan2` or allow selection.
    - [x] Hardcode `lan2` to use script method for immediate fix testing.
    - [x] (Optional) Add UI toggle in Settings for "Force Script Mode" (Skipped for now, hardcoded fix).
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

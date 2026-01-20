# Implementation Plan - Global Toggle Setting

## Phase 1: Configuration & Settings UI [checkpoint: phase1_ui_complete]
- [x] Task: Update `ConfigService` defaults in `src/config_service.py` to include `toggle_method`.
- [x] Task: Add toggle method selector to `src/settings_view.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Application Logic Integration [checkpoint: global_toggle_complete]
- [x] Task: Update `src/app.py` to use the global setting in `toggle_interface` calls.
    - [x] Remove hardcoded `lan2` check.
    - [x] Read `toggle_method` from session config.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

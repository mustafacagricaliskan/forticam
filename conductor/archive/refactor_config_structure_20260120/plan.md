# Implementation Plan - Refactor Config Structure

## Phase 1: ConfigService Update [checkpoint: config_svc_refactor]
- [x] Task: Update `load_config` in `src/config_service.py` to support `fmg_settings` and migrate legacy keys.
- [x] Task: Update `get_env_or_config` usage for the new structure (Handled in step 1).

## Phase 2: Application Logic Update [checkpoint: config_struct_refactor]
- [x] Task: Update `src/app.py` to read/write `fmg_settings`.
- [x] Task: Update `src/settings_view.py` (if applicable) to read/write `fmg_settings` (Not applicable, logic is in app.py).
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

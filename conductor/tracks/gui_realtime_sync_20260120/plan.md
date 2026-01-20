# Implementation Plan - GUI Real-time Sync

## Phase 1: API Implementation [checkpoint: realtime_ui_sync]
- [x] Task: Implement `get_interfaces_realtime` in `src/api_client.py`.
    - [x] Endpoint: `/api/v2/monitor/system/interface` via Proxy.
    - [x] Map the response format to match `get_interfaces` output (standardize fields).
- [x] Task: Update `get_cached_interfaces` in `src/app.py` to use realtime data.
    - [x] Add logic: Try realtime first -> Fail -> Fallback to DB.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

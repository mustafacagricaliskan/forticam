# Specification: Expand Unit Test Coverage

## Overview
The current unit test suite is minimal. To ensure stability and reliability, especially after recent refactoring and feature additions, we need to expand the test coverage.

## Functional Requirements
1.  **AuthService Tests:**
    *   Test `login` with valid/invalid credentials (mocked).
    *   Test `check_ldap_connectivity`.
    *   Test `has_access_to_port` logic.
2.  **ConfigService Tests:**
    *   Test `load_config` migration logic (legacy to new structure).
    *   Test `save_config` fail-safe merge logic.
    *   Test environment variable overrides.
3.  **FortiManagerAPI Tests:**
    *   Test `toggle_interface` logic (mocked responses).
    *   Test `get_interfaces_realtime` parsing.
    *   Test `proxy_update_interface`.

## Acceptance Criteria
- [ ] New test files created or existing ones updated in `tests/`.
- [ ] All tests pass when run with `pytest`.
- [ ] Code coverage increases (qualitative assessment).

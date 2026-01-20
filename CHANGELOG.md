# Changelog

All notable changes to this project will be documented in this file.

## [v1.6.4] - 2026-01-20
### Added
- Added `CHANGELOG.md` to track version history.

## [v1.6.3] - 2026-01-20
### Changed
- Expanded unit test coverage for `AuthService`, `ConfigService`, and `FortiManagerAPI`.
- Updated test suite to mock external dependencies (`streamlit`, `bcrypt`).

## [v1.6.2] - 2026-01-20
### Fixed
- Fixed configuration persistence issue where FMG settings were lost when saving other settings.
- Implemented fail-safe merge in `ConfigService.save_config`.

## [v1.6.1] - 2026-01-20
### Added
- Centralized version management via `VERSION` file.
- Displayed application version in the Dashboard header.

## [v1.6.0] - 2026-01-20
### Added
- **Scalable Dashboard:** Implemented search, filtering, and pagination for device grid (supports 200+ devices).
- **Direct Proxy Control:** Added support for direct REST API calls to devices via FMG Proxy (bypassing DB sync delays).
- **Optimistic UI:** Dashboard now reflects port status changes immediately using temporary session state.
- **Real-time Sync:** Interface list now fetches live status from device Monitor API.
- **SIEM Testing:** Added dedicated "Send Test Log" utility in Settings.
- **Global Toggle Setting:** Admin option to switch between "Standard (DB)" and "Fast (Proxy)" control methods.

### Changed
- Refactored `config.json` structure to group FMG settings under `fmg_settings`.
- Polished Login UI with modern CSS, better inputs, and Turkish labels.
- Reduced interface cache TTL to 1 second for better responsiveness.

### Fixed
- Fixed "Object does not exist" error in script creation by switching to direct proxy execution.
- Fixed `str object has no attribute get` error in verification logic with better type checking.
- Fixed glassmorphism CSS string formatting bug.

## [v1.2.0] - 2026-01-20
### Security
- Implemented `bcrypt` password hashing for local accounts.
### Reliability
- Implemented atomic file writing for `config.json` to prevent corruption.
- Improved `FortiManagerAPI` error handling and ADOM support.

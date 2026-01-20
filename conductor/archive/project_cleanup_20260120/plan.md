# Implementation Plan - Project Cleanup and Deprecation

This plan outlines the steps to remove unnecessary files, scripts, and code modules to streamline the project and focus on the Docker/OpenShift deployment model.

## Phase 1: Artifact and Temporary File Cleanup [checkpoint: f446745]
- [x] Task: Remove root-level temporary and screenshot files.
    - [x] Delete all files matching `.tmp-*`.
    - [x] Delete `22.png`, `login_page.png`, `hatalı_sayfa.png`, and `Ekran görüntüsü 2026-01-14 160829.png`.
- [x] Task: Remove redundant tar archives.
    - [x] Delete `.tmp-fortimanager_openshift1.tar869838307`.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Portable Build Deprecation [checkpoint: 91a7e43]
- [x] Task: Remove portable build directory and assets.
    - [x] Delete the `dist_portable/` directory.
    - [x] Delete `README_PORTABLE.txt`.
- [x] Task: Remove portable build scripts and launchers.
    - [x] Delete `build_exe.bat`, `create_portable_package.ps1`.
    - [x] Delete `run_portable.py` and `src/run_portable.py` (if duplicate exists).
- [x] Task: Update documentation.
    - [x] Remove portable build sections from `README.md`.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Codebase Streamlining
- [x] Task: Remove unused code modules.
    - [x] Delete `src/email_service.py`.
- [x] Task: Cleanup dependencies and imports.
    - [x] Search for and remove any imports of `email_service` in `src/app.py` or other files.
    - [x] Verify `requirements.txt` doesn't contain packages solely used by removed modules (if identifiable).
- [x] Task: Final Verification.
    - [x] Run `python run_tests.py` to ensure no regressions.
    - [x] Build Docker image to ensure the environment is still valid.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

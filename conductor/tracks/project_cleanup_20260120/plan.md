# Implementation Plan - Project Cleanup and Deprecation

This plan outlines the steps to remove unnecessary files, scripts, and code modules to streamline the project and focus on the Docker/OpenShift deployment model.

## Phase 1: Artifact and Temporary File Cleanup
- [x] Task: Remove root-level temporary and screenshot files.
    - [x] Delete all files matching `.tmp-*`.
    - [x] Delete `22.png`, `login_page.png`, `hatalı_sayfa.png`, and `Ekran görüntüsü 2026-01-14 160829.png`.
- [x] Task: Remove redundant tar archives.
    - [x] Delete `.tmp-fortimanager_openshift1.tar869838307`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Portable Build Deprecation
- [ ] Task: Remove portable build directory and assets.
    - [ ] Delete the `dist_portable/` directory.
    - [ ] Delete `README_PORTABLE.txt`.
- [ ] Task: Remove portable build scripts and launchers.
    - [ ] Delete `build_exe.bat`, `create_portable_package.ps1`.
    - [ ] Delete `run_portable.py` and `src/run_portable.py` (if duplicate exists).
- [ ] Task: Update documentation.
    - [ ] Remove portable build sections from `README.md`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Codebase Streamlining
- [ ] Task: Remove unused code modules.
    - [ ] Delete `src/email_service.py`.
- [ ] Task: Cleanup dependencies and imports.
    - [ ] Search for and remove any imports of `email_service` in `src/app.py` or other files.
    - [ ] Verify `requirements.txt` doesn't contain packages solely used by removed modules (if identifiable).
- [ ] Task: Final Verification.
    - [ ] Run `python run_tests.py` to ensure no regressions.
    - [ ] Build Docker image to ensure the environment is still valid.
- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

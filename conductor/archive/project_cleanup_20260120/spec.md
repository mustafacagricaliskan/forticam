# Specification: Project Cleanup and Deprecation of Portable Builds

## Overview
This track focuses on cleaning up the project repository by removing unnecessary artifacts, temporary files, unused code modules, and fully deprecating the "portable executable" build approach in favor of the modern Docker/OpenShift deployment strategy.

## Functional Requirements
### 1. Artifact & Temporary File Removal
- Delete all temporary files in the root directory (e.g., `.tmp-...`, `*.png` screenshots).
- Delete old or redundant archive files (`*.tar`) in the root, excluding intentional export artifacts if specified (though the goal is a "clean" root).
- Remove image assets used for debugging or documentation that are not part of the application UI (e.g., `22.png`, `login_page.png`, `hatalı_sayfa.png`).

### 2. Portable Build Deprecation
- Delete the `dist_portable/` directory and all its contents.
- Delete portable build scripts: `build_exe.bat`, `create_portable_package.ps1`.
- Delete the portable launcher: `run_portable.py`.
- Delete `README_PORTABLE.txt`.
- Update the main `README.md` to remove any instructions related to portable builds.

### 3. Codebase Cleanup
- Remove `src/email_service.py` as it is not currently utilized by the core product features.
- Remove any unused imports or dead code discovered during the removal of the above modules.

## Acceptance Criteria
- [ ] The root directory is free of `.tmp`, `.png`, and redundant `.tar` files.
- [ ] All files and folders related to portable builds are removed.
- [ ] `src/email_service.py` is deleted and the application starts successfully.
- [ ] `README.md` only contains relevant information for the current Docker-based workflow.
- [ ] `run_tests.py` passes all tests after cleanup.

## Out of Scope
- Refactoring active code modules (unless directly related to removing dead code/imports).
- Changes to the Docker or OpenShift configuration.
- Database (`data/`) cleanup.

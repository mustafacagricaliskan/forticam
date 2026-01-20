# Specification - Connection Health Check

## Overview
Implement a health check system that verifies connectivity to the FortiManager API and the LDAP server. This ensures that the application is fully functional before users attempt operations.

## Requirements
- **Startup Check:** Automatically test connectivity to FortiManager and LDAP when the application starts.
- **Settings View Indicators:** Add a "Health Status" section in the Settings page showing the status of each connection (e.g., Green/Red indicators).
- **Manual Retry:** Provide a button to re-trigger the health check without restarting the app.
- **Timeout Handling:** Implement short timeouts for health checks to prevent UI freezing.

## Technical Details
- Use `requests` for FMG connectivity test.
- Use `ldap3` for LDAP server availability test.
- Store health status in `st.session_state`.

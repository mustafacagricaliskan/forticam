# Initial Concept
A secure, role-based management dashboard for FortiManager, designed to simplify specific network operations (like toggling interface status) for varying levels of administrative users.

# Product Definition - FortiCam

## Target Audience
- **Help Desk/Support Staff:** The primary users who need limited, safe permissions to perform routine port management tasks without direct access to the full FortiManager environment.

## Core Goals
- **Operational Simplicity:** Abstract and simplify complex FortiManager JSON-RPC API operations into a user-friendly, single-click interface suitable for non-specialist support staff.

## Security & Access Control
- **Strict Role-Based Access Control (RBAC):** Implementation of granular permissions to ensure users can only view and modify specific interfaces they are authorized to manage.

## Key Features
- **Visual Interface Control:** A modern, visual dashboard featuring glassmorphism-inspired device cards and distinct status indicators (AÇIK/KAPALI) for intuitive port management and real-time operational awareness.
- **Connection Health Monitoring:** Automatic connectivity checks for FortiManager and LDAP services on startup, with visual status indicators and manual refresh capabilities in the Settings view.

# Tech Stack - FortiCam

## Backend & Core Logic
- **Python 3.11+:** The primary programming language for application logic, API communication, and data handling.
- **Requests:** Used for efficient JSON-RPC communication with the FortiManager API.
- **LDAP3:** Handles secure authentication against Active Directory/LDAP servers.

## Frontend & UI
- **Streamlit (v1.52.2):** High-performance web framework for Python, used to build the responsive, glassmorphism-styled dashboard.
- **Extra-Streamlit-Components:** Utilized for enhanced UI features like session and cookie management.

## Data Management
- **Pandas:** Employed for data manipulation, filtering, and preparing logs for CSV export.
- **Local Persistence:** 
    - **JSON (`data/config.json`):** Stores application settings, user accounts, and RBAC profiles.
    - **CSV (`data/audit_log.csv`):** Durable storage for user activity and audit trails.

## Infrastructure & Deployment
- **Docker:** Containerized for portability and consistent environments.
- **OpenShift / Kubernetes:** Configured for rootless deployment with arbitrary UID support for enhanced security in enterprise environments.

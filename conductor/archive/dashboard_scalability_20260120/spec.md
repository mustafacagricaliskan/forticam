# Specification: Dashboard Scalability Improvements

## Overview
As the number of managed devices grows (e.g., >200), the current card-based grid layout becomes unwieldy. Users struggle to find specific devices. This track aims to implement search, filtering, and pagination controls to make the dashboard scalable and user-friendly for large environments.

## Functional Requirements
1.  **Search Bar:**
    *   Add a text input field at the top of the device list.
    *   Filter devices dynamically by **Name**, **IP**, or **Serial/Model**.
2.  **Pagination:**
    *   Limit the number of devices displayed per page (e.g., 18 or 21 cards).
    *   Add "Previous" and "Next" buttons to navigate pages.
3.  **Status Filter:**
    *   Optional: Add a "Show only Offline" or "Show only Online" toggle/multiselect.

## Acceptance Criteria
- [ ] Users can type in the search bar to instantly filter the device cards.
- [ ] Large lists are broken down into pages.
- [ ] The layout remains responsive and does not break with empty results.

# Functional Requirements

**Project:** FactoryPulse AI
**Version:** 1.1
**Status:** Draft
**Change Note (v1.1):** Every functional requirement now has a formal `FR-[CATEGORY]-[NUMBER]` ID. Two new categories (**User Management**, **System / Cross-Cutting**) were split out to match the structure already used in [[Use_Cases]] and [[User_Stories]]. Several items are marked **[PROPOSED ADDITION]** — these fill gaps found during the requirements audit where a User Story or Use Case already implied a capability that had no Functional Requirement bullet. Nothing marked this way was invented from outside the existing documents; each is explained inline. MVP / Post-MVP status follows directly from the priority already assigned to the related User Story in [[User_Stories]] (High = MVP, Medium/Low = Post-MVP), per that document's own Section 10 definition.

---

## Authentication (FR-AUTH)

| ID | Requirement | MVP Status |
|---|---|---|
| FR-AUTH-001 | User Login | MVP |
| FR-AUTH-002 | User Logout | MVP |
| FR-AUTH-003 | Password Reset | Post-MVP |

---

## User Management (FR-USER)

> **v1.1 change:** This category is new. It separates account/role administration from login/logout mechanics, mirroring the split already present in [[Use_Cases]] (Section 3 "Authentication" vs. Section 10 "User Management"). Role-Based Access Control was moved here from Authentication because it is administered here (who gets which role), even though it is *enforced* everywhere.

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-USER-001 | Manage User Accounts (create, update, deactivate) | MVP | **[PROPOSED ADDITION]** — US-ADM-001 and UC-USER-001 already describe this capability; no FR bullet previously existed for it. |
| FR-USER-002 | Role-Based Access Control (assign roles/permissions) | MVP | Moved from Authentication (was implicit in the original "Role Based Access Control" bullet). |
| FR-USER-003 | System Configuration | Post-MVP | **[PROPOSED ADDITION]** — supports US-ADM-003, which previously had no FR. |
| FR-USER-004 | Audit Logs | Post-MVP | **[PROPOSED ADDITION]** — supports US-ADM-004, which previously had no FR. |

---

## Machine Management (FR-MON)

> Prefix `MON` (not `MACH`) is used deliberately, to stay consistent with the `UC-MON-###` Use Case naming already established in [[Use_Cases]], since these requirements are fulfilled by the same "Monitoring" Use Cases.

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-MON-001 | Create Machine | MVP | Previously had no supporting User Story or Use Case — see FR-MON-001/002/003 note below. |
| FR-MON-002 | Update Machine | MVP | |
| FR-MON-003 | Delete Machine | MVP | |
| FR-MON-004 | View Machine Details | MVP | |
| FR-MON-005 | Monitor Machine Availability / Downtime | MVP | **[PROPOSED ADDITION]** — supports US-PM-003 (High priority / MVP), which previously had no FR. |

> **Machine CRUD gap (resolved via PROPOSED ADDITION, not a new FR — the FR bullets already existed):** FR-MON-001/002/003 have existed in Functional_Requirements.md since v1.0, and "Machine registration" is explicitly in-scope per [[Business_Requirements]] Section 8.1. However, no User Story or Use Case previously covered *who* performs this. A new User Story (**US-ADM-005**, marked PROPOSED ADDITION) and a new Use Case (**UC-MACH-001**, marked PROPOSED ADDITION) were added to close this gap — see [[User_Stories]] and [[Use_Cases]].

---

## Sensor Management (FR-SENSOR)

| ID | Requirement | MVP Status |
|---|---|---|
| FR-SENSOR-001 | Register Sensors | MVP |
| FR-SENSOR-002 | View Sensor Data | MVP |
| FR-SENSOR-003 | Update Sensor Information | Post-MVP |

---

## Dashboard (FR-DASH)

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-DASH-001 | KPI Cards | MVP | |
| FR-DASH-002 | Real-time Monitoring | MVP | |
| FR-DASH-003 | Interactive Charts | MVP | |
| FR-DASH-004 | Alerts Overview | MVP | |
| FR-DASH-005 | Machine Comparison | Post-MVP | **[PROPOSED ADDITION]** — supports US-ME-007 (Medium priority / Post-MVP), which previously had no FR. No dedicated Use Case is created yet; per US-ME-007's own Post-MVP priority, its Use Case will be authored when the feature is scheduled for implementation. |

---

## Maintenance (FR-MAINT)

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-MAINT-001 | Create Maintenance Task | MVP | |
| FR-MAINT-002 | Assign Technician | MVP | |
| FR-MAINT-003 | Track Status | MVP | |
| FR-MAINT-004 | Maintenance History | MVP | |
| FR-MAINT-005 | Maintenance Costs (tracking) | Post-MVP | **[PROPOSED ADDITION]** — supports US-MM-006 (Medium priority / Post-MVP). BRD Section 5 (Financial Benefits) already anticipates cost visibility; this FR closes the gap identified in the audit. No dedicated Use Case yet — Post-MVP, to be authored when scheduled. |

---

## Alerts (FR-ALERT)

| ID | Requirement | MVP Status |
|---|---|---|
| FR-ALERT-001 | Generate Alerts | MVP |
| FR-ALERT-002 | Alert Priorities | MVP |
| FR-ALERT-003 | Alert Resolution | MVP |

---

## AI (FR-AI)

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-AI-001 | Anomaly Detection | MVP | |
| FR-AI-002 | Failure Prediction | MVP | Includes machine risk classification/scoring (BRD 8.1 "Machine risk scoring" is delivered as part of this requirement's output — the failure-risk level shown in UC-PRED-001 — rather than as a separate requirement). |
| FR-AI-003 | AI Recommendations | Post-MVP | Matches US-ME-008's Medium priority. |
| FR-AI-004 | Explainable AI / Prediction Explanation | MVP | Fills a documentation gap: US-ME-006, UC-PRED-002, and NFR-ML-004 already fully describe this capability; it simply had no FR bullet in v1.0. |
| FR-AI-005 | Remaining Useful Life (RUL) Prediction | **Post-MVP** | See AI/ML consistency decision below. |

> **AI/ML consistency decision — RUL Prediction:** In v1.0, RUL Prediction appeared only in this document, with no support in the BRD, User Stories, or Use Cases. Three options were considered: (A) treat it as implicitly covered by Failure Prediction, (B) add it explicitly to BRD scope, (C) mark it Post-MVP, (D) remove it. **Decision: (C) Post-MVP.** RUL (a continuous time-to-failure estimate) is technically distinct from Failure Prediction (a risk classification/probability), so folding it into FR-AI-002 (Option A) would misrepresent it. BRD does not currently list it as in-scope, and the RTM's own MVP Traceability list (Section 10) never included it, which is a strong signal it was already intended to come later. It is kept in Functional_Requirements.md — not deleted — because [[Non_Functional_Requirements]]'s NFR-ML-001 already anticipates regression-style metrics (MAE, RMSE) commonly used for RUL, suggesting it is a genuine near-term intention, just not MVP. No User Story or Use Case exists yet for it; both should be authored once it is scheduled.

---

## Reporting (FR-REPORT)

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-REPORT-001 | Generate Reports | MVP | |
| FR-REPORT-002 | Maintenance KPI Reporting (MTBF, MTTR, Downtime) | MVP | **[NEW]** — supports US-MM-007 (High priority / MVP), which previously had no FR. Fulfilled by the existing UC-REPORT-001 (report type = maintenance KPIs), no new Use Case needed. |
| FR-REPORT-003 | Performance Trend Reporting | Post-MVP | **[NEW]** — supports US-PM-004 (Medium priority / Post-MVP). Fulfilled by the existing UC-REPORT-001 (report type = trend analysis over a date range), no new Use Case needed. |
| FR-REPORT-004 | Export PDF | MVP | |
| FR-REPORT-005 | Export CSV | MVP | |

---

## System / Cross-Cutting (FR-SYS)

> **v1.1 change:** New category. Search/Filtering and Notifications are cross-cutting capabilities that apply across Machines, Alerts, and Maintenance Tasks rather than belonging to one functional area — consistent with how the task instructions describe Notifications as triggered by Alerts and Maintenance events rather than a standalone workflow.

| ID | Requirement | MVP Status | Note |
|---|---|---|---|
| FR-SYS-001 | Search and Filtering (machines, alerts, maintenance tasks) | Post-MVP | **[PROPOSED ADDITION]** — supports US-SYS-003 (Medium priority / Post-MVP), which previously had no FR. Cross-cutting; no dedicated Use Case — it is a capability layered onto existing monitoring/alert/maintenance screens. |
| FR-SYS-002 | Notifications (triggered by alerts, task assignment, and other system events) | Post-MVP | **[PROPOSED ADDITION]** — supports US-SYS-004 (Medium priority / Post-MVP), which previously had no FR. Cross-cutting by design; not given its own Use Case, since it is a delivery mechanism for events already generated by UC-ALERT-001/UC-ALERT-002 and UC-MAINT-002 rather than a new interaction. |

---

## Related Documents

- [[Software_Requirements_Specification]]
- [[User_Stories]]
- [[Use_Cases]]
- [[Business_Requirements]]
- [[Requirements_Traceability_Matrix]]

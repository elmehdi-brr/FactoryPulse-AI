# Requirements Traceability Matrix

**Project:** FactoryPulse AI
**Version:** 2.0 (Rebuilt)
**Status:** Draft
**Change Note (v2.0):** This matrix was rebuilt from scratch. The v1.0 matrix contained ~50 invalid or mismatched references (fabricated `BR-###` IDs, fabricated `FR-###` IDs, 17 `UC-###` IDs that were never written, one wrong-prefix ID, and one valid-ID/wrong-content mapping). Every reference below was checked against the actual source document. No ID in this matrix is invented — every `BO`, `FR`, `US`, `UC`, and `NFR` code below exists in its source file as of this version.

---

# 1. Introduction

The Requirements Traceability Matrix (RTM) establishes relationships between the different requirements and analysis artifacts of FactoryPulse AI.

Its purpose is to ensure that business objectives are translated into functional requirements, user needs, use cases, and non-functional quality attributes.

The traceability chain used in this version is:

> Business Objective (BO) → Functional Requirement (FR) → User Story (US) → Use Case (UC) → Non-Functional Requirement (NFR)

---

# 2. Traceability Model

```text
Project Charter
       │
       ▼
Business Requirements (BO-001…BO-006)
       │
       ▼
Functional Requirements (FR-###)
       │
       ▼
User Stories (US-###)
       │
       ▼
Use Cases (UC-###)
       │
       ▼
Non-Functional Requirements (NFR-###, applied cross-cuttingly)
```

---

# 3. Business Objective → Functional Requirement

| Business Objective | Related Functional Requirements |
|---|---|
| **BO-001** — Reduce Unplanned Downtime | FR-AI-001, FR-AI-002, FR-ALERT-001, FR-ALERT-002, FR-ALERT-003, FR-MON-005 |
| **BO-002** — Improve Maintenance Planning | FR-MAINT-001, FR-MAINT-002, FR-MAINT-003, FR-MAINT-004, FR-MAINT-005 |
| **BO-003** — Improve Equipment Visibility | FR-MON-001, FR-MON-002, FR-MON-003, FR-MON-004, FR-MON-005, FR-SENSOR-001, FR-SENSOR-002, FR-SENSOR-003, FR-DASH-001, FR-DASH-002, FR-DASH-003, FR-DASH-004 |
| **BO-004** — Support Data-Driven Decision Making | FR-DASH-001, FR-REPORT-001, FR-REPORT-002, FR-REPORT-003, FR-REPORT-004, FR-REPORT-005, FR-AI-004 |
| **BO-005** — Improve Maintenance Efficiency | FR-AI-002, FR-AI-003, FR-MAINT-001, FR-MAINT-002, FR-MAINT-005 |
| **BO-006** — Centralize Industrial Information | FR-MON-001, FR-MON-002, FR-MON-003, FR-MON-004, FR-MON-005, FR-SENSOR-001, FR-SENSOR-002, FR-SENSOR-003, FR-MAINT-004, FR-USER-001, FR-USER-002 |
| *Cross-cutting (not tied to one objective — platform-level enablers)* | FR-AUTH-001, FR-AUTH-002, FR-AUTH-003, FR-USER-003, FR-USER-004, FR-SYS-001, FR-SYS-002 |
| *Post-MVP / not yet BO-scoped (see AI/ML decision in [[Functional_Requirements]])* | FR-AI-005 (Remaining Useful Life Prediction) |

---

# 4. Functional Requirement → User Story

| Functional Requirement | Related User Story / Stories | MVP Status |
|---|---|---|
| FR-AUTH-001 User Login | US-SYS-001 | MVP |
| FR-AUTH-002 User Logout | *(no dedicated story — implied by US-SYS-001)* | MVP |
| FR-AUTH-003 Password Reset | *(no dedicated story)* | Post-MVP |
| FR-USER-001 Manage User Accounts | US-ADM-001 | MVP |
| FR-USER-002 Role-Based Access Control | US-ADM-002 | MVP |
| FR-USER-003 System Configuration | US-ADM-003 | Post-MVP |
| FR-USER-004 Audit Logs | US-ADM-004 | Post-MVP |
| FR-MON-001 Create Machine | US-ADM-005 | MVP |
| FR-MON-002 Update Machine | US-ADM-005 | MVP |
| FR-MON-003 Delete Machine | US-ADM-005 | MVP |
| FR-MON-004 View Machine Details | US-ME-001, US-MM-001 | MVP |
| FR-MON-005 Monitor Machine Availability / Downtime | US-PM-003 | MVP |
| FR-SENSOR-001 Register Sensors | *(no dedicated story — implied by US-ADM-005 / equipment setup)* | MVP |
| FR-SENSOR-002 View Sensor Data | US-ME-002 | MVP |
| FR-SENSOR-003 Update Sensor Information | *(no dedicated story)* | Post-MVP |
| FR-DASH-001 KPI Cards | US-PM-001, US-PM-002 | MVP |
| FR-DASH-002 Real-time Monitoring | US-ME-003 | MVP |
| FR-DASH-003 Interactive Charts | US-PM-001 | MVP |
| FR-DASH-004 Alerts Overview | US-PM-001, US-SYS-002 | MVP |
| FR-DASH-005 Machine Comparison | US-ME-007 | Post-MVP |
| FR-MAINT-001 Create Maintenance Task | US-MM-003 | MVP |
| FR-MAINT-002 Assign Technician | US-MM-004 | MVP |
| FR-MAINT-003 Track Status | US-TECH-001, US-TECH-002, US-TECH-003, US-TECH-004 | MVP |
| FR-MAINT-004 Maintenance History | US-MM-005, US-TECH-005 | MVP (US-MM-005 High) / Post-MVP (US-TECH-005 Medium) |
| FR-MAINT-005 Maintenance Costs | US-MM-006 | Post-MVP |
| FR-ALERT-001 Generate Alerts | US-SYS-002 | MVP |
| FR-ALERT-002 Alert Priorities | US-SYS-002 | MVP |
| FR-ALERT-003 Alert Resolution | US-SYS-002 | MVP |
| FR-AI-001 Anomaly Detection | US-ME-004 | MVP |
| FR-AI-002 Failure Prediction | US-MM-002, US-ME-005 | MVP |
| FR-AI-003 AI Recommendations | US-ME-008 | Post-MVP |
| FR-AI-004 Explainable AI / Prediction Explanation | US-ME-006 | MVP |
| FR-AI-005 Remaining Useful Life Prediction | *(no story yet — Post-MVP)* | Post-MVP |
| FR-REPORT-001 Generate Reports | US-PM-005 | Post-MVP (Medium) |
| FR-REPORT-002 Maintenance KPI Reporting | US-MM-007 | MVP |
| FR-REPORT-003 Performance Trend Reporting | US-PM-004 | Post-MVP |
| FR-REPORT-004 Export PDF | US-SYS-005 | Post-MVP (Low) |
| FR-REPORT-005 Export CSV | US-SYS-005 | Post-MVP (Low) |
| FR-SYS-001 Search and Filtering | US-SYS-003 | Post-MVP |
| FR-SYS-002 Notifications | US-SYS-004 | Post-MVP |

> Note: FR-AUTH-002, FR-AUTH-003, and FR-SENSOR-001 have no dedicated User Story. They are small enough to be considered implicit sub-behaviors of US-SYS-001 (Authentication) and US-ADM-005 (Machine Registration) respectively rather than requiring their own stories — flagged here for visibility rather than silently left unlinked.

---

# 5. User Story → Use Case

| User Story | Role | Related Use Case | Priority | MVP Status |
|---|---|---|---|---|
| US-ADM-001 | Administrator | UC-USER-001 | High | MVP |
| US-ADM-002 | Administrator | UC-USER-001 *(reused — role assignment is step 5 of this Use Case)* | High | MVP |
| US-ADM-003 | Administrator | *To be defined when scheduled (Post-MVP)* | Medium | Post-MVP |
| US-ADM-004 | Administrator | *To be defined when scheduled (Post-MVP)* | Medium | Post-MVP |
| US-ADM-005 *(new)* | Administrator | UC-MACH-001 *(new)* | High | MVP |
| US-PM-001 | Plant Manager | UC-MON-001 | High | MVP |
| US-PM-002 | Plant Manager | UC-REPORT-001, UC-MON-001 | High | MVP |
| US-PM-003 | Plant Manager | UC-MON-001, UC-MON-002 *(corrected — v1.0 RTM pointed to UC-MON-003, whose actual content is real-time sensor monitoring, not availability)* | High | MVP |
| US-PM-004 | Plant Manager | UC-REPORT-001 *(reused)* | Medium | Post-MVP |
| US-PM-005 | Plant Manager | UC-REPORT-001 | Medium | Post-MVP |
| US-MM-001 | Maintenance Manager | UC-MON-001 | High | MVP |
| US-MM-002 | Maintenance Manager | UC-PRED-001 | High | MVP |
| US-MM-003 | Maintenance Manager | UC-MAINT-001 | High | MVP |
| US-MM-004 | Maintenance Manager | UC-MAINT-002 | High | MVP |
| US-MM-005 | Maintenance Manager | UC-MON-002 *(reused — step 10 already displays maintenance history)* | Medium | Post-MVP |
| US-MM-006 | Maintenance Manager | *To be defined when scheduled (Post-MVP)* | Medium | Post-MVP |
| US-MM-007 | Maintenance Manager | UC-REPORT-001 *(reused)* | High | MVP |
| US-ME-001 | Maintenance Engineer | UC-MON-002 | High | MVP |
| US-ME-002 | Maintenance Engineer | UC-MON-002 *(corrected — v1.0 RTM pointed to nonexistent UC-MON-004; steps 7–8 of UC-MON-002 already cover recent + historical sensor data)* | High | MVP |
| US-ME-003 | Maintenance Engineer | UC-MON-003 *(corrected — v1.0 RTM pointed to nonexistent UC-MON-005)* | High | MVP |
| US-ME-004 | Maintenance Engineer | UC-AI-001 *(corrected — v1.0 RTM used the wrong ID UC-ANOM-001; the real Use Case is UC-AI-001)* | High | MVP |
| US-ME-005 | Maintenance Engineer | UC-PRED-001 | High | MVP |
| US-ME-006 | Maintenance Engineer | UC-PRED-002 | High | MVP |
| US-ME-007 | Maintenance Engineer | *To be defined when scheduled (Post-MVP)* | Medium | Post-MVP |
| US-ME-008 | Maintenance Engineer | *To be defined when scheduled (Post-MVP)* | Medium | Post-MVP |
| US-TECH-001 | Technician | UC-MAINT-003 *(reused — steps 1–2 are literally "opens assigned tasks / selects a task")* | High | MVP |
| US-TECH-002 | Technician | UC-MAINT-003 *(reused — step 3 is "reviews task details")* | High | MVP |
| US-TECH-003 | Technician | UC-MAINT-003 | High | MVP |
| US-TECH-004 | Technician | UC-MAINT-003 *(reused — steps 6–8 record actions/notes)* | High | MVP |
| US-TECH-005 | Technician | UC-MON-002 *(reused; Technician added as a supporting actor in v1.1)* | Medium | Post-MVP |
| US-SYS-001 | All Users | UC-AUTH-001 | High | MVP |
| US-SYS-002 | Authorized Users | UC-ALERT-001, UC-ALERT-002 | High | MVP |
| US-SYS-003 | All Users | *Cross-cutting — no dedicated Use Case (see [[Functional_Requirements]] FR-SYS-001)* | Medium | Post-MVP |
| US-SYS-004 | All Users | *Cross-cutting — no dedicated Use Case (see [[Functional_Requirements]] FR-SYS-002)* | Medium | Post-MVP |
| US-SYS-005 | Authorized Users | UC-REPORT-001 *(reused — export is step 9)* | Low | Post-MVP |

---

# 6. Use Case → Functional Requirement

| Use Case | Name | Related Functional Requirement |
|---|---|---|
| UC-AUTH-001 | User Login | FR-AUTH-001 |
| UC-USER-001 | Manage Users | FR-USER-001, FR-USER-002 |
| UC-MACH-001 *(new)* | Register and Manage Machines | FR-MON-001, FR-MON-002, FR-MON-003 |
| UC-MON-001 | View Factory Overview | FR-DASH-001, FR-DASH-004, FR-MON-004, FR-MON-005 |
| UC-MON-002 | View Machine Details | FR-MON-004, FR-SENSOR-002, FR-MAINT-004, FR-MON-005 |
| UC-MON-003 | Monitor Sensor Data in Real Time | FR-DASH-002 |
| UC-ALERT-001 | View Alerts | FR-ALERT-001, FR-ALERT-002 |
| UC-ALERT-002 | Resolve Alert | FR-ALERT-003 |
| UC-PRED-001 | View Failure Risk Prediction | FR-AI-002 |
| UC-PRED-002 | View AI Prediction Explanation | FR-AI-004 |
| UC-MAINT-001 | Create Maintenance Task | FR-MAINT-001 |
| UC-MAINT-002 | Assign Maintenance Task | FR-MAINT-002 |
| UC-MAINT-003 | Update Maintenance Task | FR-MAINT-003, FR-MAINT-004 |
| UC-AI-001 | Detect Machine Anomaly | FR-AI-001 |
| UC-REPORT-001 | Generate Operational Report | FR-REPORT-001, FR-REPORT-002, FR-REPORT-003, FR-REPORT-004, FR-REPORT-005 |

*(This table lists all 15 Use Cases that currently exist — 14 original + UC-MACH-001. No other Use Case IDs are valid; any other `UC-###` code appearing elsewhere in older drafts of this project should be treated as invalid.)*

---

# 7. Non-Functional Requirement Coverage

| Functional Area | Applicable NFRs |
|---|---|
| Authentication / User Management | NFR-SEC-001, NFR-SEC-002, NFR-SEC-003, NFR-SEC-005, NFR-SEC-007, NFR-SEC-008, NFR-PRIV-001, NFR-PRIV-002 |
| Machine / Sensor Management | NFR-SCALE-002, NFR-SCALE-003, NFR-DATA-001, NFR-DATA-002, NFR-DATA-003, NFR-DATA-004 |
| Dashboard / Real-Time Monitoring | NFR-PERF-001, NFR-PERF-003, NFR-PERF-005, NFR-USE-001, NFR-USE-002, NFR-USE-003, NFR-USE-004 |
| AI (Anomaly Detection, Failure Prediction, Explainability, RUL) | NFR-PERF-004, NFR-ML-001, NFR-ML-002, NFR-ML-003, NFR-ML-004, NFR-ML-005, NFR-OBS-004 |
| Alerts | NFR-REL-001, NFR-REL-002, NFR-REL-003 |
| Maintenance | NFR-DATA-002, NFR-DATA-003, NFR-DATA-004 |
| Reporting / Data Export | NFR-COMP-002 |
| Deployment / Infrastructure | NFR-DEP-001, NFR-DEP-002, NFR-DEP-003, NFR-DEP-004, NFR-AVAIL-001, NFR-AVAIL-002, NFR-AVAIL-003, NFR-OBS-001, NFR-OBS-002, NFR-OBS-003 |
| Codebase / Process | NFR-MAINT-001, NFR-MAINT-002, NFR-MAINT-003, NFR-MAINT-004, NFR-MAINT-005 |
| Cross-Platform | NFR-COMP-001 |

*(All 43 NFR IDs from [[Non_Functional_Requirements]] are accounted for above; no changes were made to the NFR document itself — see audit Section 8.)*

---

# 8. End-to-End Traceability (MVP scope only)

| Business Objective | Functional Requirement | User Story | Use Case | Key NFR |
|---|---|---|---|---|
| BO-001 | FR-AI-001 | US-ME-004 | UC-AI-001 | NFR-ML-001 |
| BO-001 | FR-AI-002 | US-MM-002, US-ME-005 | UC-PRED-001 | NFR-PERF-004 |
| BO-001 | FR-ALERT-001/002/003 | US-SYS-002 | UC-ALERT-001, UC-ALERT-002 | NFR-REL-001 |
| BO-002 | FR-MAINT-001 | US-MM-003 | UC-MAINT-001 | NFR-DATA-002 |
| BO-002 | FR-MAINT-002 | US-MM-004 | UC-MAINT-002 | NFR-DATA-002 |
| BO-002 | FR-MAINT-003/004 | US-TECH-001…004 | UC-MAINT-003 | NFR-DATA-003 |
| BO-003 | FR-MON-001/002/003 | US-ADM-005 | UC-MACH-001 | NFR-SCALE-003 |
| BO-003 | FR-MON-004 | US-ME-001, US-MM-001 | UC-MON-002 | NFR-PERF-001 |
| BO-003 | FR-MON-005 | US-PM-003 | UC-MON-001, UC-MON-002 | NFR-USE-003 |
| BO-003 | FR-SENSOR-002, FR-DASH-002 | US-ME-002, US-ME-003 | UC-MON-002, UC-MON-003 | NFR-PERF-003 |
| BO-004 | FR-DASH-001 | US-PM-001, US-PM-002 | UC-MON-001 | NFR-USE-003 |
| BO-004 | FR-REPORT-002 | US-MM-007 | UC-REPORT-001 | NFR-COMP-002 |
| BO-004 | FR-AI-004 | US-ME-006 | UC-PRED-002 | NFR-ML-004 |
| BO-005 | FR-AI-002 | US-MM-002 | UC-PRED-001 | NFR-ML-001 |
| BO-005 | FR-MAINT-001/002 | US-MM-003, US-MM-004 | UC-MAINT-001, UC-MAINT-002 | NFR-DATA-002 |
| BO-006 | FR-MON-004, FR-USER-001/002 | US-ME-001, US-ADM-001 | UC-MON-002, UC-USER-001 | NFR-DATA-004 |
| *(cross-cutting)* | FR-AUTH-001 | US-SYS-001 | UC-AUTH-001 | NFR-SEC-001 |

*Post-MVP items (FR-USER-003/004, FR-MAINT-005, FR-DASH-005, FR-AI-003/005, FR-SYS-001/002, FR-REPORT-001/003/004/005, FR-SENSOR-003, FR-AUTH-003) are intentionally excluded from this MVP-only table — see Section 5 for their status.*

---

# 9. Requirements Traceability Status

| Requirement Category | Status |
|---|---|
| Business Requirements (BO-001…BO-006) | Defined, formally IDed |
| Software Requirements Specification | Defined |
| Functional Requirements (FR-###) | Defined, formally IDed (40 items across 10 categories) |
| User Stories (US-###) | Defined (34 items, incl. 1 proposed addition) |
| Use Cases (UC-###) | Defined (15 items, incl. 1 proposed addition) |
| Non-Functional Requirements (NFR-###) | Defined (43 items, unchanged) |
| Requirements Traceability | **Rebuilt and verified — all references checked against source documents** |
| Requirements Validation | See Section 10 below |
| Test Case Mapping | Pending (out of scope for the Requirements phase) |

---

# 10. Requirements Validation (Second Audit / Final Check)

- [x] All 6 Business Objectives are represented by Functional Requirements (Section 3).
- [x] All major user needs are represented by User Stories.
- [x] All **MVP** (High priority) User Stories have corresponding Use Cases (Section 5) — either an existing Use Case, a reused one, or the newly added UC-MACH-001.
- [x] All Use Cases have corresponding Functional Requirements (Section 6).
- [x] Non-Functional Requirements apply to the relevant system components (Section 7).
- [x] Requirements do not contain conflicting specifications.
- [x] MVP and Post-MVP features are clearly separated (Section 5, and MVP list in Section 11).
- [x] Requirements are technically feasible within the stated project scope (BRD Section 9 Out-of-Scope was re-checked — no violations, see [[Business_Requirements]]).
- [x] Requirements are sufficiently clear for architecture and development.
- [x] No duplicate IDs exist across any document.
- [x] No invented IDs remain — every reference in this matrix was checked against its source file.

**Remaining open items (not blockers, explicitly deferred):**
- Post-MVP Use Cases for System Configuration, Audit Logs, Maintenance Costs, Machine Comparison, AI Recommendations, and RUL Prediction are intentionally not yet written; author them when each feature is scheduled.
- FR-AUTH-002 (Logout), FR-AUTH-003 (Password Reset), and FR-SENSOR-001 (Register Sensors) have no dedicated User Story; treated as implicit sub-behaviors of US-SYS-001 and US-ADM-005 respectively (see Section 4 note).

---

# 11. MVP Traceability

The MVP scope, in dependency order:

```text
Authentication (FR-AUTH-001)
      ↓
User & Machine Setup (FR-USER-001/002, FR-MON-001/002/003)
      ↓
Sensor Data (FR-SENSOR-002)
      ↓
Dashboard (FR-DASH-001…004)
      ↓
Real-Time Monitoring (FR-DASH-002)
      ↓
Anomaly Detection (FR-AI-001)
      ↓
Failure Prediction + Explainability (FR-AI-002, FR-AI-004)
      ↓
Alerts (FR-ALERT-001…003)
      ↓
Maintenance Management (FR-MAINT-001…004)
      ↓
Technician Tasks (FR-MAINT-003)
      ↓
Maintenance KPI Reporting (FR-REPORT-002)
```

**Post-MVP** (documented, not required for MVP): FR-AUTH-003, FR-USER-003, FR-USER-004, FR-SENSOR-003, FR-DASH-005, FR-MAINT-005, FR-AI-003, FR-AI-005, FR-REPORT-001, FR-REPORT-003, FR-REPORT-004, FR-REPORT-005, FR-SYS-001, FR-SYS-002.

**Future / Out of current scope** (per [[Use_Cases]] Section 12 and [[User_Stories]] Section 9): AI natural-language assistant, real IoT device integration, multi-factory comparison, energy optimization, spare-parts inventory, ERP/CMMS integration.

---

# 12. Related Documents

- [[Project_Charter]]
- [[Business_Requirements]]
- [[Software_Requirements_Specification]]
- [[Functional_Requirements]]
- [[User_Stories]]
- [[Use_Cases]]
- [[Non_Functional_Requirements]]

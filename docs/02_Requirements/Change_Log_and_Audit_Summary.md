# FactoryPulse AI — Requirements Fix: Change Log & Audit Summary

This companion document explains **what was wrong, what was changed, and why**, for the corrected files in this folder. Read this alongside the corrected files — it is not meant to replace them.

---

# 1. Executive Summary

The v1.0 documentation set was well-written at the prose level but had a broken traceability layer: `Business_Requirements.md` and `Functional_Requirements.md` had no formal IDs, and the `Requirements_Traceability_Matrix.md` invented roughly 50 IDs to compensate (fabricated `BR-###`, fabricated `FR-###`, and 17 `UC-###` codes for Use Cases that were never written). Two references pointed to the wrong thing entirely (`UC-ANOM-001` instead of `UC-AI-001`, and `US-PM-003` mapped to the wrong Use Case's content). Three User Stories (Maintenance Costs, Search & Filtering, Notifications) and one Functional Requirement group (Machine CRUD) existed with no path to the other layers at all.

None of this was a scope problem — no out-of-scope feature (ERP, payroll, direct machine control, etc.) ever leaked into the documents. It was a **traceability** problem. The fix was: (1) add the missing ID schemes, (2) reuse existing Use Cases wherever their content already covered a User Story instead of inventing new ones, (3) add exactly one new User Story and one new Use Case where a real gap existed (machine registration), and (4) rebuild the RTM from verified references only.

**Status after this fix: READY FOR ARCHITECTURE**, with a short, explicitly-labeled list of Post-MVP items still needing Use Cases before they are built (not before Architecture starts).

---

# 2. Problems Found (from the original audit)

| # | File | Problem | Severity |
|---|---|---|---|
| 1 | Requirements_Traceability_Matrix.md | 6 `BR-###` IDs referenced, none exist anywhere | Critical |
| 2 | Requirements_Traceability_Matrix.md | ~29 `FR-###` IDs referenced, none exist anywhere | Critical |
| 3 | Requirements_Traceability_Matrix.md | 17 `UC-###` IDs referenced that were never written in Use_Cases.md | Critical |
| 4 | Requirements_Traceability_Matrix.md | `UC-ANOM-001` used instead of the real `UC-AI-001` | Critical |
| 5 | Requirements_Traceability_Matrix.md | `US-PM-003` mapped to `UC-MON-003`, whose actual content is unrelated (real-time monitoring, not availability) | Critical |
| 6 | Use_Cases.md | `UC-ALERT-002` (Resolve Alert) written but never linked from any User Story or the RTM | Major |
| 7 | User_Stories.md / Functional_Requirements.md | Maintenance Costs, Search & Filtering, Notifications each existed only as a single User Story, with no FR or UC | Major |
| 8 | Functional_Requirements.md / User_Stories.md | Machine Create/Update/Delete existed as FR bullets with no User Story or Use Case | Major |
| 9 | Functional_Requirements.md | Formal IDs did not exist at all | Major (root cause of #1–5) |
| 10 | Business_Requirements.md | Formal IDs did not exist at all | Major (root cause of #1) |
| 11 | Software_Requirements_Specification.md | "Operations Manager" stakeholder appears only here, nowhere else | Minor |
| 12 | Software_Requirements_Specification.md | Section 3 used generic role names inconsistent with the rest of the project | Minor |
| 13 | Functional_Requirements.md | Machine Risk Scoring and Explainable AI (both BRD in-scope) had no explicit FR bullet | Minor |
| 14 | Functional_Requirements.md | Remaining Useful Life Prediction existed only here, with no BRD/US/UC support | Major (AI/ML consistency) |

---

# 3. Changes Made

## Business_Requirements.md
- Added formal `BO-001`…`BO-006` IDs to Section 4's six objectives (the user had already appended a candidate `BO-###` list at the bottom of the file — this was adopted and integrated into the section headers rather than left as a disconnected list at the end).
- Added a short note under Section 9 (Out of Scope) confirming the audit found no scope violations.
- Added a clarifying note under Section 14 distinguishing "maintenance cost optimization" (a future, AI-driven capability) from basic cost tracking (now Post-MVP, see FR-MAINT-005).
- **No objective wording was changed. No content was deleted.**

## Software_Requirements_Specification.md
- Removed "Operations Manager" from Section 2 (it appeared nowhere else in the project and had no supporting User Story or Use Case).
- Rewrote Section 3 to use the same role names as the BRD and User Stories, instead of generic labels.
- Added references from Section 1.3 objectives back to their `BO-###` IDs.

## Functional_Requirements.md
- Added a formal `FR-[CATEGORY]-[NUMBER]` ID to every existing bullet (40 IDs total).
- Split "User Management" out from "Authentication" as its own category (mirrors the structure already used in Use_Cases.md).
- Added a new "System / Cross-Cutting" category for Search/Filtering and Notifications.
- Added 10 items marked **[PROPOSED ADDITION]** or **[NEW]**, each explained inline, to close specific gaps found in the audit: Manage User Accounts, System Configuration, Audit Logs, Monitor Machine Availability, Machine Comparison, Maintenance Costs, Maintenance KPI Reporting, Performance Trend Reporting, Search and Filtering, Notifications.
- Added an explicit Explainable AI FR bullet (FR-AI-004) and a note clarifying that Machine Risk Scoring is delivered as part of Failure Prediction (FR-AI-002), not a separate item.
- Made and explained an explicit decision on Remaining Useful Life Prediction: kept, but marked Post-MVP (FR-AI-005), with the reasoning documented inline.
- Tagged every requirement MVP or Post-MVP, derived directly from the priority of its related User Story.
- **No original bullet was deleted or reworded.**

## User_Stories.md
- Added one new story, **US-ADM-005 (PROPOSED ADDITION)** — Machine Registration — with an inline explanation of why it was needed.
- **No existing story was changed, reworded, or removed.**

## Use_Cases.md
- Added one new Use Case, **UC-MACH-001 (PROPOSED ADDITION)** — Register and Manage Machines — to support US-ADM-005 and the pre-existing FR-MON-001/002/003.
- Added Technician as a supporting actor on UC-MON-002, so it correctly serves US-TECH-005 (reviewing maintenance history before an intervention) without creating a duplicate Use Case.
- Added a "Related Functional Requirement / Related User Story" line under each existing Use Case for direct traceability.
- Documented, in the Use Case text itself, which Use Cases are intentionally reused across multiple User Stories (UC-MON-002, UC-MAINT-003, UC-REPORT-001, UC-USER-001) instead of being duplicated.
- **No existing Use Case flow was changed.**

## Requirements_Traceability_Matrix.md
- Fully rebuilt. Every `BO`, `FR`, `US`, `UC`, and `NFR` reference was re-derived from the corrected source files. No fabricated ID remains.
- Restructured around the chain Business Objective → Functional Requirement → User Story → Use Case → NFR, with a dedicated table for each link, plus an end-to-end MVP-scope table.
- Explicitly marks the small number of Post-MVP items that still have no Use Case as "To be defined when scheduled," rather than inventing placeholder Use Cases for them.

## Non_Functional_Requirements.md and Project_Charter.md
- **Not modified.** The audit found no ID errors, contradictions, or scope problems in either file. Re-issuing them unchanged would only introduce unnecessary diff noise in your GitHub history — they are unchanged from your v1.0 upload.

---

# 4. ID Strategy (final)

| Layer | ID Format | Example | Count |
|---|---|---|---|
| Business Objective | `BO-###` | BO-001 | 6 |
| Functional Requirement | `FR-[CATEGORY]-###` | FR-AI-002 | 40 |
| User Story | `US-[ROLE]-###` (unchanged, already existed) | US-ME-004 | 34 |
| Use Case | `UC-[AREA]-###` (unchanged, already existed) | UC-MAINT-003 | 15 |
| Non-Functional Requirement | `NFR-[AREA]-###` (unchanged, already existed) | NFR-SEC-001 | 43 |

**Why `BO` instead of `BR`:** the BRD is structured around *objectives* (Section 4, "Business Objectives"), not discrete atomic requirement statements — `BO` (Business Objective) matches what the document actually contains, and matches the ID prefix the user had already started using in the uploaded file.

**Why `FR-MON` for Machine Management:** kept consistent with the pre-existing `UC-MON-###` naming in Use_Cases.md, since these Functional Requirements are fulfilled by the same "Monitoring" Use Cases.

**Why some User Stories map to a reused Use Case instead of a new one:** several existing Use Cases already describe, step-by-step, functionality that a different User Story also needed (e.g., UC-MAINT-003's steps 1–3 are literally "technician opens assigned tasks → selects a task → reviews details" — exactly US-TECH-001 and US-TECH-002). Creating a new Use Case for each would just duplicate the same flow under a different name. Reuse is called out explicitly everywhere it happens, so it's an intentional documented decision, not a hidden shortcut.

---

# 5. AI/ML Consistency — Final Positions

| Capability | Business | SRS | Functional | User Story | Use Case | NFR | MVP Status |
|---|---|---|---|---|---|---|---|
| Anomaly Detection | ✅ 8.1 | ✅ | FR-AI-001 | US-ME-004 | UC-AI-001 | NFR-ML-001 | MVP |
| Failure Prediction | ✅ 8.1 | ✅ | FR-AI-002 | US-MM-002, US-ME-005 | UC-PRED-001 | NFR-ML-001 | MVP |
| Machine Risk Scoring | ✅ 8.1 | — | *(delivered inside FR-AI-002, not separate — see note)* | *(implicit)* | UC-PRED-001 (risk level, step 7) | NFR-ML-001 | MVP |
| Explainable AI | ✅ 8.1 | — | FR-AI-004 | US-ME-006 | UC-PRED-002 | NFR-ML-004 | MVP |
| AI Recommendations | — | — | FR-AI-003 | US-ME-008 | *To be defined (Post-MVP)* | — | Post-MVP |
| Remaining Useful Life (RUL) Prediction | ❌ not in BRD | — | FR-AI-005 | *(none yet)* | *(none yet)* | NFR-ML-001 (regression metrics already anticipate it) | **Post-MVP — decision explained in Functional_Requirements.md** |

---

# 6. Files Modified

| File | Modified? |
|---|---|
| Project_Charter.md | No — unchanged |
| Business_Requirements.md | Yes |
| Software_Requirements_Specification.md | Yes |
| Functional_Requirements.md | Yes |
| User_Stories.md | Yes |
| Use_Cases.md | Yes |
| Non_Functional_Requirements.md | No — unchanged |
| Requirements_Traceability_Matrix.md | Yes — full rebuild |

---

# 7. Final Validation (second pass)

- Every `BO`, `FR`, `US`, `UC` reference in the rebuilt RTM was checked against its source file — none are invented.
- Every MVP (High-priority) User Story now has a Use Case, either existing, reused, or newly added.
- No duplicate IDs exist anywhere in the set.
- No out-of-scope feature was introduced.
- MVP vs. Post-MVP vs. Future is explicit at every layer (FR table, US priority, RTM Section 11).

## Final Requirements Phase Readiness Status

# **READY FOR ARCHITECTURE**

The one condition attached to this status: the small set of Post-MVP items that still have "Use Case: to be defined" (System Configuration, Audit Logs, Maintenance Costs, Machine Comparison, AI Recommendations, RUL Prediction) should get a real Use Case authored before *those specific features* enter a sprint — but none of them block starting Architecture on the MVP scope, since the MVP scope itself is now fully and validly traceable end-to-end.

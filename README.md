# FactoryPulse AI

> An industrial operations intelligence platform for monitoring production performance, machine reliability, downtime, alerts, and factory health.

## Table of Contents

- [1. What is FactoryPulse AI?](#1-what-is-factorypulse-ai)
- [2. The Problem It Solves](#2-the-problem-it-solves)
- [3. Product Vision](#3-product-vision)
- [4. Main Concepts](#4-main-concepts)
  - [Production Lines](#production-lines)
  - [Production Runs](#production-runs)
  - [OEE](#oee)
  - [Downtime](#downtime)
  - [Operational Trends](#operational-trends)
  - [Machine Reliability](#machine-reliability)
  - [Alerts](#alerts)
  - [Authentication and RBAC](#authentication-and-rbac)
- [5. Current Product Structure](#5-current-product-structure)
- [6. Architecture](#6-architecture)
- [7. Repository Structure](#7-repository-structure)
- [8. Backend](#8-backend)
  - [API layer](#api-layer)
  - [Schemas](#schemas)
  - [Services](#services)
  - [Models](#models)
  - [Database](#database)
  - [Business logic](#business-logic)
- [9. Frontend](#9-frontend)
  - [Routing](#routing)
  - [Pages](#pages)
  - [Components](#components)
  - [Services](#services-frontend)
  - [Types](#types)
  - [State and data loading](#state-and-data-loading)
- [10. Dashboard / Overview](#10-dashboard--overview)
- [11. Production Workspace](#11-production-workspace)
- [12. Machines Workspace](#12-machines-workspace)
- [13. Alerts and Notifications](#13-alerts-and-notifications)
- [14. Data Flow](#14-data-flow)
- [15. Error Handling](#15-error-handling)
- [16. Testing](#16-testing)
- [17. Development Workflow](#17-development-workflow)
- [18. Git Workflow](#18-git-workflow)
- [19. How to Understand the Project Quickly](#19-how-to-understand-the-project-quickly)
- [20. Current State and Roadmap](#20-current-state-and-roadmap)
- [21. Design Principles](#21-design-principles)
- [22. Glossary](#22-glossary)

---

# 1. What is FactoryPulse AI?

FactoryPulse AI is an industrial monitoring and operational intelligence platform designed around the idea that a factory should not only collect production data, but also turn that data into information that operators, technicians, managers, and engineers can use.

The project combines:

- production data
- machine data
- downtime events
- quality and quantity information
- alerts
- reliability metrics
- OEE calculations
- operational comparisons
- role-based access control
- a web-based operations interface

The platform is intended to answer questions such as:

- How is the factory performing right now?
- Which production line is underperforming?
- Why is a line losing production time?
- Which machine is contributing the most downtime?
- Is reliability improving or getting worse?
- Which production runs produced good or rejected quantities?
- Which alerts require attention?
- Is the current period better or worse than the previous one?

FactoryPulse is therefore more than a CRUD application. The important part of the system is the layer that turns raw records into operational metrics and decisions.

---

# 2. The Problem It Solves

A production environment generates many different kinds of information:

- production runs
- machine states
- downtime events
- quantities produced
- rejected quantities
- failures
- maintenance activity
- alerts

Without an integrated system, this information is often distributed across different tools or logs. That makes it difficult to understand the overall state of the factory.

FactoryPulse tries to create one coherent operational model.

Instead of looking at a single record such as:

```text
Machine M-101 had a downtime event of 25 minutes.
```

FactoryPulse tries to answer the next-level question:

```text
How did that downtime affect the production line?
How does that line compare with the previous period?
Is the same machine failing repeatedly?
Is the machine's MTTR increasing?
Is factory OEE being affected?
```

This progression from **raw event -> metric -> trend -> operational insight** is one of the central ideas of the project.

---

# 3. Product Vision

The long-term vision is to make FactoryPulse AI a reusable industrial intelligence platform with several layers.

## Layer 1 — Data

Store the core operational entities:

- areas
- production lines
- machines
- production runs
- downtime events
- alerts
- users

## Layer 2 — Analytics

Calculate:

- OEE
- availability
- performance
- quality
- downtime
- failure counts
- MTTR
- MTBF
- operating exposure
- production quantities

## Layer 3 — Intelligence

Combine metrics to identify:

- high-priority machines
- operational impact
- worsening reliability
- downtime concentration
- current-vs-previous changes

## Layer 4 — Interface

Present the information through:

- Overview
- Production
- Machines
- Alerts
- Maintenance
- notifications
- role-aware workflows

## Layer 5 — AI / predictive capabilities

The broader project can later extend this platform with the type of AI work already associated with FactoryPulse's direction:

- anomaly detection
- production forecasting
- predictive maintenance
- root-cause assistance
- intelligent alerts
- RAG-based operational knowledge

The important architectural principle is that AI should sit on top of reliable operational data rather than replace the operational foundation.

---

# 4. Main Concepts

## Production Lines

A production line represents an operational manufacturing line inside a factory.

A line has:

- `id`
- `area_id`
- `name`
- `code`
- `description`
- `created_at`

Production lines are the main scope used by the Production workspace.

Most production analytics can be interpreted at line level:

```text
Factory
  -> Production Line
       -> Production Runs
       -> Machines
       -> Downtime
       -> OEE
       -> Trends
```

---

## Production Runs

A production run represents one period of production activity on a line.

Important fields include:

- `id`
- `production_line_id`
- `started_at`
- `ended_at`
- `status`
- `target_quantity`
- `total_quantity`
- `good_quantity`
- `reject_quantity`
- `ideal_cycle_time_seconds`
- `created_at`

The supported run statuses are:

- `running`
- `completed`
- `cancelled`

The backend enforces consistency rules. For example:

- a running run cannot already have `ended_at`
- a completed or cancelled run must have `ended_at`
- `ended_at` cannot precede `started_at`
- good + reject quantity cannot exceed total quantity

Production runs are important because many analytics are ultimately derived from them.

---

## OEE

OEE means **Overall Equipment Effectiveness**.

FactoryPulse uses the standard conceptual decomposition:

```text
OEE = Availability × Performance × Quality
```

### Availability

Availability describes how much planned production time was actually available for operation.

Conceptually:

```text
Availability = Operating Time / Planned Production Time
```

### Performance

Performance describes how efficiently the equipment produced relative to its ideal production rate.

### Quality

Quality describes the share of production that meets the quality requirement.

```text
Quality = Good Quantity / Total Quantity
```

### Why OEE matters

OEE allows FactoryPulse to move beyond isolated numbers such as downtime or quantity.

A line can produce a large amount while still having poor OEE. Another line can have relatively few failures but still perform poorly because of long planned stops, slow cycles, or quality losses.

That is why OEE is treated as a combined operational metric rather than a simple production count.

FactoryPulse calculates OEE at multiple scopes:

- production-line level
- production-run level
- factory/dashboard level

The implementation should always reuse the established analytics logic instead of duplicating formulas inside UI code.

---

## Downtime

Downtime represents time during which production is not operating normally.

FactoryPulse distinguishes:

- recorded downtime
- planned downtime
- unplanned downtime

Downtime analytics can also be grouped by:

- reason
- machine

Reason-level records include:

- reason
- event count
- duration
- percentage

Machine-level records include:

- machine ID
- event count
- duration
- percentage

The purpose is not simply to display hours. The purpose is to reveal concentration:

```text
Total downtime
   -> Reason A: 52%
   -> Reason B: 24%
   -> Reason C: 14%
   -> Other: 10%
```

and:

```text
Total downtime
   -> Machine A: 48%
   -> Machine B: 32%
   -> Machine C: 20%
```

This makes downtime actionable.

---

## Operational Trends

Operational trends compare a **current period** with the **previous period**.

A trend metric contains:

- `current_value`
- `previous_value`
- `delta`
- `direction`

The direction can be:

- `improved`
- `worsened`
- `unchanged`
- `not_comparable`

Line-level trends currently cover:

- OEE
- Availability
- Performance
- Quality
- recorded downtime
- total failure count

Machine-level trends additionally cover:

- downtime
- failures
- MTTR
- MTBF

This distinction is important because a trend is not the same thing as a raw value.

For example:

```text
Current OEE:   72%
Previous OEE:  66%
Delta:         +6 pp
Direction:     improved
```

The UI should use the backend's `direction` instead of trying to infer whether a value is good or bad on its own.

---

## Machine Reliability

Machine reliability focuses on repeated machine behavior over a selected period.

FactoryPulse tracks:

- failure count
- total failure downtime
- MTTR
- operating exposure
- MTBF

### MTTR

Mean Time To Repair describes the average time associated with resolving failures.

In general:

```text
MTTR = Total Failure Downtime / Failure Count
```

Lower MTTR generally means failures are being resolved more quickly.

### MTBF

Mean Time Between Failures describes the amount of operating exposure between failures.

In the platform, MTBF is based on valid operating exposure rather than simply dividing an arbitrary calendar period by the failure count.

The implementation already has tests protecting the use of total valid exposure in fleet MTBF calculations.

---

## Alerts

Alerts represent operational conditions that deserve attention.

An alert contains information such as:

- severity
- title
- message
- created time
- machine context
- open/active state

Recent alerts are used by the Overview and notification system.

Severity is normalized into UI categories such as:

- critical
- high
- informational

The Notification Center now consumes real dashboard alert data rather than hardcoded demo notifications.

---

## Authentication and RBAC

FactoryPulse has authenticated API access and role-based authorization.

The exact permissions are controlled by the backend role system.

The general distinction is:

### Read-oriented roles

Can access operational information such as:

- production lines
- machines
- production runs
- analytics
- alerts

### Asset-write roles

Can perform actions such as:

- creating/updating production runs
- creating/updating machines

### Management roles

Have broader administrative operations such as management of production-line or machine assets.

The frontend should never be treated as the security boundary. Authorization is enforced by the backend.

---

# 5. Current Product Structure

The frontend is organized around operational workspaces.

## Overview

The Overview is the factory-level dashboard.

Its purpose is to answer:

> “What is happening across the factory right now?”

It includes:

- overall OEE
- availability
- active alerts
- fleet MTBF
- production-line summaries
- machine health
- recent alerts
- needs-attention ranking
- efficiency trend

The Overview should stay high-level. Detailed production-line analytics belong in Production.

## Production

Production answers:

> “What is happening on this production line, and why?”

The current workspace includes:

- production-line selector
- line-level OEE
- line downtime analytics
- operational trends
- production runs
- per-run OEE
- selectable trend periods

## Machines

The Machines workspace is the next major module.

The backend already provides machine inventory and machine reliability APIs. The frontend implementation should build on those existing contracts rather than creating duplicate data models.

## Alerts

Alerts will provide a dedicated operational view of active and historical alert information.

## Maintenance

Maintenance is intended to connect operational failures with maintenance workflows and records.

---

# 6. Architecture

FactoryPulse follows a layered architecture.

```text
┌──────────────────────────────────────────────┐
│                  Frontend                    │
│ React + TypeScript + Vite                    │
│ Pages / Components / Services / Types        │
└──────────────────────┬───────────────────────┘
                       │ HTTP/JSON
                       ▼
┌──────────────────────────────────────────────┐
│                   FastAPI                    │
│ API endpoints / authentication / RBAC        │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│                 Service Layer                │
│ business rules / analytics / aggregation     │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│              SQLAlchemy Models               │
│ ORM representation of operational data       │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│                    Database                  │
└──────────────────────────────────────────────┘
```

The important rule is:

```text
UI should display business data.
UI should not re-implement business analytics.
```

For example, the React frontend should not calculate factory OEE by itself when the backend already exposes a validated OEE calculation.

---

# 7. Repository Structure

The repository is organized approximately like this:

```text
FactoryPulse-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── production/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── tests/
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── styles/
│   └── ...
│
├── docs/
│   └── ...
│
└── README.md
```

---

# 8. Backend

## API layer

The API layer contains FastAPI routers.

Examples include:

```text
backend/app/api/
├── dashboard.py
├── machines.py
├── production_lines.py
├── production_runs.py
└── ...
```

The API layer is responsible for:

- defining routes
- validating request/response models
- enforcing authentication and roles
- calling services
- translating service errors into HTTP errors

It should not contain large amounts of business logic.

### Example

A production run endpoint roughly follows:

```text
HTTP request
    ↓
FastAPI route
    ↓
role check
    ↓
service
    ↓
database
    ↓
response schema
    ↓
JSON response
```

---

## Schemas

Schemas describe the public API contract.

Examples:

```text
backend/app/schemas/
├── machine.py
├── production_line.py
├── production_run.py
├── downtime_analytics.py
├── operational_trends.py
└── oee.py
```

Pydantic models are used to validate and structure data.

Schemas are especially important because they create a stable boundary between internal database objects and external API responses.

---

## Services

Services hold reusable business operations.

Examples:

```text
backend/app/services/
├── machine_service.py
├── production_run_service.py
├── production_analytics_service.py
├── downtime_analytics_service.py
├── operational_trends_service.py
├── machine_reliability_service.py
└── dashboard_service.py
```

A service should answer questions like:

- How are production runs retrieved?
- How is OEE calculated?
- How is downtime aggregated?
- How is machine reliability calculated?
- How is factory attention priority determined?

This keeps analytics logic reusable by multiple API endpoints.

---

## Models

Models represent database entities through SQLAlchemy ORM.

Important operational models include:

- User
- Area
- ProductionLine
- Machine
- ProductionRun
- DowntimeEvent
- Alert

Relationships connect these entities.

For example:

```text
Area
 ├── Production Lines
 │      ├── Production Runs
 │      └── Machines
 │
 └── Machines
```

---

## Database

The database is the source of operational truth.

A fundamental principle of the project is:

```text
Do not manufacture data in the UI to make the dashboard look populated.
```

If the database contains no completed runs, the UI should show an empty state instead of fake OEE or downtime values.

This is particularly important during development because the demonstration database may contain only a small amount of data.

---

## Business logic

The analytics layer is one of the most important parts of the backend.

A simplified dependency chain looks like:

```text
ProductionRun
    ↓
OEE calculations
    ↓
Line analytics
    ↓
Factory aggregation
    ↓
Dashboard / Trends / Operational Intelligence
```

Business calculations should therefore be centralized.

If an OEE formula changes, we should change it in the analytics service rather than in several frontend components.

---

# 9. Frontend

The frontend is built as an operations interface rather than a generic admin dashboard.

## Routing

Routes map operational concepts to pages.

Conceptually:

```text
/overview
/production
/machines
/alerts
/maintenance
```

The dashboard shell provides shared navigation, authentication context, command palette, and notifications.

---

## Pages

Pages represent major user workflows.

Examples:

```text
frontend/src/pages/
├── OverviewPage.tsx
├── ProductionPage.tsx
└── ...
```

A page should orchestrate data and compose components. It should not become a giant replacement for the backend.

---

## Components

Components are reusable UI modules.

Dashboard examples include:

- recent alerts panel
- machine health panel
- needs attention panel
- production line panel
- notification center
- command palette

The goal is to keep repeated patterns out of page-level code.

---

## Services

Frontend services are the HTTP boundary.

Examples:

```text
frontend/src/services/
├── api.ts
├── dashboard.ts
├── production.ts
├── machines.ts
└── ...
```

The page should call a service function such as:

```ts
getProductionLineOEE(lineId)
```

rather than manually constructing fetch requests throughout the component.

This keeps networking consistent.

---

## Types

Frontend types mirror API contracts.

Examples:

```text
frontend/src/types/
├── dashboard.ts
├── production.ts
├── machine.ts
└── ...
```

The frontend should not guess fields.

If the backend says:

```json
{
  "production_line_id": 1,
  "oee": 0.72
}
```

the frontend type should reflect that contract accurately.

---

## State and data loading

The frontend generally follows this pattern:

```text
page mounted
    ↓
load data
    ↓
loading state
    ↓
success OR error/empty state
    ↓
render data
```

When selection changes:

```text
selected line changes
        ↓
new API request
        ↓
old request can be cancelled/ignored
        ↓
new data rendered
```

This prevents stale responses from overwriting newer selections.

---

# 10. Dashboard / Overview

The Overview is a factory-level aggregation layer.

It currently includes:

## Overall OEE

Factory-wide OEE based on completed production data.

## Availability

Factory-wide availability.

## Active Alerts

Number of currently active/open alerts.

## Fleet MTBF

Reliability metric aggregated across the fleet using valid operating exposure.

## Production Lines

A summary of factory lines.

## Machine Health

Aggregated machine health state based on current alert/reliability context.

## Recent Alerts

Recent operational alerts with machine context.

## Needs Attention

A cross-line ranking that recomputes machine priority across the factory rather than treating each line's local #1 machine as the global #1.

## Efficiency Trend

A historical/bucketed factory OEE trend calculated from actual completed runs.

The most important rule in the Overview is that empty data stays empty.

---

# 11. Production Workspace

The Production workspace is the detailed operational workspace for a selected production line.

## Production line selector

The user selects a line.

Once selected, the page loads line-specific analytics.

## OEE overview

Displays:

- OEE
- Availability
- Performance
- Quality
- completed runs
- total quantity
- good quantity
- operating time

## Downtime overview

Displays:

- recorded downtime
- planned downtime
- unplanned downtime
- downtime event count
- top downtime reasons
- machine impact

## Operational Trends

Displays current vs previous period for:

- OEE
- Availability
- Performance
- Quality
- Downtime
- Failures

and machine-level changes in:

- downtime
- failures
- MTTR
- MTBF

The trend window can be selected as:

- 7 days
- 30 days
- 90 days

## Production Runs

The page lists the runs belonging to the selected line.

Each run shows:

- run ID
- status
- started time
- ended time
- target quantity
- total quantity
- good quantity
- reject quantity
- duration

## Per-run OEE

A run can be expanded to load its individual OEE information.

This is deliberately loaded on demand rather than requesting OEE for every run in the list.

That avoids an N+1 request pattern.

---

# 12. Machines Workspace

The Machines module is the next major detailed workspace.

The backend already supports machine inventory and reliability.

## Machine inventory

A machine has:

- name
- code
- area
- production line
- location
- status
- creation time

## Machine reliability

The backend provides:

- failure count
- total failure downtime
- MTTR
- operating exposure
- MTBF

The long-term Machines workspace should connect machine identity with these reliability metrics and operational context.

---

# 13. Alerts and Notifications

Alerts exist at two related levels.

## Dashboard alert data

The Overview provides real recent/open alert data.

## Notification Center

The shell displays the same live alert information rather than using hardcoded demonstration notifications.

This is important because it means the notification system is now part of the operational data flow:

```text
Database alerts
    ↓
Dashboard API
    ↓
DashboardLayout
    ↓
NotificationCenter
```

The unread count is derived from actual current notification state rather than a hardcoded number.

---

# 14. Data Flow

A typical production workflow looks like this:

```text
DATABASE
   ↓
SQLAlchemy ORM
   ↓
SERVICE / ANALYTICS LAYER
   ↓
FASTAPI ROUTE
   ↓
JSON RESPONSE
   ↓
FRONTEND SERVICE
   ↓
REACT STATE
   ↓
COMPONENT
   ↓
USER
```

### Example: OEE

```text
ProductionRun records
        ↓
production analytics service
        ↓
OEE calculation
        ↓
Production Line OEE endpoint
        ↓
frontend/src/services/production.ts
        ↓
ProductionPage.tsx
        ↓
OEE cards
```

### Example: notifications

```text
Open alerts
        ↓
Dashboard overview API
        ↓
DashboardLayout
        ↓
NotificationCenter
        ↓
User notification drawer
```

---

# 15. Error Handling

FactoryPulse distinguishes between at least three states:

## Loading

The request is still running.

Example:

```text
Loading line performance...
```

## Empty / not computable

The API responded successfully at the HTTP level but there is not enough operational data to calculate the requested metric.

Example:

```text
No recorded downtime for this line.
```

or:

```text
A trend needs completed runs in both the current
and the preceding period.
```

This should not be displayed as a generic failure.

## Actual error

Something really failed:

- network failure
- authentication problem
- server error
- unexpected backend response

The frontend uses `ApiError` and the dashboard panels distinguish expected empty analytics states from actual errors.

The shared API client also understands FastAPI validation error structures so users receive useful validation messages instead of only a status code.

---

# 16. Testing

The backend uses pytest-based tests.

Dashboard tests cover areas such as:

- access by role
- authentication requirements
- invalid dashboard periods
- factory aggregation
- MTBF calculation
- machine health
- recent alerts
- needs-attention ranking
- efficiency trend behavior

Tests are especially important for analytics because a visually correct dashboard can still contain mathematically incorrect values.

For frontend changes, the minimum validation currently used throughout development is:

```bash
npm run lint
npm run build
```

For backend changes:

```bash
python -m pytest -q
```

Targeted test files can be run when iterating on one module.

---

# 17. Development Workflow

## Backend

From:

```text
backend/
```

activate the virtual environment and run the backend using the project's configured development command.

For tests:

```bash
python -m pytest -q
```

## Frontend

From:

```text
frontend/
```

install dependencies if needed and start the Vite development server using the project's configured npm command.

Before committing frontend work:

```bash
npm run lint
npm run build
```

## API documentation

The FastAPI application exposes interactive API documentation in development, normally through `/docs`.

This is useful for:

- checking endpoint paths
- inspecting schemas
- executing authenticated requests
- verifying backend responses before implementing frontend code

---

# 18. Git Workflow

FactoryPulse development should keep commits focused.

Good examples:

```text
feat(production): add production run analytics
feat(production): add per-run OEE details
feat(dashboard): connect live operational attention
fix(auth): synchronize expired sessions
```

Avoid:

```text
update stuff
changes
fix
work
```

Before a commit:

```bash
git diff --check
git status
```

Then stage only the intended files.

Do not use `git add .` when the repository contains intentional untracked documentation or unrelated work.

This is particularly important for FactoryPulse because multiple workstreams can coexist:

- backend
- frontend
- documentation
- experiments

---

# 19. How to Understand the Project Quickly

If you are new to the repository, don't start by reading every file.

Use this order.

## Step 1 — understand the business model

Read about:

```text
Area
Production Line
Machine
Production Run
Downtime Event
Alert
```

Understand how they relate.

## Step 2 — read the backend schemas

Look at:

```text
backend/app/schemas/
```

Schemas tell you what the API considers valid.

## Step 3 — read the API routes

Look at:

```text
backend/app/api/
```

This tells you what the application exposes.

## Step 4 — read the services

Look at:

```text
backend/app/services/
backend/app/production/
```

This is where the important business logic lives.

## Step 5 — understand the frontend data layer

Look at:

```text
frontend/src/services/
frontend/src/types/
```

This shows how React communicates with the backend.

## Step 6 — read the pages

Start with:

```text
frontend/src/pages/OverviewPage.tsx
frontend/src/pages/ProductionPage.tsx
```

## Step 7 — understand the dashboard shell

Read:

```text
frontend/src/layouts/DashboardLayout.tsx
frontend/src/components/shell/
```

This is where navigation, command palette, and notifications come together.

---

# 20. Current State and Roadmap

The project is intentionally being developed in operational slices.

## Completed / implemented

### Dashboard foundation

- authenticated dashboard
- RBAC-aware API access
- factory overview
- live KPIs
- recent alerts
- machine health
- needs-attention ranking
- efficiency trend

### Production workspace

- production line selection
- line OEE
- downtime analytics
- operational trends
- trend-period selector
- production runs
- per-run OEE

### Notification foundation

- real dashboard alerts
- notification center connected to live alert data
- dynamic active-alert count
- shared relative-time formatting

### API reliability

- improved validation error parsing
- explicit empty-data states
- cancellation/stale-response protection in frontend loading flows

## Next major module

### Machines

Planned functionality:

- machine inventory
- machine selection
- production-line context
- status
- reliability metrics
- MTTR
- MTBF
- failure history/context

## Later modules

### Alerts

A dedicated alert management workspace.

### Maintenance

Maintenance workflows connected to machine and downtime data.

### AI / predictive layer

Potential future capabilities:

- anomaly detection
- predictive maintenance
- forecasting
- intelligent alert scoring
- root-cause assistance
- industrial knowledge retrieval

---

# 21. Design Principles

## 1. Backend owns business truth

The frontend displays analytics. It should not invent or duplicate core business formulas.

## 2. Empty data is not fake zero data

If there are no production runs, show an empty state.

Do not transform “no data” into `0% OEE` unless the business definition explicitly says that is correct.

## 3. API contracts must be explicit

Frontend types should mirror backend schemas.

## 4. Avoid N+1 requests

A list page should not automatically perform one additional request for every row unless there is a very strong reason.

The production-run OEE interaction is a good example: OEE is requested only when the user expands a specific run.

## 5. Preserve user context

Changing a production line should invalidate or replace line-specific data.

Old responses must not overwrite newly selected data.

## 6. Analytics should be reusable

The same OEE or reliability calculation should be reusable by:

- API endpoints
- dashboard aggregation
- production workspace
- future AI workflows

## 7. Operational UI should be honest

A dashboard should never look more complete than the underlying data actually is.

## 8. Small commits, clear history

Each milestone should be independently understandable and testable.

---

# 22. Glossary

| Term | Meaning |
|---|---|
| Area | Higher-level physical or organizational factory area |
| Production Line | Manufacturing line where production runs occur |
| Machine | Equipment associated with a factory area and optionally a production line |
| Production Run | A specific production execution interval |
| Downtime Event | A recorded interruption/loss of production time |
| OEE | Overall Equipment Effectiveness |
| Availability | Portion of planned production time that was operationally available |
| Performance | Production speed/effectiveness relative to the ideal rate |
| Quality | Share of production that is good/non-rejected |
| MTTR | Mean Time To Repair |
| MTBF | Mean Time Between Failures |
| Operational Trend | Current-period value compared with previous-period value |
| Alert | Operational event requiring attention |
| RBAC | Role-Based Access Control |
| N+1 Request Pattern | A design where one list request triggers another API request for every list item |
| Empty State | Explicit UI state indicating that there is no computable data |
| Panel Error | Actual failure while retrieving or processing data |

---

# Final Mental Model

If you remember only one thing about FactoryPulse AI, remember this pipeline:

```text
             FACTORY REALITY
                   │
                   ▼
        ┌─────────────────────┐
        │ Operational Records │
        │ runs / machines /   │
        │ downtime / alerts   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Analytics & Rules   │
        │ OEE / MTTR / MTBF  │
        │ downtime / trends  │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Operational         │
        │ Intelligence        │
        │ priorities / trends │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ FactoryPulse UI     │
        │ Overview /          │
        │ Production /        │
        │ Machines / Alerts   │
        └──────────┬──────────┘
                   │
                   ▼
             HUMAN DECISION
```

FactoryPulse AI exists to make the final step better: turning factory data into information that a human can understand, investigate, and act on.

---

## Project Status

This README describes the current architecture and implemented direction of FactoryPulse AI. As the project evolves, update this document whenever a new major module, API contract, analytics engine, or architectural pattern is introduced.

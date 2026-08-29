# Production and OEE

## Overview

FactoryPulse AI includes a production intelligence foundation for tracking production runs, downtime events, operational lifecycle integrity, and Overall Equipment Effectiveness (OEE).

The production architecture is centered around the existing industrial hierarchy:

```text
Organization
    ↓
Site
    ↓
Area
    ↓
ProductionLine
    ↓
Machine
```

Production information extends this hierarchy through:

```text
ProductionLine
    ↓
ProductionRun
    ↓
DowntimeEvent
        ↓
Machine (optional)
```

A `ProductionRun` represents a real production period on a production line.

A `DowntimeEvent` represents a planned or unplanned production interruption occurring during that run.

OEE is derived dynamically from these production facts rather than persisted as a database record.

---

## ProductionRun

The `ProductionRun` model represents a production period associated with a `ProductionLine`.

Main fields:

```text
id
production_line_id
started_at
ended_at
status
target_quantity
total_quantity
good_quantity
reject_quantity
ideal_cycle_time_seconds
created_at
```

The supported statuses are:

```text
running
completed
cancelled
```

### Production Quantities

Production runs can track:

```text
target_quantity
total_quantity
good_quantity
reject_quantity
```

All quantities must be non-negative.

The following rule is enforced:

```text
good_quantity + reject_quantity <= total_quantity
```

Equality is not required because some produced units may still be awaiting quality classification.

### Ideal Cycle Time

`ideal_cycle_time_seconds` represents the theoretical minimum time required to produce one unit under ideal operating conditions.

It must be positive when provided.

This value is required for OEE Performance calculation.

---

## ProductionRun Lifecycle

Production runs have controlled lifecycle semantics.

### Running

A running production run must satisfy:

```text
status = running
ended_at = NULL
```

While running, production quantities and other mutable production information may be updated.

### Completed

A completed production run requires:

```text
status = completed
ended_at != NULL
```

Once completed, the run becomes immutable.

### Cancelled

A cancelled production run also requires:

```text
status = cancelled
ended_at != NULL
```

Cancelled runs become immutable and are not considered valid sources for official OEE calculation.

### Terminal State Protection

The lifecycle is:

```text
running
   ├── update production data
   ├── complete
   └── cancel

completed
   └── immutable

cancelled
   └── immutable
```

Completed or cancelled production runs cannot later be modified.

---

## ProductionRun Final-State Validation

PATCH operations validate the complete resulting object rather than validating only individual changed fields.

For example, assume the current production state is:

```text
total_quantity = 100
good_quantity = 90
reject_quantity = 10
```

A PATCH request containing:

```json
{
  "total_quantity": 80
}
```

is rejected because the resulting state would become:

```text
good_quantity + reject_quantity = 100
total_quantity = 80
```

which violates:

```text
good_quantity + reject_quantity <= total_quantity
```

This protects production integrity across partial updates.

---

## DowntimeEvent

A `DowntimeEvent` represents a production interruption associated with a `ProductionRun`.

Main fields:

```text
id
production_run_id
machine_id
category
reason
started_at
ended_at
notes
created_at
```

The supported categories are:

```text
planned
unplanned
```

Examples of planned downtime:

```text
scheduled maintenance
cleaning
changeover
scheduled break
```

Examples of unplanned downtime:

```text
machine failure
electrical fault
material shortage
unexpected stoppage
```

The detailed cause remains flexible through the `reason` field.

---

## Machine Association

A downtime event may optionally reference a specific machine:

```text
machine_id = <Machine>
```

or represent a line-wide event:

```text
machine_id = NULL
```

When a machine is supplied, FactoryPulse validates that:

```text
Machine.production_line_id
==
ProductionRun.production_line_id
```

This prevents invalid relationships such as:

```text
ProductionRun → Line A
DowntimeEvent → Machine from Line B
```

A machine that is not assigned to a production line also cannot be attached to a line-specific ProductionRun.

---

## Downtime Lifecycle

Downtime events can initially be open:

```text
started_at = timestamp
ended_at = NULL
```

For example:

```text
10:00
Machine failure detected
↓
DowntimeEvent opened
```

When the interruption finishes:

```text
PATCH /downtime-events/{id}

ended_at = 10:23
```

The downtime becomes closed.

Once:

```text
ended_at != NULL
```

the downtime event becomes immutable.

The lifecycle is therefore:

```text
open downtime
      ↓
PATCH ended_at
      ↓
closed downtime
      ↓
immutable historical event
```

---

## Temporal Integrity

FactoryPulse validates that downtime events remain consistent with their ProductionRun.

A downtime event cannot start before its production run:

```text
Run:
08:00 ---------------- 16:00

Invalid downtime:
07:30 ----- 08:10
```

For an ended production run, downtime cannot extend beyond the production end:

```text
Run:
08:00 ---------------- 16:00

Invalid downtime:
15:50 ---------------- 16:10
```

A completed production run cannot contain an open downtime event.

Therefore:

```text
ProductionRun completion
        ↓
all DowntimeEvents must be closed
        ↓
all downtime timestamps must be <= run ended_at
        ↓
completion allowed
```

A ProductionRun cannot be completed or cancelled while any associated downtime event remains open.

---

## Production API

### Production Runs

Create:

```http
POST /production-runs
```

List:

```http
GET /production-runs
```

Read one:

```http
GET /production-runs/{production_run_id}
```

Update lifecycle and production values:

```http
PATCH /production-runs/{production_run_id}
```

Navigate through a production line:

```http
GET /production-lines/{production_line_id}/production-runs
```

### ProductionRun RBAC

Creation and updates use the FactoryPulse asset-write policy:

```text
Admin       ✅
Manager     ✅
Technician  ✅
Operator    ❌
```

Read operations are available to all authenticated roles.

---

## Downtime API

Create:

```http
POST /downtime-events
```

List:

```http
GET /downtime-events
```

Read one:

```http
GET /downtime-events/{downtime_event_id}
```

Close or update an open event:

```http
PATCH /downtime-events/{downtime_event_id}
```

Navigate through a ProductionRun:

```http
GET /production-runs/{production_run_id}/downtime-events
```

### Downtime RBAC

Downtime operational writes use the reading-write policy:

```text
Admin       ✅
Manager     ❌
Technician  ✅
Operator    ✅
```

Read operations are available to all authenticated roles.

---

# Overall Equipment Effectiveness

## OEE Architecture

OEE is intentionally not stored in a dedicated database table.

It is derived from production facts:

```text
ProductionRun
      +
DowntimeEvents
      +
Ideal Cycle Time
      +
Production Quantities
      ↓
Availability
Performance
Quality
      ↓
OEE
```

This avoids stale calculated records when underlying production data changes.

The pure calculation engine is implemented separately from database and API logic.

Architecture:

```text
PostgreSQL
    ↓
ProductionRun + DowntimeEvents
    ↓
OEE service adapter
    ↓
DowntimeWindow objects
    ↓
pure calculate_oee()
    ↓
OEEMetrics
    ↓
FastAPI response
```

The mathematical engine contains no SQLAlchemy or FastAPI dependencies.

---

## OEE Formula

Overall Equipment Effectiveness is calculated as:

```text
OEE
=
Availability
×
Performance
×
Quality
```

Values are represented internally as decimal ratios.

Example:

```text
Availability = 0.90
Performance  = 0.82
Quality      = 0.95
OEE          = 0.7011
```

A frontend may display those values as percentages:

```text
90%
82%
95%
70.11%
```

---

## Scheduled Time

Scheduled production time is:

```text
scheduled_time
=
ProductionRun.ended_at
-
ProductionRun.started_at
```

For an eight-hour run:

```text
08:00 → 16:00
```

the scheduled time is:

```text
28,800 seconds
```

---

## Planned Downtime

Planned downtime is excluded from the time during which production was expected to operate.

```text
planned_production_time
=
scheduled_time
-
planned_downtime
```

Example:

```text
Scheduled time:       8 hours
Planned downtime:     30 minutes
```

produces:

```text
Planned Production Time
=
7.5 hours
```

---

## Availability

Availability measures how much of planned production time the process actually operated.

```text
Availability
=
Operating Time
/
Planned Production Time
```

Operating time is:

```text
Operating Time
=
Planned Production Time
-
Unplanned Downtime
```

Example:

```text
Planned Production Time = 27,000 seconds
Unplanned Downtime      = 2,700 seconds
Operating Time          = 24,300 seconds
```

Therefore:

```text
Availability
=
24,300 / 27,000
=
0.90
```

---

## Performance

Performance compares actual production output against the theoretical maximum output during operating time.

```text
Performance
=
Ideal Cycle Time
×
Total Quantity
/
Operating Time
```

Example:

```text
Ideal Cycle Time = 20 seconds
Total Quantity   = 1000
Operating Time   = 24,300 seconds
```

Therefore:

```text
Performance
=
20 × 1000 / 24,300
```

FactoryPulse intentionally does not artificially cap Performance at `1.0`.

A value above 100% may reveal:

```text
incorrect ideal cycle time
incorrect production count
incorrect configuration
unexpected production behavior
```

Silently capping the metric could hide a data-quality or configuration problem.

---

## Quality

Quality measures the percentage of produced units classified as good.

```text
Quality
=
Good Quantity
/
Total Quantity
```

Example:

```text
Good Quantity  = 950
Total Quantity = 1000
```

Therefore:

```text
Quality = 0.95
```

When:

```text
total_quantity = 0
```

FactoryPulse returns:

```text
Quality = 0
Performance = 0
OEE = 0
```

---

## Downtime Interval Merging

Downtime durations are not calculated by simply summing every database row.

This is important because multiple machine events may overlap.

Example:

```text
Machine A:
10:00 -------- 10:30

Machine B:
       10:15 -------- 10:45
```

Naive summation would produce:

```text
30 + 30 = 60 minutes
```

which is incorrect for line-level elapsed downtime.

FactoryPulse merges overlapping intervals:

```text
10:00 ---------------- 10:45
```

giving:

```text
45 minutes
```

---

## Planned and Unplanned Downtime Overlap

FactoryPulse also prevents double-counting when planned and unplanned downtime overlap.

Example:

```text
Planned:
12:00 -------- 12:30

Unplanned:
       12:20 -------- 12:45
```

The overlap:

```text
12:20 → 12:30
```

is counted once.

Planned downtime takes priority because it is excluded from Planned Production Time.

The effective durations become:

```text
Planned downtime   = 30 minutes
Unplanned downtime = 15 minutes
```

---

## Downtime Boundary Handling

The pure OEE engine defensively clips downtime intervals to the ProductionRun boundaries.

For example:

```text
ProductionRun:
08:00 ---------------- 12:00

Downtime:
07:30 -------- 08:15
```

only:

```text
08:00 → 08:15
```

is considered.

The API/domain validation layer should normally prevent out-of-bound events from entering production data, but the OEE calculation engine remains defensive and mathematically safe.

---

## Open Downtime Protection

OEE cannot be calculated from an open downtime interval.

If:

```text
ended_at = NULL
```

the calculation engine rejects the input.

At the application level, completed ProductionRuns cannot contain open downtime events, so valid completed production data should already satisfy this requirement.

---

## OEE Eligibility

Official ProductionRun OEE is currently available only when:

```text
status = completed
```

Running runs are rejected because production facts are still changing.

Cancelled runs are rejected because they do not represent a normal completed production cycle.

Therefore:

```text
completed → OEE available ✅
running   → OEE rejected ❌
cancelled → OEE rejected ❌
```

---

## OEE API

OEE can be retrieved through:

```http
GET /production-runs/{production_run_id}/oee
```

Example response:

```json
{
  "production_run_id": 12,
  "scheduled_time_seconds": 28800,
  "planned_downtime_seconds": 1800,
  "planned_production_time_seconds": 27000,
  "unplanned_downtime_seconds": 2700,
  "operating_time_seconds": 24300,
  "availability": 0.9,
  "performance": 0.823045267489712,
  "quality": 0.95,
  "oee": 0.7037037037037037
}
```

OEE is analytical/read-only information.

All authenticated roles may access it:

```text
Admin       ✅
Manager     ✅
Technician  ✅
Operator    ✅
```

A missing ProductionRun returns HTTP `404`.

An ineligible or invalid ProductionRun returns HTTP `422`.

---

## Database Migration

Migration:

```text
58633c31421f_add_production_runs_and_downtime_events.py
```

creates:

```text
production_runs
downtime_events
```

ProductionRun references:

```text
production_runs.production_line_id
→ production_lines.id
→ ON DELETE CASCADE
```

DowntimeEvent references:

```text
downtime_events.production_run_id
→ production_runs.id
→ ON DELETE CASCADE
```

and optionally:

```text
downtime_events.machine_id
→ machines.id
→ ON DELETE SET NULL
```

The `SET NULL` behavior preserves historical downtime records if a machine is later removed.

Database defaults include:

```text
ProductionRun.status          = running
ProductionRun.total_quantity  = 0
ProductionRun.good_quantity   = 0
ProductionRun.reject_quantity = 0
```

---

## Testing

The production and OEE implementation is covered through:

- ProductionRun creation;
- missing ProductionLine handling;
- ProductionRun RBAC;
- ProductionRun read access;
- downtime creation;
- machine-to-line hierarchy validation;
- downtime RBAC;
- ProductionRun lifecycle transitions;
- completed/cancelled immutability;
- merged-state quantity validation;
- temporal consistency;
- downtime closing;
- closed-downtime immutability;
- prevention of run completion with open downtime;
- prevention of run completion before downtime end;
- pure OEE mathematical calculations;
- planned downtime;
- unplanned downtime;
- overlapping downtime merging;
- planned/unplanned overlap handling;
- zero-production behavior;
- uncapped Performance;
- open-downtime rejection;
- invalid OEE inputs;
- PostgreSQL-backed OEE integration;
- OEE RBAC;
- missing/running/cancelled ProductionRun behavior.

The complete FactoryPulse backend test suite currently passes:

```text
107 passed
```

---

## Current Architecture

The current production intelligence flow is:

```text
ProductionLine
      ↓
ProductionRun
      ↓
Operational production quantities
      +
DowntimeEvents
      ↓
Lifecycle and temporal validation
      ↓
Completed trusted production data
      ↓
OEE service
      ↓
Pure OEE calculation engine
      ↓
Availability
Performance
Quality
OEE
      ↓
Read-only analytics API
```

This provides the foundation for future industrial analytics such as:

```text
ProductionLine aggregated OEE
Site-level OEE
shift analytics
production targets
downtime Pareto analysis
MTBF / MTTR
quality analytics
production dashboards
trend analysis
energy-per-unit metrics
AI-assisted production insights
```


## Production Analytics

FactoryPulse AI extends the Production/OEE foundation with aggregated production analytics at the `ProductionLine` level.

The first analytics capabilities are:

- aggregated line-level OEE across multiple completed production runs;
- optional reporting-period filtering;
- downtime Pareto analysis by reason;
- downtime Pareto analysis by machine;
- planned vs unplanned downtime totals;
- support for production periods with zero recorded downtime.

### Aggregated ProductionLine OEE

Endpoint:

```http
GET /production-lines/{production_line_id}/oee
```

Optional reporting-period parameters:

```
GET /production-lines/{production_line_id}/oee?start_at=...&end_at=...
```

Only completed `ProductionRun` records are included.

Running and cancelled runs are excluded.

When a reporting period is supplied, only completed runs fully contained within the selected interval are included.

Production runs are intentionally not partially clipped at reporting boundaries because quantities such as `total_quantity` and `good_quantity` represent the entire run.

### OEE Aggregation Strategy

Aggregated OEE is not calculated by averaging the OEE percentages of individual production runs.

Instead, FactoryPulse aggregates the underlying production facts.

For all eligible runs:

- scheduled time is summed;
- planned downtime is summed;
- planned production time is summed;
- unplanned downtime is summed;
- operating time is summed;
- total quantity is summed;
- good quantity is summed;
- ideal production time is calculated as the sum of:

```
ideal_cycle_time_seconds × total_quantity
```

The aggregate factors are then recalculated:

```
Availability =
total operating time
────────────────────────────
total planned production time
```

```
Performance =
total ideal production time
────────────────────────────
total operating time
```

```
Quality =
total good quantity
────────────────────
total quantity
```

```
OEE =
Availability × Performance × Quality
```

This allows production runs with different durations, quantities, and ideal cycle times to be combined correctly.

Performance is intentionally not capped at `1.0`.

Values greater than `1.0` can expose incorrect ideal-cycle configuration or inconsistent production data.

### Production Analytics Domain Layer

Pure aggregation logic is implemented in:

```
app/production/analytics.py
```

Important domain types include:

```
RunOEEContribution
AggregatedOEEMetrics
ProductionAnalyticsError
```

The pure analytics layer is independent from SQLAlchemy and FastAPI.

### Production Analytics Service Layer

Database-backed aggregation is implemented in:

```
app/services/production_analytics_service.py
```

The service:

1. selects eligible completed runs for a ProductionLine;
2. applies the optional reporting period;
3. calculates each run's OEE using the existing trusted run-level OEE service;
4. builds `RunOEEContribution` objects;
5. passes those contributions to the pure aggregation engine.

A completed run without `ideal_cycle_time_seconds` is rejected for aggregated OEE rather than silently producing an incomplete KPI.

### Downtime Analytics

Endpoint:

```
GET /production-lines/{production_line_id}/downtime-analytics
```

Optional reporting-period parameters:

```
GET /production-lines/{production_line_id}/downtime-analytics?start_at=...&end_at=...
```

Downtime analytics uses the downtime events belonging to eligible completed production runs.

The response contains:

- number of production runs;
- number of downtime events;
- recorded downtime duration;
- planned downtime duration;
- unplanned downtime duration;
- Pareto breakdown by reason;
- Pareto breakdown by machine.

### Downtime Pareto by Reason

Downtime reasons are grouped case-insensitively.

For example:

```
Motor Failure
motor failure
 MOTOR FAILURE
```

are treated as the same reason.

Blank reasons are represented as:

```
Unspecified
```

Reason groups are ordered by descending recorded duration.

Each group contains:

- reason;
- event count;
- duration in seconds;
- percentage of total recorded event downtime.

### Downtime Pareto by Machine

Downtime is also aggregated by `machine_id`.

Each machine group contains:

- machine ID;
- event count;
- duration in seconds;
- percentage of total recorded event downtime.

A `machine_id` value of `null` represents a line-wide downtime event rather than a machine-specific incident.

### Recorded Downtime vs OEE Downtime

Downtime Pareto and OEE intentionally use different interval semantics.

OEE measures actual elapsed production loss.

Overlapping downtime intervals are merged before calculating OEE so the same elapsed time is never counted twice.

Pareto analytics measures recorded event attribution.

For example:

```
Motor Failure      10:00 → 10:30 = 30 min
Electrical Fault   10:15 → 10:45 = 30 min
```

Actual elapsed line downtime is:

```
45 minutes
```

but recorded event downtime used for Pareto attribution is:

```
60 minutes
```

This allows FactoryPulse to represent the contribution of individual recorded causes without changing the trusted elapsed-time semantics used by OEE.

### Zero-Downtime Reporting

A ProductionLine can have completed production runs with no recorded downtime.

This is a valid analytics result.

In this case the downtime analytics endpoint returns:

```
event_count = 0
recorded_downtime_seconds = 0
planned_downtime_seconds = 0
unplanned_downtime_seconds = 0
by_reason = []
by_machine = []
```

This is different from a reporting period containing no completed production runs.

If no completed production runs exist for the selected period, the analytics request returns a validation error.

### Analytics RBAC

Production analytics are read-only reporting endpoints.

The following roles can read both line-level OEE and downtime analytics:

- admin;
- manager;
- technician;
- operator.

Existing write permissions remain unchanged.

### Current Production Analytics Architecture

```
ProductionLine
      │
      ├── ProductionRun
      │       │
      │       └── DowntimeEvent
      │
      ├── Aggregated OEE
      │       │
      │       ├── completed runs
      │       ├── run-level OEE engine
      │       └── weighted aggregate metrics
      │
      └── Downtime Analytics
              │
              ├── recorded event duration
              ├── planned / unplanned totals
              ├── Pareto by reason
              └── Pareto by machine
```

### Production Analytics Testing

The backend test suite currently contains:

```
144 passing tests
```

Production analytics testing covers:

- weighted line-level OEE;
- different ideal cycle times;
- zero production;
- zero operating time;
- uncapped performance;
- completed-run filtering;
- exclusion of running and cancelled runs;
- reporting-period filtering;
- downtime reason aggregation;
- case-insensitive reason grouping;
- machine aggregation;
- line-wide downtime;
- overlapping event semantics;
- zero-downtime reporting;
- analytics RBAC;
- missing resources;
- invalid reporting periods;
- periods containing no completed production runs.

### Future Production Analytics

The current analytics foundation can be extended with:

- cumulative downtime Pareto;
- top-loss dashboards;
- MTBF;
- MTTR;
- machine reliability metrics;
- shift-level analytics;
- production target attainment;
- throughput trends;
- site-level OEE;
- area-level OEE;
- cross-line comparisons;
- energy-to-production correlation;
- quality-loss analytics;
- predictive production insights.



## Production Reliability and Data Integrity

FactoryPulse AI hardens the Production/OEE foundation with application-level and PostgreSQL-level integrity controls.

These safeguards ensure production history remains trustworthy for OEE, downtime analytics, and future reliability metrics such as MTBF and MTTR.

### ProductionRun Overlap Protection

FactoryPulse assumes that a single `ProductionLine` cannot execute overlapping production runs.

Production run intervals use half-open semantics:

```text
[started_at, ended_at)
```

This means two consecutive runs may touch at the boundary:

```text
Run A: 08:00 → 12:00
Run B: 12:00 → 16:00
```

This is valid because the first run no longer occupies the line at `12:00`.

An actual overlap is rejected:

```text
Run A: 08:00 → 12:00
Run B: 10:00 → 14:00
```

### Open-Ended Running Runs

A production run with:

```text
ended_at = NULL
```

is treated as an open interval extending indefinitely into the future.

Conceptually:

```text
[started_at, infinity)
```

Therefore, a running production run blocks later production runs on the same line until it is completed or cancelled.

### Application-Level Overlap Validation

ProductionRun creation first performs a service-level overlap query.

The validation is implemented in:

```text
app/services/production_run_service.py
```

If an overlap is detected before insertion, FactoryPulse raises:

```text
ProductionRunValidationError
```

with:

```text
Production run overlaps an existing run on the same production line
```

The API translates this business validation failure to:

```http
422 Unprocessable Content
```

This provides a clear client-facing error before attempting the database insert.

### PostgreSQL Exclusion Constraint

Application-level validation alone cannot fully prevent race conditions.

For example:

```text
Request A                  Request B
    │                          │
overlap check → clear      overlap check → clear
    │                          │
insert                     insert
```

Two concurrent requests could theoretically pass the pre-check before either transaction commits.

FactoryPulse therefore also enforces the rule directly in PostgreSQL using:

```text
ex_production_runs_line_time_overlap
```

The constraint uses:

```text
EXCLUDE USING gist
```

over:

```text
production_line_id WITH =
```

and:

```text
tstzrange(
    started_at,
    COALESCE(ended_at, 'infinity'),
    '[)'
) WITH &&
```

The `&&` operator rejects overlapping time ranges for the same ProductionLine.

This protection applies even when data is inserted outside FastAPI.

### btree_gist

The exclusion constraint requires the PostgreSQL extension:

```text
btree_gist
```

because the GiST constraint combines equality comparison on:

```text
production_line_id
```

with range-overlap comparison on the production interval.

The extension is created using:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

The migration downgrade intentionally does not remove the extension because PostgreSQL extensions can be shared by other indexes or constraints.

### Overlap Migration

ProductionRun overlap enforcement is introduced by Alembic revision:

```text
9965bd5ba936
```

which revises:

```text
58633c31421f
```

The migration:

- enables `btree_gist` when necessary;
- adds the ProductionRun GiST exclusion constraint;
- supports open-ended production runs using PostgreSQL `infinity`;
- uses half-open `[start, end)` interval semantics;
- removes only the exclusion constraint during downgrade.

The migration upgrade, downgrade, and re-upgrade paths were verified successfully.

### Concurrency Integrity Fallback

The service still performs the overlap pre-check for friendly validation.

However, PostgreSQL remains the final authority.

If a concurrent request passes the service check but PostgreSQL rejects the insert through:

```text
ex_production_runs_line_time_overlap
```

the service:

1. catches the SQLAlchemy `IntegrityError`;
2. rolls back the failed transaction;
3. identifies the overlap constraint;
4. raises the same `ProductionRunValidationError`;
5. allows the API to return the same HTTP `422` response.

Therefore both normal validation and race-condition rejection expose consistent API behavior.

### ProductionRun Database CHECK Constraints

FactoryPulse also protects ProductionRun data directly at the database level.

The following constraints are enforced:

```text
ck_production_runs_status
ck_production_runs_status_end_consistency
ck_production_runs_time_order
ck_production_runs_target_quantity_positive
ck_production_runs_total_quantity_nonnegative
ck_production_runs_good_quantity_nonnegative
ck_production_runs_reject_quantity_nonnegative
ck_production_runs_quantity_consistency
ck_production_runs_ideal_cycle_positive
```

#### Valid Status

The database allows only:

```text
running
completed
cancelled
```

#### Status and End-Time Consistency

Running production runs require:

```text
ended_at IS NULL
```

Completed or cancelled production runs require:

```text
ended_at IS NOT NULL
```

#### Production Time Order

When an end time exists:

```text
ended_at >= started_at
```

#### Target Quantity

When specified:

```text
target_quantity > 0
```

#### Production Quantities

The database requires:

```text
total_quantity >= 0
good_quantity >= 0
reject_quantity >= 0
```

and:

```text
good_quantity + reject_quantity <= total_quantity
```

#### Ideal Cycle Time

When configured:

```text
ideal_cycle_time_seconds > 0
```

### DowntimeEvent Database CHECK Constraints

Downtime events are protected by:

```text
ck_downtime_events_category
ck_downtime_events_time_order
```

Valid categories are:

```text
planned
unplanned
```

For closed downtime events:

```text
ended_at >= started_at
```

### Production Integrity Migration

The ProductionRun and DowntimeEvent CHECK constraints are introduced by Alembic revision:

```text
8b9aab729277
```

which revises:

```text
9965bd5ba936
```

Before applying the migration, existing development data was audited against every new rule.

All integrity checks returned:

```text
0 violations
```

The migration upgrade, downgrade, and re-upgrade paths were also verified successfully.

### Production and Test Schema Consistency

FactoryPulse's automated tests recreate the PostgreSQL schema using SQLAlchemy metadata.

To avoid differences between the Alembic-managed development schema and the test schema, the ORM metadata declares the same:

- ProductionRun exclusion constraint;
- ProductionRun CHECK constraints;
- DowntimeEvent CHECK constraints.

The test environment also ensures:

```text
btree_gist
```

exists before `Base.metadata.create_all()` runs.

This keeps:

```text
Alembic production schema
        =
SQLAlchemy test schema
```

for production integrity rules.

### Direct Database Integrity Testing

FactoryPulse includes tests that deliberately bypass:

```text
FastAPI
Pydantic
service validation
```

and insert ORM records directly into PostgreSQL.

These tests verify that PostgreSQL itself rejects:

- overlapping ProductionRuns;
- negative production quantities;
- inconsistent good/reject/total quantities;
- invalid production statuses;
- invalid downtime categories;
- invalid downtime time ordering.

This proves that production integrity does not depend exclusively on API validation.

### Current Reliability Testing

The backend test suite currently contains:

```text
154 passing tests
```

Reliability and integrity coverage includes:

- same-line ProductionRun overlap rejection;
- touching production-run boundaries;
- open-ended running-run protection;
- database-level overlap enforcement;
- PostgreSQL race-condition fallback;
- consistent API `422` behavior;
- ProductionRun CHECK constraints;
- DowntimeEvent CHECK constraints;
- direct database integrity tests;
- production/test schema parity;
- migration upgrade;
- migration downgrade;
- migration re-upgrade.

### Reliability Architecture

```text
Client / Integration
        │
        ▼
FastAPI
        │
        ▼
Pydantic validation
        │
        ▼
Production service validation
        │
        ├── lifecycle rules
        ├── hierarchy rules
        └── overlap pre-check
        │
        ▼
SQLAlchemy
        │
        ▼
PostgreSQL
        │
        ├── foreign keys
        ├── CHECK constraints
        └── GiST exclusion constraint
                │
                ▼
        trusted production history
                │
                ├── OEE
                ├── downtime analytics
                └── future reliability KPIs
```

### Next Reliability Milestone

With production data integrity established, future machine-reliability analytics can safely build on this foundation.

Planned capabilities include:

- failure-event identification;
- failure counts;
- MTTR;
- MTBF;
- machine downtime trends;
- reliability ranking;
- failure Pareto;
- maintenance effectiveness;
- line-level reliability aggregation;
- predictive failure insights.


---

## Machine Reliability Analytics

### Overview

FactoryPulse AI now includes machine-level reliability analytics built on top of the production and downtime domain.

The first reliability implementation provides:

- Machine failure counting
- Total recorded failure downtime
- Mean Time To Repair (MTTR)
- Machine operating exposure
- Mean Time Between Failures (MTBF)
- Optional reporting-period filtering
- Reliability API access for all authenticated roles
- Explicit handling for standalone machines without production-runtime data

The implementation is separated into three layers:

1. Pure reliability calculations
2. PostgreSQL-backed reliability service
3. Machine reliability REST API

This keeps reliability formulas independent from database and API concerns.

---

### Failure Definition

For the current FactoryPulse domain, a machine failure is defined as a `DowntimeEvent` that satisfies all of the following:

- `machine_id` references the target machine
- `category == "unplanned"`
- `ended_at IS NOT NULL`
- The event belongs to a completed `ProductionRun`

Therefore:

- Planned downtime is not counted as a machine failure.
- Line-wide downtime with `machine_id = NULL` is not counted as a machine failure.
- Downtime belonging to another machine is not counted.
- Open downtime events are not counted.
- Failures from incomplete/running production runs are not included in reliability reporting.

This definition provides a deterministic failure population for MTTR and MTBF.

---

### Pure Reliability Domain

The pure calculation layer is implemented in:

`app/production/reliability.py`

Important domain objects include:

- `MachineFailureEvent`
- `MachineFailureMetrics`
- `MachineReliabilityMetrics`
- `ReliabilityDowntimeWindow`
- `MachineReliabilityError`

The module contains no database or FastAPI dependencies.

This allows the reliability mathematics to be tested independently.

---

### Failure Count and Failure Downtime

For a set of eligible failure events:

`failure_count = number of eligible failure events`

Total failure downtime is calculated as:

`total_failure_downtime = Σ(failure ended_at - failure started_at)`

Only closed failures are accepted by the pure calculation layer.

Invalid intervals where:

`ended_at < started_at`

are rejected.

A failure with equal start and end timestamps is valid and contributes zero seconds of downtime.

---

### Mean Time To Repair — MTTR

MTTR represents the average recorded repair/failure duration.

Formula:

`MTTR = total failure downtime / failure count`

Example:

- Failure A: 30 minutes
- Failure B: 90 minutes

Therefore:

- Failure count = 2
- Total failure downtime = 120 minutes
- MTTR = 60 minutes

The API exposes MTTR in seconds as:

`mttr_seconds`

If no failures exist:

`mttr_seconds = null`

It is intentionally not returned as `0`, because zero would imply that repairs were instantaneous rather than that no repair observations exist.

---

### Machine Operating Exposure

MTBF requires a measure of how long the machine was actually exposed to production operation.

For machines assigned to a production line, FactoryPulse derives this exposure from completed production runs.

For each eligible completed run:

`operating exposure = scheduled production duration - unique elapsed downtime`

Scheduled production duration is:

`ProductionRun.ended_at - ProductionRun.started_at`

All recorded downtime associated with the run is considered production-impacting downtime for the current domain model.

This includes:

- Planned downtime
- Unplanned downtime
- Machine-specific downtime
- Line-wide downtime

The objective is to determine how much elapsed production time remained after periods when the production line was stopped.

---

### Downtime Interval Merging

Downtime intervals are merged before subtraction.

This prevents overlapping downtime events from being counted twice.

Example:

Production run:

`08:00 → 12:00`

Downtime events:

- `09:00 → 10:00`
- `09:30 → 10:30`

The recorded event durations total two hours, but the real elapsed downtime is only:

`09:00 → 10:30 = 1.5 hours`

Therefore:

- Scheduled duration = 4 hours
- Unique elapsed downtime = 1.5 hours
- Operating exposure = 2.5 hours

This follows the same elapsed-time principle used by FactoryPulse OEE analytics.

Downtime intervals are also clipped to the production-run boundaries before being merged.

---

### Mean Time Between Failures — MTBF

For machines associated with a production line:

`MTBF = operating exposure / failure count`

Example:

- Completed production duration = 8 hours
- Unique downtime = 2 hours
- Operating exposure = 6 hours
- Machine failures = 1

Therefore:

`MTBF = 6 hours`

The API exposes this as:

`mtbf_seconds`

If the machine has production exposure but no observed failures:

`mtbf_seconds = null`

This avoids incorrectly representing a failure-free period as an MTBF of zero.

---

### Consistent Reliability Population

MTBF requires both its numerator and denominator to describe the same reporting population.

FactoryPulse therefore calculates both:

- Operating exposure
- Machine failures

from eligible completed production runs.

This prevents situations where a failure from a currently running production period is counted while operating exposure is calculated only from completed runs.

---

### Standalone Machines

The industrial hierarchy allows machines to exist directly under an `Area` without being assigned to a `ProductionLine`.

Such machines have:

`production_line_id = NULL`

The current FactoryPulse data model does not yet maintain a dedicated machine runtime/state timeline for these assets.

Therefore a trustworthy MTBF cannot currently be derived for standalone machines.

For a standalone machine, the reliability API returns:

`operating_exposure_seconds = null`

`mtbf_seconds = null`

FactoryPulse deliberately avoids using calendar time as a substitute for machine operating time.

A future machine-runtime/state subsystem can provide operating exposure for standalone assets.

---

### Reporting Period

Machine reliability supports optional query parameters:

- `start_at`
- `end_at`

Example:

`GET /machines/{machine_id}/reliability?start_at=2026-08-01T00:00:00Z&end_at=2026-08-31T23:59:59Z`

When both values are supplied:

`end_at` must be later than `start_at`.

Otherwise the API returns:

`422 Unprocessable Content`

with:

`end_at must be later than start_at`

The reliability service selects completed production runs within the requested reporting period and derives both failure metrics and operating exposure from that population.

---

### Reliability Service

The PostgreSQL-backed orchestration layer is implemented in:

`app/services/machine_reliability_service.py`

Its responsibilities include:

- Validating the requested reporting period
- Loading the target machine
- Selecting eligible machine failures
- Restricting reliability analysis to completed production runs
- Loading production-run downtime
- Grouping downtime by production run
- Calculating unique operating exposure
- Combining failure metrics with operating exposure
- Producing MTTR and MTBF
- Handling standalone machines
- Translating pure-domain errors into service-level errors

The service uses SQLAlchemy's asynchronous API and the project's PostgreSQL database.

---

### Reliability Response Schema

The response schema is implemented in:

`app/schemas/machine_reliability.py`

The API response contains:

- `machine_id`
- `start_at`
- `end_at`
- `failure_count`
- `total_failure_downtime_seconds`
- `mttr_seconds`
- `operating_exposure_seconds`
- `mtbf_seconds`

Example conceptual response:

```json
{
  "machine_id": 12,
  "start_at": null,
  "end_at": null,
  "failure_count": 2,
  "total_failure_downtime_seconds": 7200.0,
  "mttr_seconds": 3600.0,
  "operating_exposure_seconds": 14400.0,
  "mtbf_seconds": 7200.0
}

```


All duration-based reliability values are exposed in seconds so the API uses a consistent base unit.

---

### Machine Reliability API

Reliability is exposed through:

`GET /machines/{machine_id}/reliability`

Optional filters:

- `start_at`
- `end_at`

The endpoint first verifies that the requested machine exists.

If it does not:

`404 Machine not found`

Invalid reporting periods return:

`422 Unprocessable Content`

A valid machine with no failures still returns:

`200 OK`

with zero failure counts and nullable MTTR/MTBF where appropriate.

---

### RBAC

Machine reliability analytics are read-only.

All authenticated FactoryPulse roles can access the endpoint:

- Admin
- Manager
- Technician
- Operator

This follows the existing analytics-read policy based on:

`ALL_ROLES`

No reliability write endpoint is required because reliability metrics are derived from production and downtime records.

---

### Testing Strategy

Machine Reliability Analytics is covered at multiple levels.

#### Pure Reliability Tests

File:

`tests/test_machine_reliability.py`

Coverage includes:

- Multiple failure durations
- Failure count
- Total failure downtime
- MTTR
- Zero failures
- Zero-duration failures
- Open failure rejection
- Invalid failure interval rejection
- MTBF calculation
- MTBF with zero failures
- Negative operating-time rejection
- Negative failure-count rejection
- Operating exposure without downtime
- Overlapping downtime merging
- Downtime clipping to run boundaries
- Open downtime rejection
- Invalid production-run ranges

These tests validate reliability calculations without involving PostgreSQL or FastAPI.

#### PostgreSQL Service Tests

The reliability service is tested against the real PostgreSQL test database.

Coverage includes:

- Selecting only target-machine failures
- Excluding planned downtime from failure count
- Excluding line-wide downtime from machine failures
- Excluding downtime belonging to other machines
- Excluding open failures
- Date-range filtering
- Zero-failure behavior
- Invalid reporting-period rejection
- MTBF calculation from completed production runs
- Operating exposure calculation
- Overlapping downtime merging
- MTBF behavior when no failures exist

The database-backed tests verify that the pure reliability engine is correctly connected to the FactoryPulse production domain.

#### API Tests

The machine reliability API tests cover:

- Failure metrics
- MTTR
- Operating exposure
- MTBF
- Zero-failure responses
- Reporting-period filtering
- Admin access
- Manager access
- Technician access
- Operator access
- Missing machine handling
- Invalid reporting-period handling
- Standalone-machine MTBF behavior

The reliability API tests use FastAPI through `httpx.AsyncClient` with the ASGI application and the real PostgreSQL test database.

No browser automation or Selenium is used for these backend tests.

---

### Architecture

The completed reliability flow is:

`ProductionRun + DowntimeEvent`

↓

`Machine reliability service`

↓

`Failure selection + production exposure selection`

↓

`Pure reliability engine`

↓

`Failure Count + Failure Downtime + MTTR`

↓

`Operating Exposure + MTBF`

↓

`GET /machines/{machine_id}/reliability`

This preserves separation of concerns:

- Database selection belongs to the service layer.
- Reliability mathematics belong to the pure production/reliability layer.
- HTTP behavior belongs to the API layer.

---

### Current Limitations

The current MTBF model intentionally has several explicit boundaries.

1. MTBF is derived only from completed production runs.
2. A machine must belong to a production line for production-run-based operating exposure to be available.
3. Standalone machines do not yet have a machine runtime/state source.
4. Calendar time is not used as a replacement for operating exposure.
5. The current production model assumes downtime associated with a run represents production-impacting elapsed downtime.
6. Predictive AI outputs are not yet used to modify MTTR or MTBF calculations.

These limitations are deliberate so reliability metrics remain explainable and auditable.

---

### Future Reliability Extensions

Possible future additions include:

- Dedicated machine runtime/state history
- Standalone-machine operating exposure
- Failure classification and failure modes
- Reliability trends over time
- MTTR trend analysis
- MTBF trend analysis
- Failure-rate metrics
- Availability metrics at machine level
- Reliability comparison between machines
- Reliability comparison between production lines
- Maintenance effectiveness analytics
- Preventive vs corrective maintenance analysis
- Connection between predictions, alerts, failures, and maintenance outcomes
- AI-assisted failure-risk scoring

These can build on the current reliability foundation without changing the core metric semantics.

---

### Machine Reliability Analytics Status

Machine Reliability Analytics backend milestone:

- Failure definition ✅
- Failure count ✅
- Total failure downtime ✅
- MTTR ✅
- Operating exposure ✅
- Overlapping downtime merging ✅
- MTBF ✅
- Completed-run consistency ✅
- Reporting-period filtering ✅
- Standalone-machine handling ✅
- REST API ✅
- RBAC ✅
- Pure unit tests ✅
- PostgreSQL integration tests ✅
- API tests ✅
- Full regression suite ✅


---

# Operational Intelligence

## Overview

Operational Intelligence connects the production, downtime, and machine reliability layers into a single explainable production-line report.

The goal is to move FactoryPulse AI beyond isolated metrics such as OEE, MTBF, MTTR, and downtime totals and begin answering higher-level operational questions such as:

- Which machines are contributing the most recorded downtime burden?
- Which machine should operations investigate first?
- How is production performance related to machine reliability?
- How much downtime is associated with machines versus line-wide events?
- What are the reliability characteristics of each machine on the production line?

The first Operational Intelligence vertical slice deliberately remains deterministic and explainable. It does not introduce an arbitrary AI-generated health score.

---

## Architecture

The Operational Intelligence layer composes existing analytics rather than duplicating their calculation logic.

```text
Production Line
│
├── Production Runs
│      │
│      └── OEE Analytics
│
├── Downtime Events
│      │
│      └── Downtime Analytics
│
└── Machines
       │
       └── Machine Reliability
               │
               ├── Failure Count
               ├── MTTR
               ├── Operating Exposure
               └── MTBF

                ↓

      Operational Intelligence
      
```


Main implementation files:

```
app/production/operational_intelligence.py
app/services/operational_intelligence_service.py
app/schemas/operational_intelligence.py
app/api/production_lines.py
```

Tests:

```
tests/test_operational_intelligence.py
tests/test_production_oee_foundation.py
```

---

## Pure Operational Intelligence Layer

The pure analytics layer is implemented in:

```
app/production/operational_intelligence.py
```

It does not access PostgreSQL or FastAPI directly.

### MachineReliabilitySnapshot

Represents the reliability information required for one machine:

```
machine_id
machine_name
machine_code

failure_count
mttr_seconds
operating_exposure_seconds
mtbf_seconds
```

### MachineOperationalImpact

Combines reliability with recorded downtime burden:

```
machine_id
machine_name
machine_code

recorded_downtime_event_count
recorded_downtime_seconds
recorded_downtime_share

failure_count
mttr_seconds
operating_exposure_seconds
mtbf_seconds
```

### OperationalDowntimeSummary

Represents the line-level downtime attribution result:

```
recorded_downtime_seconds

machine_attributed_recorded_downtime_seconds
unattributed_recorded_downtime_seconds

machine_attributed_share
unattributed_share

top_downtime_machine_id

machines
```

---

## Important Downtime Semantics

Operational Intelligence intentionally distinguishes between:

```
Unique elapsed downtime
```

and:

```
Recorded downtime burden
```

They represent different concepts and must not be mixed.

---

## Unique Elapsed Downtime

Unique elapsed downtime is used by OEE and production-time calculations.

Example:

```
Machine A:
09:00 → 10:00

Machine B:
09:30 → 10:30
```

The two events overlap for 30 minutes.

Actual unique elapsed downtime is:

```
09:00 → 10:30
=
1.5 hours
```

It is not two hours.

This prevents overlapping downtime events from artificially reducing operating time more than once.

---

## Recorded Downtime Burden

Downtime attribution analytics measure recorded event duration.

Using the same example:

```
Machine A recorded duration = 1 hour
Machine B recorded duration = 1 hour
```

Recorded burden:

```
2 hours
```

This metric answers:

> How much recorded downtime-event burden is associated with each machine?

It does not claim that each machine independently caused that amount of unique production loss.

This distinction is necessary because simultaneous machine events may overlap.

---

## Recorded Downtime Share

For each machine:

```
recorded_downtime_share =
machine recorded downtime duration
/
total recorded downtime-event duration
```

Example:

```
Machine A = 1.5 hours
Machine B = 1.0 hour
Line-wide events = 1.0 hour

Total recorded downtime burden = 3.5 hours
```

Therefore:

```
Machine A share = 1.5 / 3.5
Machine B share = 1.0 / 3.5
Unattributed share = 1.0 / 3.5
```

The percentages remain mathematically consistent because the numerator and denominator use the same recorded-event-duration semantics.

---

## Machine-Attributed and Unattributed Downtime

A DowntimeEvent may have:

```
machine_id = <machine>
```

or:

```
machine_id = NULL
```

A machine-linked event contributes to:

```
machine_attributed_recorded_downtime_seconds
```

A line-wide event with no machine contributes to:

```
unattributed_recorded_downtime_seconds
```

Examples of line-wide events may include:

```
changeover
line-wide setup
general production interruption
site or line-level event
```

---

## Top Downtime Machine

Machines are ranked primarily by:

```
recorded_downtime_seconds descending
```

Tie-breaking uses:

```
failure_count descending
machine_code
machine_id
```

The machine with the highest positive recorded downtime burden becomes:

```
top_downtime_machine_id
```

If no machine has recorded downtime:

```
top_downtime_machine_id = null
```

Machines with zero downtime are still included in the report.

This is important because the report represents the production line's machine population, not only problematic machines.

---

## PostgreSQL Orchestration Service

The orchestration layer is implemented in:

```
app/services/operational_intelligence_service.py
```

It composes three existing analytics systems:

```
calculate_production_line_oee()
+
calculate_production_line_downtime_analytics()
+
calculate_machine_reliability()
```

The service first retrieves all machines assigned to the production line.

For each machine it calculates:

```
failure_count
MTTR
operating exposure
MTBF
```

The resulting reliability information is then combined with the downtime analytics breakdown by the pure Operational Intelligence layer.

---

## Reuse Instead of Duplication

Operational Intelligence intentionally reuses the existing OEE, downtime, and reliability services.

This avoids introducing a second implementation of:

```
OEE calculations
downtime duration calculations
failure definitions
MTTR calculations
operating exposure calculations
MTBF calculations
```

Therefore the new report uses the same semantics already validated elsewhere in FactoryPulse AI.

---

## Reporting Period

The endpoint supports:

```
start_at
end_at
```

The reporting period is passed to the existing production and reliability analytics services.

The selected production cohort consists of completed production runs that satisfy the existing production analytics period rules.

Invalid ranges where:

```
end_at <= start_at
```

are rejected.

If no completed production runs exist in the selected period, Operational Intelligence cannot calculate the production report and returns an error.

---

## API

Endpoint:

```
GET /production-lines/{production_line_id}/operational-intelligence
```

Optional query parameters:

```
start_at
end_at
```

All authenticated FactoryPulse roles may read Operational Intelligence analytics.

Current roles:

```
admin
manager
technician
operator
```

The endpoint follows the same read-access policy as the existing OEE, downtime, reliability, and maintenance analytics endpoints.

---

## API Response Structure

Conceptually:

```
ProductionLineOperationalIntelligenceResponse
│
├── production_line_id
├── start_at
├── end_at
├── run_count
│
├── oee
│      ├── run_count
│      ├── scheduled_time_seconds
│      ├── planned_downtime_seconds
│      ├── planned_production_time_seconds
│      ├── unplanned_downtime_seconds
│      ├── operating_time_seconds
│      ├── total_quantity
│      ├── good_quantity
│      ├── availability
│      ├── performance
│      ├── quality
│      └── oee
│
└── operational_impact
       ├── recorded_downtime_seconds
       ├── machine_attributed_recorded_downtime_seconds
       ├── unattributed_recorded_downtime_seconds
       ├── machine_attributed_share
       ├── unattributed_share
       ├── top_downtime_machine_id
       │
       └── machines
              ├── machine_id
              ├── machine_name
              ├── machine_code
              ├── recorded_downtime_event_count
              ├── recorded_downtime_seconds
              ├── recorded_downtime_share
              ├── failure_count
              ├── mttr_seconds
              ├── operating_exposure_seconds
              └── mtbf_seconds
```

---

## Example

Consider an eight-hour completed production run:

```
08:00 → 16:00
```

Events:

```
Machine A failure:
09:00 → 10:00

Machine B failure:
09:30 → 10:30

Line-wide planned changeover:
12:00 → 13:00

Machine A failure:
14:00 → 14:30
```

### OEE Time Semantics

Unique unplanned downtime:

```
09:00 → 10:30 = 1.5 hours
14:00 → 14:30 = 0.5 hours

Total = 2 hours
```

Planned downtime:

```
1 hour
```

Therefore:

```
Scheduled time = 8 hours

Planned production time =
8h - 1h
=
7h

Operating time =
7h - 2h
=
5h
```

---

## Recorded Downtime Burden for the Same Example

Recorded event durations:

```
Machine A =
1h + 0.5h
=
1.5h

Machine B =
1h

Line-wide =
1h
```

Total recorded burden:

```
3.5 hours
```

This differs from unique elapsed downtime because overlapping machine events are intentionally preserved for burden attribution.

---

## Reliability Integration

For the same machine population, Operational Intelligence exposes existing Machine Reliability metrics.

Example:

```
Machine A

failure_count = 2
failure downtime = 1.5h

MTTR =
1.5h / 2
=
45 minutes
```

If operating exposure is five hours:

```
MTBF =
5h / 2
=
2.5 hours
```

Machine B:

```
failure_count = 1
MTTR = 1 hour
operating exposure = 5 hours
MTBF = 5 hours
```

This allows production performance and machine reliability to appear in one operational report.

---

## Error Handling

The endpoint returns:

```
404
```

when the production line does not exist.

It returns:

```
422
```

for analytics-domain errors such as:

```
invalid reporting period
no completed production runs
unsupported underlying analytics condition
```

---

## RBAC

Operational Intelligence is currently read-only.

Allowed roles:

```
admin
manager
technician
operator
```

No new write permissions are introduced by this milestone.

---

## Testing

Operational Intelligence is tested at multiple levels.

### Pure Analytics Tests

```
tests/test_operational_intelligence.py
```

Coverage includes:

```
machine downtime burden calculation
machine ranking
machine with zero downtime
empty downtime history
nullable shares
duplicate machine ID rejection
```

### PostgreSQL Integration Tests

Coverage includes:

```
OEE integration
overlapping machine downtime
line-wide downtime
machine reliability integration
MTTR
MTBF
operating exposure
machine population with zero-downtime machine
invalid reporting period
```

### API Tests

Coverage includes:

```
complete report response
OEE values
recorded downtime attribution
machine ranking
reliability metrics
RBAC for all authenticated roles
missing production line
invalid date range
period without completed production runs
```

---

## Regression Status

After the first Operational Intelligence vertical slice:

```
243 tests passed
```

The complete backend regression suite remained green.

---

## Current Limitations

The current Operational Intelligence report deliberately does not claim exact production-loss attribution to individual machines.

Because machine downtime events may overlap, recorded machine downtime burden is not equivalent to unique lost production time.

For example:

```
Machine A = 1 hour
Machine B = 1 hour

with 30 minutes overlap
```

does not imply two hours of production loss.

Therefore FactoryPulse currently reports:

```
recorded_downtime_share
```

rather than:

```
production_loss_share
```

This naming is intentional.

---

## Performance Consideration

The initial orchestration service calculates machine reliability separately for each machine.

Conceptually:

```
line machines
    ↓
for each machine
    ↓
calculate machine reliability
```

This maximizes reuse and correctness for the first implementation.

For large production lines, this may later be optimized using bulk PostgreSQL queries while preserving the same domain models and API contract.

---

## Future Operational Intelligence Extensions

Potential next capabilities include:

### Operational Priority Ranking

Combine explainable operational metrics to identify which machines deserve attention first.

Potential inputs:

```
recorded downtime burden
failure count
MTTR
MTBF
production context
```

Any priority model should remain explainable.

---

### Downtime Cause Intelligence

Connect:

```
machine
+
reason
+
frequency
+
duration
```

to identify recurring dominant causes.

---

### Production Loss Estimation

Use production context such as:

```
ideal cycle time
downtime duration
production rate
```

to estimate theoretical lost production opportunity.

This must be clearly distinguished from confirmed physical production loss.

---

### Maintenance and Reliability Correlation

Future data-model improvements could allow:

```
DowntimeEvent
    ↓
MaintenanceRecord
```

This would enable analysis such as:

```
repeated failure after maintenance
MTBF before versus after maintenance
repair effectiveness
failure recurrence
maintenance impact on reliability
```

The current MaintenanceRecord model does not yet directly reference a DowntimeEvent, so FactoryPulse does not fabricate these relationships.

---

### Trend Analytics

Future reports may compare:

```
current period
vs
previous period
```

for:

```
OEE
downtime
failure count
MTBF
MTTR
maintenance response
```

---

### Operational Recommendations

Once sufficient reliable metrics exist, FactoryPulse AI may produce explainable recommendations such as:

```
Machine M-101 has the largest recorded downtime burden
and the lowest MTBF on Line A.

Recommended operational focus:
inspect recurring failure causes and recent corrective maintenance.
```

Recommendations should always remain traceable to the underlying industrial data.

---

## Current Operational Intelligence Flow

```
Organization
    ↓
Site
    ↓
Area
    ↓
Production Line
    │
    ├── Production Runs
    │       ↓
    │      OEE
    │
    ├── Downtime Events
    │       ↓
    │   Downtime Analytics
    │
    └── Machines
            ↓
       Reliability Analytics
            │
            ├── Failures
            ├── MTTR
            ├── Operating Exposure
            └── MTBF

                ↓

       Operational Intelligence

                ↓

Production Performance
+
Downtime Attribution
+
Machine Reliability
+
Operational Prioritization Foundation
```

Operational Intelligence is therefore the first FactoryPulse layer that deliberately combines multiple previously independent industrial analytics domains into one production-management view.


---

# Operational Priority Ranking

## Overview

Operational Priority Ranking extends the Operational Intelligence layer by identifying which machines deserve operational attention first.

The ranking is intentionally:

- deterministic
- explainable
- relative to the machines on the selected production line
- based on existing industrial metrics
- free from arbitrary AI-generated scores

FactoryPulse does not currently expose a mysterious health score such as:

```text
Machine A health score = 37.4
```

Instead, it exposes the evidence behind the ranking.

Example:

```
Machine A
priority_rank = 1

downtime_rank = 1
failure_rank = 1
mttr_rank = 2
mtbf_rank = 1
```

This allows operators and managers to understand why a machine received its position.

---

## Ranking Inputs

The current priority model uses four operational indicators:

```
recorded downtime burden
failure count
MTTR
MTBF
```

Their adverse directions are:

```
Higher recorded downtime = worse

Higher failure count = worse

Higher MTTR = worse

Lower MTBF = worse
```

These metrics already exist in the Operational Intelligence machine-impact model.

The priority engine therefore does not introduce a second implementation of downtime or reliability calculations.

---

## Why FactoryPulse Does Not Use Arbitrary Weights

A weighted formula such as:

```
priority score =
downtime × 0.40
+
failure count × 0.30
+
MTTR × 0.20
+
MTBF × 0.10
```

would require evidence that those weights correctly represent the business priorities of the factory.

FactoryPulse does not currently possess that plant-specific knowledge.

Therefore the first priority model gives equal importance to the four ranking dimensions rather than inventing business weights.

Future versions may support configurable weights if organizations explicitly define them.

---

## Metric Ranking

Each machine receives a relative rank for every supported metric.

Example:

```
               Downtime   Failures   MTTR   MTBF

Machine A         1          1        2      1
Machine B         2          2        1      2
Machine C         3          3        -      -
```

Rank:

```
1
```

represents the most concerning value for that metric.

---

## Downtime Rank

Machines are ranked by:

```
recorded_downtime_seconds
```

in descending order.

Therefore:

```
more recorded downtime
=
more operational concern
```

Example:

```
Machine A = 4 hours → rank 1
Machine B = 2 hours → rank 2
Machine C = 0 hours → rank 3
```

---

## Failure Rank

Machines are ranked by:

```
failure_count
```

in descending order.

Therefore:

```
more qualifying failures
=
more operational concern
```

The failure definition remains the same as Machine Reliability Analytics.

Operational Priority Ranking does not redefine what constitutes a failure.

---

## MTTR Rank

MTTR measures the average time required to recover from qualifying machine failures.

For MTTR:

```
higher MTTR
=
worse
```

Example:

```
Machine A MTTR = 20 minutes
Machine B MTTR = 50 minutes
```

Therefore:

```
Machine B receives the more concerning MTTR rank.
```

---

## MTBF Rank

MTBF measures operating exposure relative to failure count.

For MTBF:

```
lower MTBF
=
worse
```

Example:

```
Machine A MTBF = 6 hours
Machine B MTBF = 20 hours
```

Machine A receives the more concerning MTBF rank because it fails more frequently relative to its operating exposure.

---

## Competition Ranking

Metric rankings use competition ranking.

Example:

```
Machine A downtime = 2 hours
Machine B downtime = 2 hours
Machine C downtime = 1 hour
```

The downtime ranks are:

```
Machine A = 1
Machine B = 1
Machine C = 3
```

They are not:

```
1
2
3
```

because Machine A and Machine B have equal metric values.

Competition ranking preserves genuine ties.

---

## Priority Position

The first priority model combines the four metric ranks with equal importance.

Conceptually:

```
priority rank value =
downtime rank
+
failure rank
+
MTTR rank
+
MTBF rank
```

Lower aggregate rank values represent greater operational concern.

Example:

```
Machine A

downtime rank = 1
failure rank = 1
MTTR rank = 2
MTBF rank = 1

aggregate rank value = 5
```

Machine B:

```
downtime rank = 2
failure rank = 2
MTTR rank = 1
MTBF rank = 2

aggregate rank value = 7
```

Therefore:

```
Machine A priority_rank = 1
Machine B priority_rank = 2
```

The internal aggregate rank value is not exposed as a fake health score.

The public API exposes the priority position and its component evidence.

---

## Zero-Failure Machines

A machine with:

```
failure_count = 0
```

naturally has:

```
MTTR = null
MTBF = null
```

This does not mean that the machine has poor reliability.

It means there were no qualifying failures from which those metrics could be calculated.

FactoryPulse therefore does not interpret:

```
MTBF = null
```

as:

```
bad MTBF
```

For ranking purposes, a zero-failure machine is treated as better than machines that experienced qualifying failures.

Its public response remains:

```
mttr_rank = null
mtbf_rank = null
```

because the metrics are not applicable.

This distinction prevents healthy machines from being penalized for missing failure-based metrics.

---

## No Operational Concern

If every machine has:

```
recorded_downtime_seconds = 0
failure_count = 0
```

there is no evidence supporting an operational priority.

FactoryPulse therefore returns:

```
top_priority_machine_id = null
```

and machine priority values are:

```
priority_rank = null
```

rather than arbitrarily selecting a machine.

---

## Priority Result Model

The pure domain layer exposes:

```
MachineOperationalPriority
```

with:

```
machine_id
machine_name
machine_code

priority_rank

downtime_rank
failure_rank
mttr_rank
mtbf_rank
```

The line-level summary exposes:

```
OperationalPrioritySummary
```

with:

```
top_priority_machine_id
machines
```

---

## Integration with Operational Intelligence

The priority calculation occurs after the existing Operational Impact calculation.

Flow:

```
Production Runs
      ↓
     OEE

Downtime Events
      ↓
Downtime Analytics

Machines
      ↓
Reliability Analytics
      ↓
Machine Operational Impact
      ↓
Operational Priority Ranking
```

No additional PostgreSQL query is required specifically for ranking.

The priority engine operates on machine facts already produced by Operational Intelligence.

---

## API Integration

Priority ranking is exposed through the existing endpoint:

```
GET /production-lines/{production_line_id}/operational-intelligence
```

No separate priority endpoint is required.

The response now conceptually contains:

```
Operational Intelligence
│
├── OEE
│
├── Operational Impact
│   ├── downtime attribution
│   ├── machine downtime burden
│   ├── failure count
│   ├── MTTR
│   ├── MTBF
│   └── operating exposure
│
└── Priority
    ├── top_priority_machine_id
    │
    └── machines
        ├── priority_rank
        ├── downtime_rank
        ├── failure_rank
        ├── mttr_rank
        └── mtbf_rank
```

This keeps production performance, reliability facts, and operational prioritization within one coherent report.

---

## Validation Rules

The pure priority engine rejects inconsistent input such as:

```
negative recorded downtime
negative failure count
duplicate machine IDs
```

A machine with qualifying failures must also have the reliability values required by the priority engine.

This protects the ranking from silently operating on contradictory data.

---

## Testing

Operational Priority Ranking is covered by pure analytics, PostgreSQL-backed orchestration, and API tests.

Pure tests cover:

```
priority ordering
metric ranks
competition ranking
ties
zero-failure machines
null MTTR/MTBF semantics
no-concern population
invalid machine reliability input
```

PostgreSQL orchestration tests prove that priority ranking uses metrics calculated from actual FactoryPulse production and downtime records.

API tests prove that the ranking evidence is exposed correctly through the Operational Intelligence endpoint.

---

## Regression Status

After Operational Priority Ranking:

```
248 tests passed
```

The complete FactoryPulse backend regression suite remained green.

---

## Current Interpretation

Operational Priority Ranking answers:

> Which machine currently deserves the most operational attention based on the evidence available in FactoryPulse?

It does not claim:

> Which machine is objectively the most important machine in the factory?

Business criticality, replacement cost, safety impact, production bottleneck importance, spare-parts availability, and other plant-specific factors are not yet included.

The current priority result should therefore be interpreted as:

```
data-driven operational concern
```

rather than:

```
complete business criticality
```

---

## Future Priority Extensions

Future versions may incorporate explicitly modeled factors such as:

```
machine criticality
safety impact
production bottleneck importance
maintenance backlog
alert severity
maintenance response performance
repeat failure patterns
production loss estimates
cost impact
```

Plant-specific configurable weights may also be introduced if organizations define their priorities explicitly.

Until then, FactoryPulse keeps the ranking simple, transparent, and auditable.


---

# Downtime Cause Intelligence

## Overview

Downtime Cause Intelligence extends Operational Intelligence by explaining the recorded reasons associated with machine downtime.

After Operational Priority Ranking identifies which machine deserves attention, Downtime Cause Intelligence helps answer:

> Why is this machine accumulating downtime?

The analysis uses the existing:

```text
DowntimeEvent.reason
```

field.

FactoryPulse deliberately refers to these values as:

```text
recorded downtime reasons
```

rather than:

```text
verified root causes
```

because the current data model does not contain a formal root-cause-analysis workflow or verified root-cause entity.

---

## Operational Flow

The Operational Intelligence flow now becomes:

```text
Production Line
      │
      ├── OEE
      │
      ├── Downtime Attribution
      │
      ├── Machine Reliability
      │
      ├── Operational Priority Ranking
      │
      └── Downtime Cause Intelligence
              │
              ├── dominant duration reason
              ├── most frequent reason
              └── per-reason breakdown
```

This allows FactoryPulse to move from:

```text
Which machine has the largest operational concern?
```

to:

```text
Which recorded downtime reasons explain that concern?
```

---

## Pure Analytics Layer

The reason-analysis logic is implemented in:

```text
app/production/downtime_analytics.py
```

The pure calculation:

```text
calculate_machine_downtime_reason_analytics()
```

accepts normalized downtime analytics events and a target machine ID.

It does not access PostgreSQL or FastAPI directly.

---

## Machine Downtime Reason Summary

For each machine, FactoryPulse calculates:

```text
machine_id

event_count
recorded_downtime_seconds

dominant_duration_reason
most_frequent_reason

by_reason
```

The `by_reason` collection contains detailed metrics for every recorded reason.

---

## Per-Reason Metrics

Each recorded reason includes:

```text
reason

event_count
duration_seconds
percentage

planned_event_count
planned_duration_seconds

unplanned_event_count
unplanned_duration_seconds
```

This allows FactoryPulse to distinguish:

```text
how often a reason occurred
```

from:

```text
how much recorded downtime it accumulated
```

---

## Duration vs Frequency

Frequency and downtime burden are intentionally treated as different concepts.

Example:

```text
Motor Overheating
2 events
2.0 hours total

Bearing Failure
3 events
1.5 hours total
```

The result is:

```text
dominant_duration_reason =
Motor Overheating

most_frequent_reason =
Bearing Failure
```

Therefore:

```text
most frequent
```

does not necessarily mean:

```text
largest downtime burden
```

This distinction is operationally important.

A frequent short interruption may require a different response from a rare but extremely long failure.

---

## Dominant Duration Reason

The:

```text
dominant_duration_reason
```

is the recorded reason with the greatest accumulated downtime-event duration for the target machine.

Conceptually:

```text
Reason A = 3.0 hours
Reason B = 1.5 hours
Reason C = 0.5 hours
```

results in:

```text
dominant_duration_reason = Reason A
```

---

## Most Frequent Reason

The:

```text
most_frequent_reason
```

is the recorded reason with the greatest number of downtime events.

Example:

```text
Reason A = 2 events
Reason B = 5 events
Reason C = 1 event
```

results in:

```text
most_frequent_reason = Reason B
```

---

## Reason Share

For each machine reason:

```text
percentage =
reason recorded downtime duration
/
machine total recorded downtime duration
```

Example:

```text
Machine A total recorded downtime = 4 hours

Motor Overheating = 2 hours
Bearing Failure = 1.5 hours
Sensor Fault = 0.5 hours
```

Therefore:

```text
Motor Overheating = 50%
Bearing Failure = 37.5%
Sensor Fault = 12.5%
```

These percentages describe recorded downtime-event burden.

They do not represent independently attributable unique production loss when events overlap.

The same semantic distinction used by Operational Intelligence remains in effect.

---

## Planned and Unplanned Breakdown

A recorded reason may appear in both planned and unplanned downtime events.

FactoryPulse therefore preserves both categories.

Example:

```text
Maintenance

planned:
1 event
60 minutes

unplanned:
1 event
30 minutes
```

The reason summary becomes:

```text
event_count = 2
duration = 90 minutes

planned_event_count = 1
planned_duration = 60 minutes

unplanned_event_count = 1
unplanned_duration = 30 minutes
```

This prevents the analytics layer from treating all occurrences of the same textual reason as operationally identical.

---

## Reason Normalization

Recorded reasons are normalized for grouping.

FactoryPulse currently:

```text
trims surrounding whitespace
+
groups case-insensitively
```

Therefore values such as:

```text
"Motor Overheating"
" motor overheating "
"MOTOR OVERHEATING"
```

belong to the same logical reason group.

The first normalized display representation is preserved for the report.

---

## Unspecified Reasons

If a reason contains only whitespace, the analytics layer normalizes it to:

```text
Unspecified
```

This prevents blank reason groups from appearing in reports.

---

## Machine Isolation

Reason intelligence is calculated separately for each machine.

Events belonging to another machine do not contribute to the target machine's:

```text
event_count
recorded_downtime_seconds
reason percentages
dominant duration reason
most frequent reason
```

This preserves machine-level analytical isolation.

---

## Empty Machine History

A production-line machine may have no downtime events in the selected reporting period.

It remains part of Operational Intelligence.

Its reason summary becomes:

```text
event_count = 0

recorded_downtime_seconds = 0

dominant_duration_reason = null

most_frequent_reason = null

by_reason = []
```

FactoryPulse therefore does not fabricate a cause when no downtime evidence exists.

---

## PostgreSQL Integration

The existing production-line downtime analytics service already loads the relevant downtime events from PostgreSQL.

The service now preserves the normalized events inside:

```text
ProductionLineDowntimeAnalyticsResult
```

alongside:

```text
run_count
metrics
events
```

Operational Intelligence reuses those events to calculate machine reason summaries.

Conceptually:

```text
PostgreSQL
    ↓
Downtime Events
    ↓
Downtime Analytics Service
    │
    ├── aggregate downtime metrics
    └── normalized analytics events
                   ↓
         Operational Intelligence
                   ↓
       Machine Reason Intelligence
```

---

## No Additional Downtime Query

Downtime Cause Intelligence does not execute another query to reload the same downtime events.

The existing downtime analytics service already retrieved them.

Operational Intelligence reuses:

```text
downtime_result.events
```

This avoids unnecessary duplicate database work and keeps the analytics semantics synchronized.

---

## Integration with Operational Priority

Operational Priority Ranking answers:

```text
Which machine deserves operational attention first?
```

Downtime Cause Intelligence adds:

```text
Which recorded reasons are contributing to that machine's downtime?
```

Example:

```text
Priority #1
Machine M-101

Recorded downtime = 6.2 hours
Failure count = 5
MTBF = 7.4 hours

Dominant duration reason:
Motor Overheating
3.4 hours

Most frequent reason:
Bearing Failure
4 events
```

This provides substantially more operational context than a priority rank alone.

---

## API Integration

Downtime Cause Intelligence is exposed through the existing endpoint:

```http
GET /production-lines/{production_line_id}/operational-intelligence
```

No additional API endpoint is required.

The Operational Intelligence response now conceptually contains:

```text
Operational Intelligence
│
├── OEE
│
├── Operational Impact
│
├── Priority
│
└── Downtime Reasons
    │
    └── Machine
        ├── event_count
        ├── recorded_downtime_seconds
        ├── dominant_duration_reason
        ├── most_frequent_reason
        │
        └── by_reason
            ├── reason
            ├── event_count
            ├── duration_seconds
            ├── percentage
            ├── planned_event_count
            ├── planned_duration_seconds
            ├── unplanned_event_count
            └── unplanned_duration_seconds
```

---

## Terminology: Reason vs Root Cause

The current FactoryPulse model stores:

```text
DowntimeEvent.reason
```

This value may describe why the downtime was recorded, but it is not sufficient evidence that a formal root-cause investigation has verified the underlying technical cause.

Therefore FactoryPulse currently uses terminology such as:

```text
recorded reason
downtime reason
dominant recorded reason
```

and avoids claiming:

```text
verified root cause
```

A future Root Cause Analysis domain could model that distinction explicitly.

---

## Testing

Downtime Cause Intelligence is tested at multiple layers.

### Pure Analytics

Coverage includes:

```text
duration-based dominant reason
frequency-based dominant reason
reason normalization
case-insensitive grouping
whitespace normalization
planned/unplanned separation
empty machine history
unspecified reasons
machine isolation
reason percentage
```

### PostgreSQL Integration

Tests prove that real DowntimeEvent records are:

```text
loaded from the completed production-run cohort
normalized
grouped
isolated by machine
integrated into Operational Intelligence
```

A dedicated integration scenario verifies that:

```text
Motor Overheating
=
largest duration

Bearing Failure
=
highest frequency
```

and that FactoryPulse correctly reports both independently.

### API

The HTTP contract verifies that:

```text
dominant_duration_reason
most_frequent_reason
reason durations
reason event counts
reason shares
planned/unplanned breakdown
```

are correctly exposed by the Operational Intelligence endpoint.

---

## Regression Status

After Downtime Cause Intelligence:

```text
254 tests passed
```

The complete FactoryPulse backend regression suite remained green.

---

## Current Operational Intelligence Capability

FactoryPulse can now answer four progressively deeper production questions:

```text
1. How is the line performing?
   ↓
   OEE

2. Which machines are contributing downtime and reliability problems?
   ↓
   Operational Impact

3. Which machine deserves attention first?
   ↓
   Operational Priority Ranking

4. What recorded reasons explain that machine's downtime?
   ↓
   Downtime Cause Intelligence
```

This creates the first substantial diagnostic chain in FactoryPulse AI.

---

## Current Limitations

Recorded reason analytics are based on textual:

```text
DowntimeEvent.reason
```

values.

The current system does not yet model:

```text
formal root-cause investigations
failure-mode taxonomy
cause hierarchy
cause verification
corrective-action effectiveness by cause
machine component responsible for failure
```

Reason normalization currently handles case and surrounding whitespace but does not perform semantic matching.

Therefore values such as:

```text
Motor Overheating
Motor Overheat
Overheated Motor
```

may still remain different reason groups.

Automatic semantic consolidation should not be introduced without an auditable strategy.

---

## Future Extensions

Potential extensions include:

```text
structured failure modes
root-cause taxonomy
component-level failures
reason recurrence trends
reason Pareto changes over time
maintenance response by failure reason
failure recurrence after maintenance
AI-assisted cause suggestions
```

AI-generated cause suggestions should remain clearly distinguished from confirmed engineering root causes.



---

# Period-over-Period Operational Trends

## Overview

Period-over-Period Operational Trends extends FactoryPulse Operational Intelligence by comparing a selected reporting period with the immediately preceding period of equal duration.

It answers:

> Is production performance improving, worsening, or remaining stable?

The comparison includes both line-level production metrics and machine-level reliability metrics.

---

## Comparison Period Semantics

The API receives an explicit current reporting period:

```text
start_at
end_at
```

Example:

```text
Current:
2026-08-14 → 2026-08-21
```

The period duration is:

```text
7 days
```

FactoryPulse automatically derives the immediately preceding period of identical duration:

```text
Previous:
2026-08-07 → 2026-08-14

Current:
2026-08-14 → 2026-08-21
```

The two periods are therefore:

```text
adjacent
+
equal duration
```

This prevents arbitrary comparisons between incompatible time windows.

---

## Architecture

Operational Trends does not reimplement OEE, downtime, or reliability calculations.

Instead:

```text
Current Period
      ↓
Operational Intelligence
      ↓
Current Snapshot

Previous Equal Period
      ↓
Operational Intelligence
      ↓
Previous Snapshot

Current Snapshot
+
Previous Snapshot
      ↓
Pure Trend Engine
      ↓
Operational Trend Summary
```

Main implementation files:

```text
app/production/operational_trends.py
app/services/operational_trends_service.py
app/schemas/operational_trends.py
app/api/production_lines.py
```

Tests:

```text
tests/test_operational_trends.py
tests/test_production_oee_foundation.py
```

---

## Line-Level Trend Metrics

FactoryPulse currently compares:

```text
OEE
Availability
Performance
Quality

Recorded downtime
Total machine failure count
```

These metrics retain their existing FactoryPulse definitions.

Operational Trends only compares their period values.

---

## Machine-Level Trend Metrics

For each machine, FactoryPulse compares:

```text
recorded downtime
failure count
MTTR
MTBF
```

This allows the system to show whether individual machine reliability is improving or worsening between periods.

---

## Trend Direction

Each comparison produces:

```text
current_value
previous_value
delta
direction
```

Supported directions are:

```text
improved
worsened
unchanged
not_comparable
```

---

## Higher-Is-Better Metrics

For:

```text
OEE
Availability
Performance
Quality
MTBF
```

higher values represent improvement.

Example:

```text
Previous OEE = 0.72
Current OEE = 0.78

delta = +0.06
direction = improved
```

---

## Lower-Is-Better Metrics

For:

```text
recorded downtime
failure count
MTTR
```

lower values represent improvement.

Example:

```text
Previous downtime = 12 hours
Current downtime = 9 hours

delta = -3 hours
direction = improved
```

The raw delta and semantic direction are kept separate.

---

## Unchanged Metrics

When:

```text
current_value == previous_value
```

FactoryPulse returns:

```text
delta = 0
direction = unchanged
```

---

## Not Comparable

Some reliability metrics may legitimately be unavailable.

Example:

```text
Previous:
failure_count = 2
MTBF = 8 hours

Current:
failure_count = 0
MTBF = null
```

FactoryPulse must not interpret:

```text
8 hours → null
```

as MTBF deterioration.

The current MTBF is unavailable because there were no qualifying failures from which MTBF could be calculated.

Therefore:

```text
delta = null
direction = not_comparable
```

The failure-count comparison still remains valid:

```text
2 → 0
direction = improved
```

The same rule applies to MTTR.

---

## Pure Trend Engine

The pure trend logic is implemented in:

```text
app/production/operational_trends.py
```

It does not access:

```text
PostgreSQL
FastAPI
SQLAlchemy
production services
```

It only compares current and previous snapshots.

This keeps trend interpretation independent from data retrieval.

---

## Operational Metric Trend

The core result structure is:

```text
OperationalMetricTrend
```

containing:

```text
current_value
previous_value
delta
direction
```

The trend engine receives whether higher or lower values represent improvement.

---

## Machine Period Snapshot

Each machine snapshot contains:

```text
machine_id
machine_name
machine_code

recorded_downtime_seconds
failure_count

mttr_seconds
mtbf_seconds
```

These values originate from the already established Operational Intelligence and Machine Reliability layers.

---

## Operational Period Snapshot

The line-level period snapshot contains:

```text
oee
availability
performance
quality

recorded_downtime_seconds
total_failure_count

machines
```

The snapshot is deliberately limited to facts needed by the trend engine.

---

## Machine Population

The trend engine compares machines by:

```text
machine_id
```

Machine IDs must be unique within each period.

If a machine appears in only one period, metrics that cannot be compared across both periods become:

```text
not_comparable
```

rather than being silently converted to zero.

---

## PostgreSQL Orchestration

The orchestration service is implemented in:

```text
app/services/operational_trends_service.py
```

It receives:

```text
production_line_id
start_at
end_at
```

and calculates:

```text
period_duration = end_at - start_at
```

Then:

```text
previous_start_at =
start_at - period_duration

previous_end_at =
start_at
```

It calls the existing Operational Intelligence service twice:

```text
calculate_production_line_operational_intelligence(
    current period
)

calculate_production_line_operational_intelligence(
    previous period
)
```

This guarantees both periods use the same definitions for:

```text
OEE
downtime
failure count
MTTR
MTBF
machine operational impact
```

---

## Production Data Requirement

Both comparison periods currently require completed production runs.

If either period contains no completed runs, FactoryPulse returns an analytics error rather than treating missing production as zero.

This avoids misleading comparisons such as:

```text
Previous OEE = 0
Current OEE = 0.80
```

when the previous period actually contained no production data.

Future versions may introduce explicit states such as:

```text
no_production
insufficient_data
```

---

## API

Endpoint:

```http
GET /production-lines/{production_line_id}/operational-trends
```

Required query parameters:

```text
start_at
end_at
```

Example:

```text
/production-lines/5/operational-trends
?start_at=2026-08-14T00:00:00Z
&end_at=2026-08-21T00:00:00Z
```

FactoryPulse automatically derives:

```text
Previous:
2026-08-07 → 2026-08-14

Current:
2026-08-14 → 2026-08-21
```

---

## API Response

The response contains:

```text
production_line_id

current_period
previous_period

trends
```

The full Operational Intelligence reports for both periods are not returned through this endpoint.

They are used internally by the trend service.

This keeps the HTTP response focused and avoids duplicating large Operational Intelligence payloads.

---

## Conceptual Response Structure

```text
Operational Trends
│
├── production_line_id
│
├── current_period
│   ├── start_at
│   └── end_at
│
├── previous_period
│   ├── start_at
│   └── end_at
│
└── trends
    │
    ├── OEE
    ├── Availability
    ├── Performance
    ├── Quality
    ├── Recorded Downtime
    ├── Total Failure Count
    │
    └── Machines
        ├── Recorded Downtime
        ├── Failure Count
        ├── MTTR
        └── MTBF
```

Each metric contains:

```text
current_value
previous_value
delta
direction
```

---

## Example

Previous period:

```text
Recorded downtime = 3 hours
Failures = 2
MTTR = 1 hour
MTBF = 2.5 hours
```

Current period:

```text
Recorded downtime = 1 hour
Failures = 1
MTTR = 0.5 hours
MTBF = 7 hours
```

FactoryPulse reports:

```text
Recorded downtime
delta = -2 hours
direction = improved

Failure count
delta = -1
direction = improved

MTTR
delta = -0.5 hour
direction = improved

MTBF
delta = +4.5 hours
direction = improved
```

---

## RBAC

Operational Trends is read-only.

Allowed authenticated roles:

```text
admin
manager
technician
operator
```

This follows the same read policy as other FactoryPulse analytics endpoints.

---

## Error Handling

The endpoint returns:

```text
404
```

when the production line does not exist.

It returns:

```text
422
```

when:

```text
end_at <= start_at
required dates are missing
current period lacks completed production runs
previous period lacks completed production runs
underlying Operational Intelligence cannot calculate the report
```

---

## Testing

Operational Trends is tested at three levels.

### Pure Trend Tests

Coverage includes:

```text
higher-is-better improvement
lower-is-better improvement
unchanged metrics
not-comparable null metrics
line-level trends
machine-level trends
zero-failure MTTR/MTBF semantics
```

### PostgreSQL Integration

A dedicated two-period scenario verifies:

```text
automatic previous-period derivation

previous downtime = 3h
current downtime = 1h

previous failures = 2
current failures = 1

previous MTTR = 1h
current MTTR = 0.5h

previous MTBF = 2.5h
current MTBF = 7h
```

and confirms every direction is correctly interpreted as improvement.

### API Tests

Coverage includes:

```text
period derivation
OEE trend
Availability trend
Performance trend
Quality trend
recorded downtime trend
failure-count trend
MTTR trend
MTBF trend
RBAC for all authenticated roles
missing production line
invalid date range
required query parameters
missing previous-period production data
```

---

## Regression Status

After Period-over-Period Operational Trends:

```text
267 tests passed
```

The complete FactoryPulse backend regression suite remained green.

---

# Operational Intelligence Milestone Summary

The completed Operational Intelligence milestone now answers five progressively deeper production questions.

```text
1. How is the production line performing?
   ↓
   OEE

2. Which machines are contributing the most operational burden?
   ↓
   Operational Impact

3. Which machine deserves attention first?
   ↓
   Explainable Operational Priority Ranking

4. Which recorded reasons explain its downtime?
   ↓
   Downtime Cause Intelligence

5. Is the line and machine reliability improving or worsening?
   ↓
   Period-over-Period Operational Trends
```

The resulting architecture is:

```text
Production Line
│
├── Production Runs
│      ↓
│     OEE
│
├── Downtime Events
│      ↓
│   Downtime Analytics
│      ↓
│   Cause Intelligence
│
└── Machines
       ↓
   Reliability Analytics
       │
       ├── Failure Count
       ├── MTTR
       ├── Operating Exposure
       └── MTBF
             ↓
     Operational Impact
             ↓
     Priority Ranking
             ↓
     Period Comparison
             ↓
      Operational Trends
```

The milestone remains intentionally deterministic and explainable.

FactoryPulse does not currently fabricate:

```text
AI health scores
verified root causes
exact machine production-loss attribution
business criticality scores
```

without sufficient supporting data.

This preserves the core design principle:

> Industrial analytics should only claim what the available data can actually support.
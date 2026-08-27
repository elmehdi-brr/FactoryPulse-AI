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
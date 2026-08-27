# Maintenance Effectiveness Analytics

## Overview

FactoryPulse AI now includes machine-level Maintenance Effectiveness Analytics.

This milestone connects maintenance activity, industrial alerts, machines, sensors, users, and maintenance lifecycle data to provide measurable maintenance-performance indicators.

The implementation includes:

- Strict maintenance vocabulary
- Database-level maintenance data integrity
- Maintenance lifecycle analytics
- Preventive vs corrective maintenance analysis
- Completion and verification rates
- Alert linkage analytics
- Technician assignment analytics
- Alert-to-maintenance response analytics
- Average, median, fastest, and slowest response times
- Machine-level reporting
- Date-range filtering
- RBAC-protected REST API
- Pure unit tests
- PostgreSQL integration tests
- API tests

The implementation intentionally avoids metrics that cannot yet be calculated reliably from the current data model.

---

## Maintenance Domain

Maintenance activity is represented by:

`MaintenanceRecord`

Important fields include:

- `machine_id`
- `alert_id`
- `performed_by_user_id`
- `maintenance_type`
- `description`
- `status`
- `performed_at`
- `created_at`

A maintenance record always belongs to a machine.

It can optionally:

- Reference an alert
- Reference the user who performed the intervention
- Record the timestamp at which the intervention was performed

---

## Maintenance Vocabulary

The maintenance domain now uses a controlled vocabulary.

### Maintenance Types

Supported values:

- `preventive`
- `corrective`

### Maintenance Statuses

Supported values:

- `planned`
- `in_progress`
- `completed`
- `verified`
- `cancelled`

Conceptual lifecycle:

`planned`

↓

`in_progress`

↓

`completed`

↓

`verified`

A maintenance intervention may instead become:

`cancelled`

`verified` is preserved as a distinct state rather than being converted to `completed`.

This allows FactoryPulse to distinguish between work that was completed and work that was subsequently verified.

---

## Data Integrity

Maintenance vocabulary is enforced at multiple layers.

### Pydantic

`app/schemas/maintenance_record.py`

Pydantic uses literal maintenance type and status values.

Invalid API payloads are rejected before reaching the database.

Examples:

`maintenance_type = "inspection"` → rejected

`status = "unknown"` → rejected

### SQLAlchemy Metadata

`app/models/maintenance_record.py`

The ORM metadata contains CHECK constraints matching the database migration.

This is important because the FactoryPulse test database is recreated using SQLAlchemy metadata.

### PostgreSQL

Alembic migration:

`08e0e906b398_enforce_maintenance_record_vocabulary.py`

adds:

`ck_maintenance_records_maintenance_type`

and:

`ck_maintenance_records_status`

The database therefore rejects invalid maintenance values even when application validation is bypassed.

The migration was verified through:

- Existing-data audit
- Upgrade
- Direct PostgreSQL constraint testing
- Downgrade
- Re-upgrade

The existing `corrective + verified` maintenance record remained valid.

---

## Maintenance Effectiveness Engine

Pure maintenance analytics are implemented in:

`app/maintenance/analytics.py`

The pure domain layer contains no FastAPI or SQLAlchemy dependencies.

Important objects include:

- `MaintenanceRecordSnapshot`
- `MaintenanceEffectivenessMetrics`
- `MaintenanceResponseObservation`
- `MaintenanceResponseMetrics`
- `MaintenanceAnalyticsError`

This keeps maintenance mathematics independently testable.

---

## Maintenance Activity Metrics

The first analytics group measures maintenance activity and lifecycle effectiveness.

### Total Maintenance Records

`total_records`

Represents the number of maintenance records included in the reporting population.

---

## Preventive vs Corrective Maintenance

FactoryPulse calculates:

- `preventive_count`
- `corrective_count`
- `preventive_share`

Formula:

`preventive_share = preventive_count / total_records`

When no maintenance records exist:

`preventive_share = null`

rather than `0`, because there is no maintenance population from which to calculate a proportion.

---

## Maintenance Lifecycle Counts

FactoryPulse reports:

- `planned_count`
- `in_progress_count`
- `completed_count`
- `verified_count`
- `cancelled_count`

Finished maintenance is defined as:

`finished_count = completed_count + verified_count`

Both completed and verified interventions therefore contribute to finished maintenance.

---

## Completion Rate

Completion rate measures the proportion of non-cancelled maintenance work that reached a finished state.

Formula:

`completion_rate = finished_count / non_cancelled_count`

where:

`non_cancelled_count = total_records - cancelled_count`

Cancelled work is deliberately excluded from the denominator.

Example:

- 1 completed
- 1 verified
- 1 planned
- 1 cancelled

Then:

`finished_count = 2`

`non_cancelled_count = 3`

`completion_rate = 2 / 3`

If all records are cancelled:

`completion_rate = null`

---

## Verification Rate

Verification rate measures how much finished maintenance reached the verified state.

Formula:

`verification_rate = verified_count / finished_count`

Example:

- Completed = 1
- Verified = 1

Then:

`finished_count = 2`

`verification_rate = 1 / 2`

If no finished maintenance exists:

`verification_rate = null`

---

## Alert Linkage Analytics

Maintenance records may optionally reference an industrial alert.

FactoryPulse calculates:

- `alert_linked_count`
- `alert_link_rate`

Formula:

`alert_link_rate = alert_linked_count / total_records`

This provides visibility into how much maintenance activity is directly connected to recorded alert events.

---

## Technician Assignment Analytics

Maintenance records may optionally identify the user who performed the work.

FactoryPulse calculates:

- `assigned_count`
- `assignment_rate`

Formula:

`assignment_rate = assigned_count / total_records`

This indicates how consistently maintenance interventions are associated with responsible personnel.

---

## Maintenance Reporting Period

Machine maintenance effectiveness supports optional:

- `start_at`
- `end_at`

For maintenance activity metrics, the reporting cohort is selected using:

`MaintenanceRecord.created_at`

This is deliberate.

`created_at` always exists, while `performed_at` can be `NULL` for planned or in-progress maintenance.

Using `created_at` therefore allows lifecycle analytics to include maintenance that has not yet been performed.

When both timestamps are supplied:

`end_at` must be later than `start_at`

Otherwise:

`422 Unprocessable Content`

is returned.

---

# Alert → Maintenance Response Analytics

## Objective

FactoryPulse also measures how effectively maintenance responds to machine alerts.

The response flow is:

`Machine`

↓

`Sensor`

↓

`Alert`

↓

`MaintenanceRecord`

This analysis answers questions such as:

- How many machine alerts received maintenance follow-up?
- How many alerts remain without a completed maintenance response?
- What percentage of alerts receive a response?
- How quickly does maintenance respond?
- What is the median response time?
- What are the fastest and slowest observed responses?

---

## Response Definition

A maintenance record qualifies as a response to an alert only when:

- It belongs to the target machine
- `alert_id` references the alert
- `performed_at IS NOT NULL`
- `status` is `completed` or `verified`

Records with the following statuses do not count as finished alert responses:

- `planned`
- `in_progress`
- `cancelled`

---

## Earliest Qualifying Response

One alert may have multiple maintenance records.

Example:

`Alert A`

- planned maintenance at +5 minutes
- completed maintenance at +30 minutes
- verified maintenance at +60 minutes

FactoryPulse counts this as:

`1 responded alert`

with:

`response time = 30 minutes`

The planned record is ignored because it is not a finished response.

The later verified record does not create another alert response.

The earliest qualifying completed/verified maintenance timestamp is used.

This prevents multiple maintenance records from artificially inflating the response count.

---

## Response Time

For a responded alert:

`response_time = earliest qualifying maintenance performed_at - alert created_at`

The result is exposed in seconds.

A zero-second response is valid.

A response timestamp earlier than the alert timestamp is rejected by the pure analytics engine as invalid data.

---

## Alert Response Metrics

FactoryPulse calculates:

- `total_alerts`
- `responded_alert_count`
- `unresponded_alert_count`
- `response_rate`
- `average_response_time_seconds`
- `median_response_time_seconds`
- `fastest_response_time_seconds`
- `slowest_response_time_seconds`

---

## Response Rate

Formula:

`response_rate = responded_alert_count / total_alerts`

Example:

- Total alerts = 3
- Responded = 2
- Unresponded = 1

Then:

`response_rate = 2 / 3`

If no alerts exist:

`response_rate = null`

rather than `0`.

A zero-percent response rate is reserved for the meaningful case where alerts exist but none received a qualifying response.

---

## Average Response Time

Formula:

`average response time = sum(response times) / responded alerts`

Only responded alerts participate in response-time statistics.

Unresponded alerts do not receive an artificial response duration.

---

## Median Response Time

FactoryPulse also calculates:

`median_response_time_seconds`

Median response time provides a measure less sensitive to unusually slow maintenance responses than the arithmetic average.

Example:

Response times:

- 10 minutes
- 50 minutes

Median:

`30 minutes`

---

## Fastest and Slowest Response

FactoryPulse reports:

- `fastest_response_time_seconds`
- `slowest_response_time_seconds`

When no alerts have qualifying responses, all response-time statistics are:

`null`

---

## Alert Reporting Cohort

Alert-response reporting uses:

`Alert.created_at`

for the requested date range.

This means the report asks:

> For alerts created during this reporting period, how effectively did maintenance respond?

Maintenance responses may occur after the alert creation timestamp.

This keeps the denominator and response population tied to the same alert cohort.

---

## Machine Isolation

Alerts are selected through:

`Machine → Sensor → Alert`

Only sensors belonging to the requested machine are included.

Maintenance responses are additionally restricted to:

`MaintenanceRecord.machine_id == target machine`

This prevents:

- Another machine's alert from entering the report
- Another machine's maintenance record from being treated as a response

---

## PostgreSQL Service Layer

Database-backed analytics are implemented in:

`app/services/maintenance_analytics_service.py`

Responsibilities include:

- Reporting-period validation
- Machine maintenance-record selection
- Machine filtering
- Maintenance `created_at` filtering
- Conversion to pure analytics snapshots
- Sensor-based machine alert selection
- Alert `created_at` filtering
- Loading qualifying maintenance responses
- Completed/verified filtering
- Earliest response selection per alert
- Including unresponded alerts
- Converting alerts into response observations
- Calling the pure analytics engine
- Translating domain errors into service-level errors

The service uses asynchronous SQLAlchemy with PostgreSQL.

---

## Maintenance Analytics API

Machine maintenance analytics are exposed through:

`GET /machines/{machine_id}/maintenance-analytics`

Optional parameters:

- `start_at`
- `end_at`

The endpoint combines:

1. Maintenance activity effectiveness
2. Alert-response effectiveness

into one machine-level maintenance analytics response.

---

## API Response

The response includes:

### Report Metadata

- `machine_id`
- `start_at`
- `end_at`

### Maintenance Activity

- `total_records`
- `preventive_count`
- `corrective_count`
- `preventive_share`

### Maintenance Lifecycle

- `planned_count`
- `in_progress_count`
- `completed_count`
- `verified_count`
- `cancelled_count`
- `finished_count`
- `completion_rate`
- `verification_rate`

### Traceability

- `alert_linked_count`
- `alert_link_rate`
- `assigned_count`
- `assignment_rate`

### Alert Response Effectiveness

- `total_alerts`
- `responded_alert_count`
- `unresponded_alert_count`
- `response_rate`
- `average_response_time_seconds`
- `median_response_time_seconds`
- `fastest_response_time_seconds`
- `slowest_response_time_seconds`

All duration values use seconds as the API base unit.

---

## API Behavior

Missing machine:

`404 Machine not found`

Invalid reporting period:

`422 end_at must be later than start_at`

Machine with no maintenance records and no alerts:

`200 OK`

with:

- Counts equal to `0`
- Rates requiring a population equal to `null`
- Response-time statistics equal to `null`

---

## RBAC

Maintenance analytics are read-only.

All authenticated FactoryPulse roles can access them:

- Admin
- Manager
- Technician
- Operator

Maintenance record writes remain protected by the technical-write RBAC policy.

Operators can read maintenance analytics but cannot create maintenance records.

---

# Testing Strategy

## Maintenance Schema Tests

`tests/test_maintenance_record_schema.py`

Coverage includes:

- Valid preventive maintenance
- Valid corrective maintenance
- Valid verified status
- Invalid maintenance type rejection
- Invalid maintenance status rejection
- Invalid update vocabulary rejection

---

## Maintenance CRUD / Integrity Tests

`tests/test_maintenance_records.py`

Coverage includes:

- Valid maintenance creation
- Invalid type → 422
- Invalid status → 422
- PATCH vocabulary validation
- Missing-machine handling
- Read RBAC
- Write RBAC
- PostgreSQL maintenance-type constraint
- PostgreSQL maintenance-status constraint

Direct database tests bypass FastAPI and Pydantic and verify PostgreSQL itself enforces maintenance vocabulary.

---

## Pure Maintenance Analytics Tests

`tests/test_maintenance_analytics.py`

Coverage includes:

- Preventive/corrective counts
- Preventive share
- Lifecycle counts
- Finished maintenance
- Completion rate
- Verification rate
- Alert linkage
- Assignment rate
- Empty maintenance history
- All-cancelled maintenance
- Invalid maintenance types
- Invalid maintenance statuses
- Alert response rate
- Average response time
- Median response time
- Fastest response time
- Slowest response time
- Alerts without maintenance
- Empty alert history
- Zero-time response
- Invalid response chronology

---

## PostgreSQL Analytics Tests

Database-backed tests verify:

### Maintenance Effectiveness

- Metric aggregation
- Machine isolation
- `created_at` reporting-period filtering
- Invalid date-range rejection

### Alert Response

- Machine → Sensor → Alert selection
- Responded vs unresponded alerts
- Completed/verified response filtering
- Planned maintenance ignored as response
- Earliest qualifying response selection
- Multiple maintenance records do not inflate alert count
- Machine isolation
- Alert `created_at` reporting-period filtering
- Average response time
- Median response time
- Fastest response time
- Slowest response time

---

## API Tests

Maintenance analytics API coverage includes:

- Full maintenance-effectiveness response
- Empty maintenance history
- Date-range filtering
- Alert response metrics
- Empty alert-response population
- Admin access
- Manager access
- Technician access
- Operator access
- Missing-machine handling
- Invalid reporting-period handling

Tests use:

- `pytest`
- `pytest-asyncio`
- `httpx.AsyncClient`
- FastAPI ASGI
- Real PostgreSQL test database

No Selenium or browser automation is used for these backend tests.

---

# Architecture

The maintenance activity flow is:

`MaintenanceRecord`

↓

`Maintenance Analytics Service`

↓

`MaintenanceRecordSnapshot`

↓

`Pure Maintenance Analytics Engine`

↓

`Lifecycle + Type + Traceability Metrics`

The alert-response flow is:

`Machine`

↓

`Sensor`

↓

`Alert`

↓

`Qualifying MaintenanceRecord`

↓

`Earliest Response Selection`

↓

`MaintenanceResponseObservation`

↓

`Pure Response Analytics Engine`

↓

`Response Rate + Response-Time Metrics`

Both flows are combined by:

`GET /machines/{machine_id}/maintenance-analytics`

---

# Current Limitations

The current maintenance analytics model intentionally does not calculate several metrics.

## Maintenance Duration

The model does not currently store:

- maintenance `started_at`
- maintenance `ended_at`

Therefore FactoryPulse does not claim to calculate:

- Average repair duration
- Technician working time
- Maintenance duration

`performed_at` is a single event timestamp and cannot truthfully represent duration.

---

## Maintenance Cost

The current model contains no maintenance-cost fields.

FactoryPulse therefore does not calculate:

- Cost per intervention
- Cost per machine
- Preventive vs corrective cost
- Maintenance ROI

---

## Direct Failure-to-Maintenance Link

`MaintenanceRecord` can reference an `Alert`, but it does not currently directly reference a `DowntimeEvent`.

Therefore advanced metrics such as:

- Failure → maintenance traceability
- Repeat failure after maintenance
- Reliability before vs after intervention
- Maintenance impact on MTBF
- Maintenance impact on MTTR

require additional domain modelling before they can be implemented reliably.

---

# Future Extensions

Possible future maintenance capabilities include:

- Maintenance start/end timestamps
- Maintenance duration
- Maintenance cost
- Parts and materials used
- Downtime-event linkage
- Work-order lifecycle
- Maintenance priority
- Failure mode classification
- Root-cause classification
- Technician workload analytics
- Preventive maintenance schedule compliance
- Maintenance backlog
- Mean response time trends
- Response SLA thresholds
- Maintenance effectiveness trends
- Failure recurrence after repair
- Reliability before vs after maintenance
- Preventive vs corrective cost comparison
- AI-assisted maintenance recommendations
- Prediction → Alert → Maintenance → Failure outcome traceability

These should be added only when the underlying data model can support them accurately.

---

# Maintenance Effectiveness Analytics Status

Maintenance domain integrity:

- Controlled maintenance types ✅
- Controlled lifecycle statuses ✅
- Pydantic validation ✅
- SQLAlchemy constraints ✅
- PostgreSQL CHECK constraints ✅
- Existing-data audit ✅
- Migration upgrade ✅
- Migration downgrade ✅
- Migration re-upgrade ✅
- Direct database constraint tests ✅

Maintenance activity analytics:

- Total maintenance records ✅
- Preventive count ✅
- Corrective count ✅
- Preventive share ✅
- Lifecycle counts ✅
- Finished interventions ✅
- Completion rate ✅
- Verification rate ✅
- Alert-link rate ✅
- Assignment rate ✅
- Machine filtering ✅
- Date-range filtering ✅

Alert response analytics:

- Machine alert cohort ✅
- Responded alerts ✅
- Unresponded alerts ✅
- Response rate ✅
- Earliest qualifying response ✅
- Average response time ✅
- Median response time ✅
- Fastest response time ✅
- Slowest response time ✅
- Machine isolation ✅
- Alert date-range filtering ✅

Backend delivery:

- Pure domain analytics ✅
- PostgreSQL service ✅
- REST API ✅
- RBAC ✅
- Unit tests ✅
- Integration tests ✅
- API tests ✅
- Full regression suite ✅
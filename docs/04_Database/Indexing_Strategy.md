# FactoryPulse AI — Indexing Strategy

## 1. Purpose

This document defines the PostgreSQL indexing strategy for the FactoryPulse AI MVP.

Its goals are to:

- Support frequent application queries
- Improve joins between related tables
- Retrieve recent sensor measurements efficiently
- Retrieve active alerts and maintenance tasks quickly
- Support prediction, notification and audit history
- Protect important uniqueness rules
- Avoid unnecessary indexes that would slow down inserts
- Provide a foundation for future performance tuning

Indexes will be created through Alembic migrations rather than manually in production databases.

---

## 2. Indexing Principles

FactoryPulse AI will follow these principles:

- Create indexes based on real query patterns
- Avoid indexing every column automatically
- Avoid duplicating indexes already created by primary-key or unique constraints
- Prioritize high-frequency filtering, joining and ordering operations
- Pay special attention to append-heavy tables such as `sensor_measurements`
- Use composite indexes when queries commonly filter by several columns together
- Use partial indexes for frequently accessed subsets of records
- Review indexes using PostgreSQL query plans after implementation
- Add advanced indexes only when actual usage justifies them

Indexes improve read performance but introduce costs:

- Additional disk usage
- Slower inserts
- Slower updates
- Additional database maintenance

This is especially important for sensor measurements because they will be inserted frequently.

---

## 3. PostgreSQL Index Type

The default index type for the MVP will be:

```text
B-tree
```

B-tree indexes are suitable for:

- Equality searches
- Range searches
- Sorting
- Timestamp queries
- Foreign-key lookups
- Composite filters

Examples:

```text
email = ?
machine_id = ?
recorded_at BETWEEN ? AND ?
status = ?
ORDER BY created_at DESC
```

Other index types such as GIN and BRIN will only be introduced when needed.

---

## 4. Index Naming Convention

Index names will follow this structure:

```text
ix_<table>_<column_or_purpose>
```

Examples:

```text
ix_users_role_id
ix_measurements_sensor_recorded
ix_alerts_machine_status_created
ix_notifications_user_unread
```

Unique indexes may use:

```text
uq_<table>_<column_or_purpose>
```

Examples:

```text
uq_users_email
uq_machine_assignments_user_machine
uq_model_versions_active_model
```

Names should remain descriptive and short enough for PostgreSQL identifier limits.

---

## 5. Automatically Created Indexes

PostgreSQL automatically creates indexes for:

- Primary keys
- Unique constraints

Therefore, additional duplicate indexes must not be created for these fields.

Existing primary-key indexes include:

```text
roles.id
users.id
machines.id
machine_assignments.id
sensors.id
sensor_measurements.id
model_versions.id
predictions.id
alerts.id
maintenance_tasks.id
maintenance_events.id
notifications.id
audit_logs.id
```

Existing unique constraints also provide indexes for:

```text
roles.name
users.email
machines.code
machine_assignments(user_id, machine_id)
sensors(machine_id, code)
model_versions(name, version)
```

---

## 6. Foreign-Key Indexing

PostgreSQL does not automatically create an index on every foreign-key column.

Frequently joined or filtered foreign keys should therefore receive indexes where the existing composite or unique indexes do not already support them.

Foreign-key indexes help with:

- Joining related entities
- Finding dependent records
- Validating parent-record changes
- Filtering by parent entity

However, foreign keys that are rarely queried may not require an immediate index.

---

## 7. Identity and Access Indexes

## 7.1 `roles`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (name)
```

No additional MVP index is required.

The table will contain only a small number of roles.

---

## 7.2 `users`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (email)
```

### Proposed index: users by role

```sql
CREATE INDEX ix_users_role_id
ON users (role_id);
```

Supports:

- Retrieving users belonging to a role
- Administrative user filtering
- Role-based reporting

Example query:

```sql
SELECT *
FROM users
WHERE role_id = :role_id;
```

### Optional future index: active users

```sql
CREATE INDEX ix_users_active
ON users (is_active)
WHERE is_active = TRUE;
```

This is not required initially because the user table is expected to remain relatively small.

---

## 8. Industrial Asset Indexes

## 8.1 `machines`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (code)
```

### Optional index: machine status

```sql
CREATE INDEX ix_machines_status
ON machines (status);
```

Supports:

- Filtering operational machines
- Finding critical or offline machines
- Dashboard status summaries

This index may be deferred until the number of machines becomes large enough to justify it.

A status column has relatively few possible values, so indexing it alone may provide limited value on a small table.

---

## 8.2 `machine_assignments`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (user_id, machine_id)
```

The unique index already supports queries beginning with `user_id`.

Example:

```sql
SELECT machine_id
FROM machine_assignments
WHERE user_id = :user_id;
```

### Proposed reverse-lookup index

```sql
CREATE INDEX ix_machine_assignments_machine_user
ON machine_assignments (machine_id, user_id);
```

Supports:

- Retrieving users assigned to a machine
- Finding operators or engineers responsible for a machine
- Authorization and assignment-management operations

Example query:

```sql
SELECT user_id
FROM machine_assignments
WHERE machine_id = :machine_id;
```

### Optional index: creator

```sql
CREATE INDEX ix_machine_assignments_assigned_by
ON machine_assignments (assigned_by);
```

This may be deferred because assignment history is more likely to be accessed through audit logs.

---

## 8.3 `sensors`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (machine_id, code)
```

The unique index supports retrieving sensors for one machine because `machine_id` is the leading column.

Example query:

```sql
SELECT *
FROM sensors
WHERE machine_id = :machine_id;
```

### Optional index: sensor status

```sql
CREATE INDEX ix_sensors_status
ON sensors (status);
```

This may be added later if the application frequently retrieves all faulty, inactive or retired sensors across machines.

No additional mandatory MVP index is required.

---

## 9. Sensor Measurement Indexes

The `sensor_measurements` table requires the most careful indexing because it will receive frequent inserts and contain the largest number of records.

## 9.1 Primary measurement-history index

```sql
CREATE INDEX ix_measurements_sensor_recorded
ON sensor_measurements (sensor_id, recorded_at DESC);
```

Supports:

- Retrieving recent measurements for a sensor
- Retrieving measurements within a time range
- Displaying sensor-history charts
- Preparing machine-learning input windows

Example query:

```sql
SELECT *
FROM sensor_measurements
WHERE sensor_id = :sensor_id
  AND recorded_at BETWEEN :start_time AND :end_time
ORDER BY recorded_at DESC;
```

This is the most important non-unique index in the MVP database.

---

## 9.2 Global timestamp index

A global timestamp index may support:

- Recent ingestion monitoring
- Time-based cleanup
- Data-retention operations
- Cross-sensor reporting

Possible index:

```sql
CREATE INDEX ix_measurements_recorded_at
ON sensor_measurements (recorded_at DESC);
```

This index should not be added immediately unless the application requires frequent queries across all sensors by time.

The composite index on `(sensor_id, recorded_at)` should be implemented first.

---

## 9.3 Quality-status index

An index on `quality_status` alone is not recommended initially because:

- The column has few distinct values
- Most measurements will likely use the same value
- It would increase insert cost
- Queries will normally combine quality with sensor and time

A future partial index could be considered for problematic measurements:

```sql
CREATE INDEX ix_measurements_invalid_quality
ON sensor_measurements (recorded_at DESC)
WHERE quality_status IN ('suspect', 'invalid', 'missing');
```

This should only be added if the platform frequently reviews invalid or suspicious data.

---

## 9.4 Future BRIN index

If the measurement table becomes very large and rows are physically inserted in timestamp order, a BRIN index may be considered:

```sql
CREATE INDEX ix_measurements_recorded_brin
ON sensor_measurements
USING BRIN (recorded_at);
```

BRIN indexes are small and useful for very large naturally ordered tables.

They are not required for the MVP.

---

## 10. Machine-Learning Indexes

## 10.1 `model_versions`

Existing indexes:

```text
PRIMARY KEY (id)
UNIQUE (name, version)
```

### Partial unique index for active models

```sql
CREATE UNIQUE INDEX uq_model_versions_active_model
ON model_versions (name, model_type)
WHERE is_active = TRUE;
```

Supports the rule:

> Only one active version should exist for the same model name and model type.

This prevents accidental activation of several competing versions.

Example:

```text
Name: pump_failure_predictor
Type: failure_prediction
Active versions allowed: one
```

### Optional model-type index

```sql
CREATE INDEX ix_model_versions_type
ON model_versions (model_type);
```

This is not initially necessary because the table will remain small.

---

## 10.2 `predictions`

### Proposed machine-history index

```sql
CREATE INDEX ix_predictions_machine_predicted
ON predictions (machine_id, predicted_at DESC);
```

Supports:

- Retrieving the latest prediction for a machine
- Displaying prediction history
- Building machine-health dashboards
- Finding predictions within a time range

Example query:

```sql
SELECT *
FROM predictions
WHERE machine_id = :machine_id
ORDER BY predicted_at DESC
LIMIT 20;
```

### Proposed model-version index

```sql
CREATE INDEX ix_predictions_model_version
ON predictions (model_version_id);
```

Supports:

- Reviewing predictions produced by a model
- Comparing model-version usage
- Investigating model behaviour

### Optional high-risk partial index

```sql
CREATE INDEX ix_predictions_high_risk
ON predictions (machine_id, predicted_at DESC)
WHERE risk_level IN ('high', 'critical');
```

This may be useful if dashboards and alert workflows frequently query only serious predictions.

It should be added after confirming the real query pattern.

---

## 11. Alert Indexes

Alerts will frequently be retrieved by machine, status and creation time.

## 11.1 Machine alert-history index

```sql
CREATE INDEX ix_alerts_machine_created
ON alerts (machine_id, created_at DESC);
```

Supports:

- Retrieving the alert history of a machine
- Displaying recent alerts
- Calculating alert statistics

---

## 11.2 Active-alert index

```sql
CREATE INDEX ix_alerts_machine_active
ON alerts (machine_id, severity, created_at DESC)
WHERE status IN ('open', 'acknowledged', 'in_progress');
```

Supports:

- Displaying active alerts for a machine
- Prioritizing active alerts by severity
- Avoiding scanning resolved and closed alerts

Example query:

```sql
SELECT *
FROM alerts
WHERE machine_id = :machine_id
  AND status IN ('open', 'acknowledged', 'in_progress')
ORDER BY created_at DESC;
```

---

## 11.3 Prediction-reference index

```sql
CREATE INDEX ix_alerts_prediction_id
ON alerts (prediction_id)
WHERE prediction_id IS NOT NULL;
```

Supports:

- Finding alerts generated by a prediction
- Investigating prediction-to-alert workflows

---

## 11.4 Sensor-reference index

```sql
CREATE INDEX ix_alerts_sensor_id
ON alerts (sensor_id)
WHERE sensor_id IS NOT NULL;
```

Supports:

- Retrieving alerts associated with a sensor
- Reviewing recurring sensor problems

---

## 12. Maintenance Indexes

## 12.1 Assigned-user task index

```sql
CREATE INDEX ix_maintenance_tasks_assignee_status_due
ON maintenance_tasks (
    assigned_user_id,
    status,
    due_date
);
```

Supports:

- Showing an engineer's assigned tasks
- Filtering tasks by workflow state
- Ordering or identifying tasks by deadline
- Finding overdue tasks

Example query:

```sql
SELECT *
FROM maintenance_tasks
WHERE assigned_user_id = :user_id
  AND status IN ('assigned', 'in_progress', 'blocked')
ORDER BY due_date;
```

---

## 12.2 Machine maintenance-history index

```sql
CREATE INDEX ix_maintenance_tasks_machine_created
ON maintenance_tasks (machine_id, created_at DESC);
```

Supports:

- Retrieving maintenance history for a machine
- Displaying recent interventions
- Reporting machine-maintenance frequency

---

## 12.3 Alert-source index

```sql
CREATE INDEX ix_maintenance_tasks_source_alert
ON maintenance_tasks (source_alert_id)
WHERE source_alert_id IS NOT NULL;
```

Supports:

- Finding tasks created from an alert
- Preventing or detecting duplicate task creation
- Tracing alert-to-maintenance workflows

---

## 12.4 Maintenance-event history index

```sql
CREATE INDEX ix_maintenance_events_task_created
ON maintenance_events (
    maintenance_task_id,
    created_at
);
```

Supports:

- Retrieving the chronological history of a maintenance task
- Displaying the intervention timeline

Example query:

```sql
SELECT *
FROM maintenance_events
WHERE maintenance_task_id = :task_id
ORDER BY created_at;
```

---

## 13. Notification Indexes

## 13.1 User notification-history index

```sql
CREATE INDEX ix_notifications_user_created
ON notifications (user_id, created_at DESC);
```

Supports:

- Retrieving recent notifications for a user
- Displaying notification history

---

## 13.2 Unread-notification partial index

```sql
CREATE INDEX ix_notifications_user_unread
ON notifications (user_id, created_at DESC)
WHERE is_read = FALSE;
```

Supports:

- Retrieving unread notifications
- Calculating unread notification counts
- Displaying notification badges

Example query:

```sql
SELECT *
FROM notifications
WHERE user_id = :user_id
  AND is_read = FALSE
ORDER BY created_at DESC;
```

---

## 13.3 Related-resource indexes

Possible indexes:

```sql
CREATE INDEX ix_notifications_alert_id
ON notifications (alert_id)
WHERE alert_id IS NOT NULL;
```

```sql
CREATE INDEX ix_notifications_maintenance_task_id
ON notifications (maintenance_task_id)
WHERE maintenance_task_id IS NOT NULL;
```

These may be added if the application frequently retrieves notifications through their related alerts or maintenance tasks.

They are optional for the first implementation.

---

## 14. Audit Indexes

Audit logs may be queried by actor, resource and time.

## 14.1 Actor-history index

```sql
CREATE INDEX ix_audit_logs_actor_created
ON audit_logs (actor_user_id, created_at DESC)
WHERE actor_user_id IS NOT NULL;
```

Supports:

- Reviewing actions performed by a user
- Investigating suspicious activity
- Administrative audit views

---

## 14.2 Resource-history index

```sql
CREATE INDEX ix_audit_logs_resource_created
ON audit_logs (
    resource_type,
    resource_id,
    created_at DESC
);
```

Supports:

- Retrieving the complete audit history of a record
- Reviewing changes to machines, sensors, alerts or users

Example query:

```sql
SELECT *
FROM audit_logs
WHERE resource_type = 'machine'
  AND resource_id = :machine_id
ORDER BY created_at DESC;
```

---

## 14.3 Global timestamp index

A global timestamp index may be useful for:

- Recent audit-event monitoring
- Security investigation
- Retention and archival processes

Possible index:

```sql
CREATE INDEX ix_audit_logs_created_at
ON audit_logs (created_at DESC);
```

It may be deferred until audit-log volume becomes significant.

---

## 15. JSONB Indexing

The MVP includes several JSONB fields:

```text
model_versions.metrics
model_versions.model_metadata
predictions.explanation_data
audit_logs.previous_values
audit_logs.new_values
```

GIN indexes will not be created initially.

Example future GIN index:

```sql
CREATE INDEX ix_predictions_explanation_gin
ON predictions
USING GIN (explanation_data);
```

A JSONB index should only be added when the application frequently searches inside a JSON document.

For example:

```sql
WHERE explanation_data @> '{"feature": "vibration"}'
```

The initial application will normally retrieve JSONB data through the parent record rather than search inside it.

---

## 16. Text Search Indexing

The MVP will not initially use full-text search.

Fields such as:

```text
machines.name
alerts.title
maintenance_tasks.title
```

may initially use normal filtering or case-insensitive matching.

Full-text or trigram indexes may be introduced later if search becomes an important feature.

Possible future extension:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Possible future index:

```sql
CREATE INDEX ix_machines_name_trgm
ON machines
USING GIN (name gin_trgm_ops);
```

This is outside the first MVP implementation.

---

## 17. Initial Mandatory Indexes

The first database migration should include these non-automatic indexes:

```text
ix_users_role_id
ix_machine_assignments_machine_user
ix_measurements_sensor_recorded
uq_model_versions_active_model
ix_predictions_machine_predicted
ix_predictions_model_version
ix_alerts_machine_created
ix_alerts_machine_active
ix_maintenance_tasks_assignee_status_due
ix_maintenance_tasks_machine_created
ix_maintenance_events_task_created
ix_notifications_user_created
ix_notifications_user_unread
ix_audit_logs_actor_created
ix_audit_logs_resource_created
```

Indexes generated automatically by primary keys and unique constraints are not repeated in this list.

---

## 18. Deferred Indexes

The following indexes should be added only when real application queries justify them:

```text
ix_users_active
ix_machines_status
ix_sensors_status
ix_measurements_recorded_at
ix_measurements_invalid_quality
ix_measurements_recorded_brin
ix_model_versions_type
ix_predictions_high_risk
ix_notifications_alert_id
ix_notifications_maintenance_task_id
ix_audit_logs_created_at
JSONB GIN indexes
Full-text or trigram indexes
```

Deferring them helps avoid premature optimization.

---

## 19. Query Validation

After implementation, important queries should be reviewed using:

```sql
EXPLAIN
```

or:

```sql
EXPLAIN ANALYZE
```

These tools show:

- Whether PostgreSQL uses an index
- How many rows are scanned
- Join strategies
- Sorting operations
- Estimated and actual execution time

Example:

```sql
EXPLAIN ANALYZE
SELECT *
FROM sensor_measurements
WHERE sensor_id = :sensor_id
ORDER BY recorded_at DESC
LIMIT 100;
```

The goal is to verify that PostgreSQL uses:

```text
ix_measurements_sensor_recorded
```

Performance decisions should be based on evidence rather than assumptions.

---

## 20. Index Maintenance

PostgreSQL automatically maintains indexes as records change.

The database should also maintain query-planning statistics using:

```text
ANALYZE
```

PostgreSQL normally performs this automatically through autovacuum.

Future production monitoring may review:

- Index size
- Index usage
- Sequential scans
- Insert performance
- Dead tuples
- Table growth
- Unused indexes

Unused indexes may be removed if they create write overhead without improving important queries.

---

## 21. Sensor-Ingestion Performance

Sensor ingestion is write-heavy.

To protect ingestion performance:

- Keep the number of measurement indexes limited
- Implement `(sensor_id, recorded_at)` first
- Avoid indexing `value`
- Avoid indexing `quality_status` alone
- Avoid unnecessary JSONB fields in the measurement table
- Insert measurements in batches when appropriate
- Use prepared statements or efficient ORM operations
- Monitor query and insert performance
- Introduce partitioning only after measuring real growth

The MVP should remain simple until actual data volume demonstrates a need for more advanced techniques.

---

## 22. Pagination Strategy

Large history endpoints should not return all records at once.

Examples include:

- Sensor measurements
- Predictions
- Alerts
- Maintenance events
- Notifications
- Audit logs

The Backend API should use pagination.

For time-ordered data, cursor-based pagination may use:

```text
created_at
recorded_at
predicted_at
id
```

Example concept:

```sql
WHERE recorded_at < :cursor_time
ORDER BY recorded_at DESC
LIMIT 100;
```

The indexes defined in this document support this access pattern.

---

## 23. Review Triggers

The indexing strategy should be reviewed when:

- Sensor-ingestion volume increases significantly
- Queries become slow
- Tables contain large numbers of rows
- New filters or reports are introduced
- Search capabilities are added
- Data-retention processes are introduced
- TimescaleDB or partitioning is considered
- The system moves to production
- Multiple Backend API instances are deployed

Any new index should identify the query it is intended to support.

---

## 24. Related Documents

- [[04_Database/Database_Overview|Database Overview]]
- [[04_Database/Entity_Relationship_Diagram|Entity Relationship Diagram]]
- [[04_Database/Database_Schema|Database Schema]]
- [[04_Database/Data_Dictionary|Data Dictionary]]
- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[02_Requirements/Software_Requirements_Specification|Software Requirements Specification]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
- [[Migration_and_Seed_Strategy]]
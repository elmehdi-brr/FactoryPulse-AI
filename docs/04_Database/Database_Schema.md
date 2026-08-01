 # FactoryPulse AI — Database Schema

## 1. Purpose

This document defines the logical PostgreSQL schema for the FactoryPulse AI MVP.

It specifies:

- The thirteen database tables
- Column names
- PostgreSQL data types
- Required and optional values
- Primary keys
- Foreign keys
- Unique constraints
- Default values
- Check constraints
- Foreign-key deletion behaviour
- Important cross-field integrity rules

This document is the blueprint that will later be implemented using SQLAlchemy models and Alembic migrations.

---

## 2. Schema Conventions

### 2.1 Primary Keys

Main entities use PostgreSQL UUID primary keys.

```text
UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

The `gen_random_uuid()` function is provided by PostgreSQL's `pgcrypto` extension.

The initial migration should enable it using:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

---

### 2.2 Timestamps

Timestamp columns use:

```text
TIMESTAMPTZ
```

All timestamps should be stored in UTC.

Common defaults:

```text
created_at DEFAULT CURRENT_TIMESTAMP
updated_at DEFAULT CURRENT_TIMESTAMP
```

The Backend API or database logic must update `updated_at` whenever a record changes.

---

### 2.3 Controlled Values

Important statuses and categories will initially use:

```text
VARCHAR + CHECK constraint
```

This approach is preferred over PostgreSQL native enums for the MVP because controlled values can be modified more easily through database migrations.

Application-level Python enums should use the same values.

---

### 2.4 Email Addresses

Email addresses should be:

- Trimmed
- Converted to lowercase before storage
- Validated by the Backend API
- Protected by a unique database constraint

---

### 2.5 Monetary and Sensor Values

Sensor and model values use fixed-precision numeric types rather than floating-point types where predictable precision is useful.

Typical type:

```text
NUMERIC(18, 6)
```

Probabilities use:

```text
NUMERIC(7, 6)
```

This supports values between `0.000000` and `1.000000`.

---

## 3. Identity and Access Tables

## 3.1 `roles`

Stores the supported FactoryPulse AI user roles.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `name` | `VARCHAR(50)` | No | — | Unique role name |
| `description` | `TEXT` | Yes | `NULL` | Human-readable role description |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Record creation time |

### Primary key

```text
PRIMARY KEY (id)
```

### Unique constraints

```text
UNIQUE (name)
```

### Allowed initial values

```text
administrator
plant_manager
maintenance_engineer
machine_operator
```

### Check constraints

```text
name IN (
    'administrator',
    'plant_manager',
    'maintenance_engineer',
    'machine_operator'
)
```

### Deletion behaviour

A role must not be deleted while users reference it.

```text
users.role_id → roles.id ON DELETE RESTRICT
```

---

## 3.2 `users`

Stores FactoryPulse AI user accounts.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `role_id` | `UUID` | No | — | User's assigned role |
| `first_name` | `VARCHAR(100)` | No | — | User's first name |
| `last_name` | `VARCHAR(100)` | No | — | User's last name |
| `email` | `VARCHAR(254)` | No | — | Normalized login email |
| `password_hash` | `VARCHAR(255)` | No | — | Secure password hash |
| `is_active` | `BOOLEAN` | No | `TRUE` | Whether login is allowed |
| `last_login_at` | `TIMESTAMPTZ` | Yes | `NULL` | Most recent successful login |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Account creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last account update |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign key

```text
FOREIGN KEY (role_id)
REFERENCES roles(id)
ON DELETE RESTRICT
```

### Unique constraints

```text
UNIQUE (email)
```

### Check constraints

```text
email = LOWER(email)
```

```text
LENGTH(TRIM(first_name)) > 0
```

```text
LENGTH(TRIM(last_name)) > 0
```

### Important rules

- Passwords must never be stored in plain text.
- Users should normally be deactivated instead of deleted.
- Changing a user's role should create an audit record.

---

## 4. Industrial Asset Tables

## 4.1 `machines`

Stores industrial machines monitored by FactoryPulse AI.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `code` | `VARCHAR(50)` | No | — | Unique machine identifier |
| `name` | `VARCHAR(150)` | No | — | Machine display name |
| `description` | `TEXT` | Yes | `NULL` | Machine description |
| `location` | `VARCHAR(255)` | Yes | `NULL` | Factory area or location |
| `manufacturer` | `VARCHAR(150)` | Yes | `NULL` | Equipment manufacturer |
| `model` | `VARCHAR(150)` | Yes | `NULL` | Manufacturer model |
| `installation_date` | `DATE` | Yes | `NULL` | Machine installation date |
| `status` | `VARCHAR(30)` | No | `'operational'` | Current operational status |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update time |

### Primary key

```text
PRIMARY KEY (id)
```

### Unique constraints

```text
UNIQUE (code)
```

### Allowed status values

```text
operational
warning
critical
maintenance
offline
decommissioned
```

### Check constraints

```text
status IN (
    'operational',
    'warning',
    'critical',
    'maintenance',
    'offline',
    'decommissioned'
)
```

```text
LENGTH(TRIM(code)) > 0
```

```text
LENGTH(TRIM(name)) > 0
```

### Important rules

- Machine codes should be normalized consistently.
- Machines with historical information should be marked as `decommissioned` rather than deleted.
- Machine status may be changed by monitoring, maintenance or authorized users.

---

## 4.2 `machine_assignments`

Creates a many-to-many relationship between users and machines.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `user_id` | `UUID` | No | — | Assigned user |
| `machine_id` | `UUID` | No | — | Assigned machine |
| `assignment_type` | `VARCHAR(30)` | No | — | Purpose of the assignment |
| `assigned_by` | `UUID` | Yes | `NULL` | User who created the assignment |
| `assigned_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Assignment creation time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (machine_id)
REFERENCES machines(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (assigned_by)
REFERENCES users(id)
ON DELETE SET NULL
```

### Unique constraints

```text
UNIQUE (user_id, machine_id)
```

### Allowed assignment types

```text
operation
maintenance
supervision
```

### Check constraints

```text
assignment_type IN (
    'operation',
    'maintenance',
    'supervision'
)
```

### Important rules

- Duplicate assignments between the same user and machine are not allowed.
- The Backend API should verify that assignment type is compatible with the user's role.
- Removing an assignment should create an audit record.

---

## 4.3 `sensors`

Stores sensors attached to machines.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `machine_id` | `UUID` | No | — | Machine containing the sensor |
| `code` | `VARCHAR(50)` | No | — | Sensor code within the machine |
| `name` | `VARCHAR(150)` | No | — | Sensor display name |
| `sensor_type` | `VARCHAR(50)` | No | — | Measurement category |
| `measurement_unit` | `VARCHAR(30)` | No | — | Unit used by the sensor |
| `warning_min` | `NUMERIC(18,6)` | Yes | `NULL` | Lower warning threshold |
| `warning_max` | `NUMERIC(18,6)` | Yes | `NULL` | Upper warning threshold |
| `critical_min` | `NUMERIC(18,6)` | Yes | `NULL` | Lower critical threshold |
| `critical_max` | `NUMERIC(18,6)` | Yes | `NULL` | Upper critical threshold |
| `status` | `VARCHAR(30)` | No | `'active'` | Sensor operational status |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign key

```text
FOREIGN KEY (machine_id)
REFERENCES machines(id)
ON DELETE RESTRICT
```

### Unique constraints

```text
UNIQUE (machine_id, code)
```

### Allowed sensor types

Initial values may include:

```text
temperature
pressure
vibration
rotational_speed
voltage
current
flow_rate
```

### Allowed sensor statuses

```text
active
inactive
faulty
maintenance
retired
```

### Check constraints

```text
status IN (
    'active',
    'inactive',
    'faulty',
    'maintenance',
    'retired'
)
```

```text
warning_min IS NULL
OR warning_max IS NULL
OR warning_min <= warning_max
```

```text
critical_min IS NULL
OR warning_min IS NULL
OR critical_min <= warning_min
```

```text
critical_max IS NULL
OR warning_max IS NULL
OR warning_max <= critical_max
```

### Important rules

- A sensor must belong to exactly one machine.
- Historical sensors should normally be marked as `retired`.
- Sensor threshold changes should be recorded in audit logs.

---

## 5. Sensor Data Table

## 5.1 `sensor_measurements`

Stores individual sensor measurements.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `sensor_id` | `UUID` | No | — | Sensor that produced the value |
| `value` | `NUMERIC(18,6)` | No | — | Recorded sensor value |
| `quality_status` | `VARCHAR(30)` | No | `'valid'` | Data-quality classification |
| `recorded_at` | `TIMESTAMPTZ` | No | — | Time the sensor produced the value |
| `received_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Time the platform received the value |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign key

```text
FOREIGN KEY (sensor_id)
REFERENCES sensors(id)
ON DELETE RESTRICT
```

### Allowed quality values

```text
valid
suspect
invalid
missing
simulated
```

### Check constraints

```text
quality_status IN (
    'valid',
    'suspect',
    'invalid',
    'missing',
    'simulated'
)
```

```text
recorded_at <= received_at + INTERVAL '5 minutes'
```

The small tolerance permits minor clock differences between the simulator and the Backend API.

### Important rules

- This table is expected to receive frequent inserts.
- Stored measurement records should normally not be modified.
- Duplicate measurements may later be detected through an ingestion identifier or timestamp strategy.
- Measurement indexing will be defined in `Indexing_Strategy.md`.

---

## 6. Artificial Intelligence Tables

## 6.1 `model_versions`

Stores metadata about trained machine-learning models.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `name` | `VARCHAR(150)` | No | — | Model name |
| `version` | `VARCHAR(50)` | No | — | Model version identifier |
| `model_type` | `VARCHAR(50)` | No | — | Model purpose |
| `file_path` | `VARCHAR(500)` | No | — | Path to the model artifact |
| `metrics` | `JSONB` | Yes | `NULL` | Evaluation metrics |
| `model_metadata` | `JSONB` | Yes | `NULL` | Additional model information |
| `is_active` | `BOOLEAN` | No | `FALSE` | Whether the version is active |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Version registration time |

### Primary key

```text
PRIMARY KEY (id)
```

### Unique constraints

```text
UNIQUE (name, version)
```

### Allowed model types

```text
anomaly_detection
failure_prediction
combined
```

### Check constraints

```text
model_type IN (
    'anomaly_detection',
    'failure_prediction',
    'combined'
)
```

### Important rules

- Model files are not stored directly in PostgreSQL.
- A model record stores only metadata and artifact location.
- The ML Service must confirm that the referenced model artifact exists.
- The application should normally have only one active version per model name and model type.
- Enforcing one active version may require a partial unique index.

---

## 6.2 `predictions`

Stores anomaly-detection and failure-risk results.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `machine_id` | `UUID` | No | — | Evaluated machine |
| `model_version_id` | `UUID` | No | — | Model that produced the result |
| `prediction_type` | `VARCHAR(30)` | No | — | Type of prediction |
| `is_anomaly` | `BOOLEAN` | Yes | `NULL` | Anomaly classification |
| `anomaly_score` | `NUMERIC(18,6)` | Yes | `NULL` | Model-specific anomaly score |
| `failure_probability` | `NUMERIC(7,6)` | Yes | `NULL` | Failure probability from 0 to 1 |
| `risk_level` | `VARCHAR(20)` | No | — | Classified risk level |
| `explanation_data` | `JSONB` | Yes | `NULL` | Structured prediction explanation |
| `input_window_start` | `TIMESTAMPTZ` | Yes | `NULL` | Start of evaluated measurement window |
| `input_window_end` | `TIMESTAMPTZ` | Yes | `NULL` | End of evaluated measurement window |
| `predicted_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Prediction generation time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (machine_id)
REFERENCES machines(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (model_version_id)
REFERENCES model_versions(id)
ON DELETE RESTRICT
```

### Allowed prediction types

```text
anomaly
failure_risk
combined
```

### Allowed risk levels

```text
low
medium
high
critical
```

### Check constraints

```text
prediction_type IN (
    'anomaly',
    'failure_risk',
    'combined'
)
```

```text
risk_level IN (
    'low',
    'medium',
    'high',
    'critical'
)
```

```text
failure_probability IS NULL
OR (
    failure_probability >= 0
    AND failure_probability <= 1
)
```

```text
input_window_start IS NULL
OR input_window_end IS NULL
OR input_window_start <= input_window_end
```

```text
prediction_type <> 'anomaly'
OR is_anomaly IS NOT NULL
```

```text
prediction_type <> 'failure_risk'
OR failure_probability IS NOT NULL
```

```text
prediction_type <> 'combined'
OR (
    is_anomaly IS NOT NULL
    AND failure_probability IS NOT NULL
)
```

### Important rules

- Every prediction must identify its machine and model version.
- Prediction results should remain immutable after creation.
- Explainability data may contain feature contributions and model interpretation details.
- Risk classification logic should be consistent across the ML Service and Backend API.

---

## 7. Alert Table

## 7.1 `alerts`

Stores threshold, AI-generated and manually reported alerts.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `machine_id` | `UUID` | No | — | Machine concerned by the alert |
| `sensor_id` | `UUID` | Yes | `NULL` | Related sensor |
| `prediction_id` | `UUID` | Yes | `NULL` | Related prediction |
| `alert_type` | `VARCHAR(30)` | No | — | Source or category |
| `severity` | `VARCHAR(20)` | No | — | Alert importance |
| `status` | `VARCHAR(30)` | No | `'open'` | Alert workflow state |
| `title` | `VARCHAR(200)` | No | — | Short alert title |
| `message` | `TEXT` | No | — | Detailed alert information |
| `acknowledged_by` | `UUID` | Yes | `NULL` | User who acknowledged it |
| `resolved_by` | `UUID` | Yes | `NULL` | User who resolved it |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Alert creation time |
| `acknowledged_at` | `TIMESTAMPTZ` | Yes | `NULL` | Acknowledgement time |
| `resolved_at` | `TIMESTAMPTZ` | Yes | `NULL` | Resolution time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (machine_id)
REFERENCES machines(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (sensor_id)
REFERENCES sensors(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (prediction_id)
REFERENCES predictions(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (acknowledged_by)
REFERENCES users(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (resolved_by)
REFERENCES users(id)
ON DELETE SET NULL
```

### Allowed alert types

```text
threshold
anomaly
failure_risk
manual
system
```

### Allowed severity values

```text
info
warning
high
critical
```

### Allowed status values

```text
open
acknowledged
in_progress
resolved
closed
```

### Check constraints

```text
alert_type IN (
    'threshold',
    'anomaly',
    'failure_risk',
    'manual',
    'system'
)
```

```text
severity IN (
    'info',
    'warning',
    'high',
    'critical'
)
```

```text
status IN (
    'open',
    'acknowledged',
    'in_progress',
    'resolved',
    'closed'
)
```

```text
status NOT IN ('acknowledged', 'in_progress', 'resolved', 'closed')
OR acknowledged_at IS NOT NULL
```

```text
status NOT IN ('resolved', 'closed')
OR resolved_at IS NOT NULL
```

```text
acknowledged_at IS NULL
OR acknowledged_at >= created_at
```

```text
resolved_at IS NULL
OR resolved_at >= created_at
```

### Important rules

- Every alert belongs to one machine.
- Threshold alerts should normally reference a sensor.
- AI alerts should normally reference a prediction.
- Manual alerts may reference only a machine.
- Duplicate-alert prevention will be handled by the Backend API and indexing strategy.

---

## 8. Maintenance Tables

## 8.1 `maintenance_tasks`

Stores maintenance work associated with machines.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `machine_id` | `UUID` | No | — | Machine requiring maintenance |
| `source_alert_id` | `UUID` | Yes | `NULL` | Alert that generated the task |
| `assigned_user_id` | `UUID` | Yes | `NULL` | Assigned Maintenance Engineer |
| `created_by` | `UUID` | Yes | `NULL` | User who created the task |
| `title` | `VARCHAR(200)` | No | — | Task title |
| `description` | `TEXT` | Yes | `NULL` | Detailed work description |
| `priority` | `VARCHAR(20)` | No | `'medium'` | Task importance |
| `status` | `VARCHAR(30)` | No | `'open'` | Workflow state |
| `due_date` | `TIMESTAMPTZ` | Yes | `NULL` | Planned completion deadline |
| `started_at` | `TIMESTAMPTZ` | Yes | `NULL` | Work start time |
| `completed_at` | `TIMESTAMPTZ` | Yes | `NULL` | Work completion time |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Task creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last task update |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (machine_id)
REFERENCES machines(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (source_alert_id)
REFERENCES alerts(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (assigned_user_id)
REFERENCES users(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (created_by)
REFERENCES users(id)
ON DELETE SET NULL
```

### Allowed priority values

```text
low
medium
high
critical
```

### Allowed status values

```text
open
assigned
in_progress
blocked
completed
cancelled
```

### Check constraints

```text
priority IN (
    'low',
    'medium',
    'high',
    'critical'
)
```

```text
status IN (
    'open',
    'assigned',
    'in_progress',
    'blocked',
    'completed',
    'cancelled'
)
```

```text
status <> 'assigned'
OR assigned_user_id IS NOT NULL
```

```text
status NOT IN ('in_progress', 'blocked', 'completed')
OR started_at IS NOT NULL
```

```text
status <> 'completed'
OR completed_at IS NOT NULL
```

```text
started_at IS NULL
OR started_at >= created_at
```

```text
completed_at IS NULL
OR completed_at >= created_at
```

```text
completed_at IS NULL
OR started_at IS NULL
OR completed_at >= started_at
```

### Important rules

- Every task belongs to one machine.
- Tasks may be created manually or from an alert.
- Assigned users should normally have the Maintenance Engineer role.
- Every important task-state change should create a maintenance event and audit record.

---

## 8.2 `maintenance_events`

Stores append-only history for maintenance tasks.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `maintenance_task_id` | `UUID` | No | — | Related maintenance task |
| `performed_by` | `UUID` | Yes | `NULL` | User responsible for the event |
| `event_type` | `VARCHAR(50)` | No | — | Type of maintenance event |
| `notes` | `TEXT` | Yes | `NULL` | Additional intervention details |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Event occurrence time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (maintenance_task_id)
REFERENCES maintenance_tasks(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (performed_by)
REFERENCES users(id)
ON DELETE SET NULL
```

### Initial event types

```text
task_created
assigned
started
note_added
inspection_completed
component_replaced
blocked
resumed
completed
cancelled
```

### Important rules

- Events should normally be append-only.
- Existing event history should not be overwritten.
- System-generated events may have no `performed_by` user.
- Event timestamps should reflect the real order of the intervention.

---

## 9. Notification Table

## 9.1 `notifications`

Stores in-application and email-notification records.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `user_id` | `UUID` | No | — | Notification recipient |
| `alert_id` | `UUID` | Yes | `NULL` | Related alert |
| `maintenance_task_id` | `UUID` | Yes | `NULL` | Related maintenance task |
| `notification_type` | `VARCHAR(30)` | No | — | Notification category |
| `delivery_channel` | `VARCHAR(20)` | No | `'in_app'` | Delivery method |
| `delivery_status` | `VARCHAR(20)` | No | `'pending'` | Delivery state |
| `title` | `VARCHAR(200)` | No | — | Notification title |
| `message` | `TEXT` | No | — | Notification content |
| `is_read` | `BOOLEAN` | No | `FALSE` | In-app read state |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Notification creation time |
| `read_at` | `TIMESTAMPTZ` | Yes | `NULL` | Time opened by the user |
| `sent_at` | `TIMESTAMPTZ` | Yes | `NULL` | Successful external-delivery time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign keys

```text
FOREIGN KEY (user_id)
REFERENCES users(id)
ON DELETE RESTRICT
```

```text
FOREIGN KEY (alert_id)
REFERENCES alerts(id)
ON DELETE SET NULL
```

```text
FOREIGN KEY (maintenance_task_id)
REFERENCES maintenance_tasks(id)
ON DELETE SET NULL
```

### Allowed notification types

```text
alert
maintenance
assignment
system
```

### Allowed delivery channels

```text
in_app
email
both
```

### Allowed delivery statuses

```text
pending
sent
failed
not_applicable
```

### Check constraints

```text
notification_type IN (
    'alert',
    'maintenance',
    'assignment',
    'system'
)
```

```text
delivery_channel IN (
    'in_app',
    'email',
    'both'
)
```

```text
delivery_status IN (
    'pending',
    'sent',
    'failed',
    'not_applicable'
)
```

```text
is_read = FALSE
OR read_at IS NOT NULL
```

```text
delivery_status <> 'sent'
OR delivery_channel = 'in_app'
OR sent_at IS NOT NULL
```

### Important rules

- Every notification has one recipient.
- In-app notifications remain available even when email delivery fails.
- Delivery failures should be logged.
- Duplicate notifications should be prevented by application logic.

---

## 10. Audit Table

## 10.1 `audit_logs`

Stores important security, administrative and business actions.

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---:|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `actor_user_id` | `UUID` | Yes | `NULL` | User responsible for the action |
| `action` | `VARCHAR(100)` | No | — | Action identifier |
| `resource_type` | `VARCHAR(100)` | No | — | Type of affected resource |
| `resource_id` | `UUID` | Yes | `NULL` | Identifier of affected resource |
| `previous_values` | `JSONB` | Yes | `NULL` | Values before the change |
| `new_values` | `JSONB` | Yes | `NULL` | Values after the change |
| `ip_address` | `INET` | Yes | `NULL` | Client IP address |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Event creation time |

### Primary key

```text
PRIMARY KEY (id)
```

### Foreign key

```text
FOREIGN KEY (actor_user_id)
REFERENCES users(id)
ON DELETE SET NULL
```

### Important rules

- Audit logs should be append-only.
- Normal users must not edit or delete audit records.
- Sensitive fields such as password hashes, tokens and secrets must not be stored in audit JSON.
- `resource_id` is intentionally not a foreign key because it may refer to different table types.
- System-generated actions may have no `actor_user_id`.

---

## 11. Relationship Summary

| Parent Table | Child Table | Foreign Key | Deletion Behaviour |
|---|---|---|---|
| `roles` | `users` | `role_id` | `RESTRICT` |
| `users` | `machine_assignments` | `user_id` | `RESTRICT` |
| `machines` | `machine_assignments` | `machine_id` | `RESTRICT` |
| `users` | `machine_assignments` | `assigned_by` | `SET NULL` |
| `machines` | `sensors` | `machine_id` | `RESTRICT` |
| `sensors` | `sensor_measurements` | `sensor_id` | `RESTRICT` |
| `machines` | `predictions` | `machine_id` | `RESTRICT` |
| `model_versions` | `predictions` | `model_version_id` | `RESTRICT` |
| `machines` | `alerts` | `machine_id` | `RESTRICT` |
| `sensors` | `alerts` | `sensor_id` | `SET NULL` |
| `predictions` | `alerts` | `prediction_id` | `SET NULL` |
| `users` | `alerts` | `acknowledged_by` | `SET NULL` |
| `users` | `alerts` | `resolved_by` | `SET NULL` |
| `machines` | `maintenance_tasks` | `machine_id` | `RESTRICT` |
| `alerts` | `maintenance_tasks` | `source_alert_id` | `SET NULL` |
| `users` | `maintenance_tasks` | `assigned_user_id` | `SET NULL` |
| `users` | `maintenance_tasks` | `created_by` | `SET NULL` |
| `maintenance_tasks` | `maintenance_events` | `maintenance_task_id` | `RESTRICT` |
| `users` | `maintenance_events` | `performed_by` | `SET NULL` |
| `users` | `notifications` | `user_id` | `RESTRICT` |
| `alerts` | `notifications` | `alert_id` | `SET NULL` |
| `maintenance_tasks` | `notifications` | `maintenance_task_id` | `SET NULL` |
| `users` | `audit_logs` | `actor_user_id` | `SET NULL` |

---

## 12. Record Mutability

### Normally mutable

The following records may be updated:

- Users
- Machines
- Machine assignments
- Sensors
- Alerts
- Maintenance tasks
- Notifications
- Model activation status

### Normally immutable or append-only

The following records should not normally be changed after creation:

- Sensor measurements
- Predictions
- Maintenance events
- Audit logs

Corrections to immutable records should normally create a new record or a separate correction event rather than silently replacing history.

---

## 13. Soft Deletion and Deactivation

The MVP will not use a universal `deleted_at` field for every table.

Instead, domain-specific statuses will be used:

```text
users.is_active
machines.status = 'decommissioned'
sensors.status = 'retired'
```

Historical records such as measurements, predictions, alerts, maintenance events and audit logs must remain traceable.

Permanent deletion should be limited to development or administrative cleanup procedures.

---

## 14. Database-Level and Application-Level Rules

### Database-level rules

PostgreSQL should enforce:

- Primary keys
- Foreign keys
- Unique constraints
- Required fields
- Value ranges
- Controlled status values
- Basic timestamp consistency
- Relationship integrity

### Application-level rules

The Backend API should enforce:

- Role compatibility for machine assignments
- Maintenance tasks assigned only to appropriate users
- Valid alert workflow transitions
- Valid maintenance workflow transitions
- Duplicate-alert prevention
- Duplicate-notification prevention
- Machine-health status calculation
- Prediction risk classification
- Authorization for data access
- Audit-log creation
- Cross-table business workflows

---

## 15. Planned Implementation Mapping

The schema will later be implemented using:

```text
PostgreSQL
SQLAlchemy
Alembic
Pydantic
FastAPI
```

Each table will normally have:

- A SQLAlchemy ORM model
- Pydantic request and response schemas
- Repository or data-access functions
- Alembic migration definitions
- Automated database tests

The implementation may introduce minor changes when technical testing reveals a justified need.

Any major schema change should also update this documentation.

---

## 16. Next Database Documents

The next documents will be:

```text
Data_Dictionary.md
Indexing_Strategy.md
Migration_and_Seed_Strategy.md
```

The Data Dictionary will explain the business meaning and usage of important fields.

The Indexing Strategy will define indexes based on expected application queries.

The Migration and Seed Strategy will define how the database is created and populated safely.

---

## 17. Related Documents

- [[04_Database/Database_Overview|Database Overview]]
- [[04_Database/Entity_Relationship_Diagram|Entity Relationship Diagram]]
- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[03_Architecture/Deployment_Architecture|Deployment Architecture]]
- [[02_Requirements/Software_Requirements_Specification|Software Requirements Specification]]
- [[02_Requirements/Functional_Requirements|Functional Requirements]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
- [[02_Requirements/Use_Cases|Use Cases]]
- [[Data_Dictionary]]
- [[Indexing_Strategy]]
- [[Migration_and_Seed_Strategy]]

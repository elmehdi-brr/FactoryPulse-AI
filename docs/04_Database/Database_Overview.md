# FactoryPulse AI — Database Overview

## 1. Purpose

This document provides a high-level overview of the FactoryPulse AI database architecture.

It defines:

- The database technology
- The main data domains
- The entities required for the MVP
- The principal relationships
- Data integrity rules
- Persistence and deletion principles
- Performance considerations
- Database responsibilities and boundaries

Detailed tables, fields, constraints and indexes will be defined in later database-design documents.

---

## 2. Database Technology

FactoryPulse AI will use:

```text
PostgreSQL
```

PostgreSQL was selected because it is:

- Free and open source
- Reliable and widely used
- Suitable for relational business data
- Suitable for operational and time-series-like sensor data
- Compatible with SQLAlchemy and Alembic
- Supported by Docker
- Capable of storing structured JSON data through JSONB
- Appropriate for future production deployment

PostgreSQL will initially run inside a Docker container.

A native PostgreSQL installation on Windows is not required for the MVP.

---

## 3. Database Responsibilities

The FactoryPulse AI database is responsible for storing persistent application information.

This includes:

- Users and roles
- Machines and sensors
- Machine assignments
- Sensor measurements
- Machine-learning model versions
- AI predictions
- Alerts
- Maintenance tasks and history
- Notifications
- Audit records

The database must support:

- Data integrity
- Historical traceability
- Efficient data retrieval
- Secure access
- Relationship enforcement
- Future schema evolution

---

## 4. Database Boundary

### Inside the main PostgreSQL database

The database stores:

- Application users
- Role assignments
- Industrial assets
- Sensor configuration
- Sensor measurements
- Prediction results
- Alerts
- Maintenance information
- Notifications
- Audit history
- Model metadata

### Outside the main PostgreSQL database

The database does not store:

- User passwords in plain text
- Trained machine-learning model files
- Source-code files
- Docker images
- Application logs
- Frontend static files
- Raw secret keys
- Environment configuration files
- Email-service infrastructure

Trained model files will remain in the ML Service model directory or a dedicated model-storage location.

Only model metadata and version information will be stored in PostgreSQL.

---

## 5. Data Domains

The database is divided logically into the following data domains.

### 5.1 Identity and Access

This domain manages users and platform roles.

Entities:

- `roles`
- `users`

Responsibilities:

- Store supported platform roles
- Store user accounts
- Associate every user with a role
- Support account activation and deactivation
- Support role-based access control

---

### 5.2 Industrial Assets

This domain manages machines, sensors and user assignments.

Entities:

- `machines`
- `machine_assignments`
- `sensors`

Responsibilities:

- Register machines
- Store machine information
- Register sensors
- Assign sensors to machines
- Assign users to machines
- Store threshold configuration
- Track machine and sensor status

---

### 5.3 Sensor Data

This domain stores measurements received from simulated or future physical sensors.

Entity:

- `sensor_measurements`

Responsibilities:

- Store measurement values
- Associate measurements with sensors
- Store measurement timestamps
- Store data-quality information
- Support recent and historical monitoring queries

The `sensor_measurements` table is expected to become the largest table in the system.

---

### 5.4 Artificial Intelligence

This domain stores model metadata and prediction results.

Entities:

- `model_versions`
- `predictions`

Responsibilities:

- Track model versions
- Identify the model used for each prediction
- Store anomaly results
- Store failure-risk predictions
- Store risk levels
- Store prediction explanations
- Preserve prediction history

---

### 5.5 Alert Management

This domain stores operational warnings and critical events.

Entity:

- `alerts`

Responsibilities:

- Store threshold-based alerts
- Store AI-generated alerts
- Store manually reported alerts
- Track alert severity
- Track alert status
- Record acknowledgement and resolution information

---

### 5.6 Maintenance Management

This domain stores maintenance tasks and intervention history.

Entities:

- `maintenance_tasks`
- `maintenance_events`

Responsibilities:

- Create maintenance tasks
- Assign tasks to users
- Link tasks to machines and alerts
- Track maintenance progress
- Store intervention notes
- Preserve maintenance history

---

### 5.7 Notifications

This domain stores user notifications.

Entity:

- `notifications`

Responsibilities:

- Store in-application notifications
- Track email-delivery status
- Associate notifications with users
- Track read and unread status
- Preserve notification history

---

### 5.8 Audit

This domain stores important system and user actions.

Entity:

- `audit_logs`

Responsibilities:

- Record authentication-related actions
- Record administrative changes
- Record asset changes
- Record alert actions
- Record maintenance actions
- Preserve previous and new values where appropriate

Audit records should normally be append-only.

---

## 6. MVP Entity List

The initial FactoryPulse AI database contains thirteen entities:

| Entity | Purpose |
|---|---|
| `roles` | Stores platform roles |
| `users` | Stores user accounts |
| `machines` | Stores monitored industrial machines |
| `machine_assignments` | Associates users with machines |
| `sensors` | Stores sensors attached to machines |
| `sensor_measurements` | Stores sensor values over time |
| `model_versions` | Stores ML model metadata and versions |
| `predictions` | Stores anomaly and failure-risk results |
| `alerts` | Stores warnings and critical conditions |
| `maintenance_tasks` | Stores planned or active maintenance work |
| `maintenance_events` | Stores maintenance-task history |
| `notifications` | Stores in-app and email notifications |
| `audit_logs` | Stores important system actions |

---

## 7. Main Relationships

The principal relationships are:

```text
One Role
  → has many Users

One User
  → may have many Machine Assignments
  → may receive many Notifications
  → may perform many Maintenance Events
  → may create many Audit Logs

One Machine
  → has many Machine Assignments
  → has many Sensors
  → has many Predictions
  → has many Alerts
  → has many Maintenance Tasks

One Sensor
  → belongs to one Machine
  → has many Sensor Measurements
  → may be associated with many Alerts

One Model Version
  → produces many Predictions

One Prediction
  → belongs to one Machine
  → may generate one or more Alerts

One Alert
  → belongs to one Machine
  → may reference one Sensor
  → may reference one Prediction
  → may generate one or more Maintenance Tasks

One Maintenance Task
  → belongs to one Machine
  → may originate from one Alert
  → has many Maintenance Events
```

The exact cardinalities and optional relationships will be defined in the Entity Relationship Diagram.

---

## 8. Primary Key Strategy

The database will use UUID values as primary keys for main application entities.

Example:

```text
550e8400-e29b-41d4-a716-446655440000
```

UUID primary keys are planned for:

- Users
- Machines
- Sensors
- Measurements
- Predictions
- Alerts
- Maintenance tasks
- Notifications
- Audit records

Advantages include:

- Keys can be generated without relying on sequential database values
- IDs are difficult to guess
- Data can be moved between environments more safely
- Future distributed processing is easier to support

The final implementation may use PostgreSQL's native `UUID` type.

---

## 9. Naming Conventions

The database will follow consistent naming conventions.

### Tables

Table names use lowercase plural `snake_case`.

Examples:

```text
users
sensor_measurements
maintenance_tasks
model_versions
```

### Columns

Column names use lowercase `snake_case`.

Examples:

```text
first_name
recorded_at
machine_id
failure_probability
```

### Primary keys

Primary-key columns use:

```text
id
```

### Foreign keys

Foreign-key columns use the referenced entity name followed by `_id`.

Examples:

```text
role_id
machine_id
sensor_id
assigned_user_id
model_version_id
```

### Timestamps

Common timestamp names include:

```text
created_at
updated_at
recorded_at
received_at
acknowledged_at
resolved_at
completed_at
```

---

## 10. Timestamp Strategy

PostgreSQL timestamps should include timezone information where appropriate.

The planned type is:

```text
TIMESTAMP WITH TIME ZONE
```

All application timestamps should be stored consistently, preferably in UTC.

The frontend may convert timestamps into the user's local timezone for display.

Important distinctions include:

- `recorded_at`: when a sensor produced the measurement
- `received_at`: when FactoryPulse AI received the measurement
- `created_at`: when a database record was created
- `updated_at`: when a record was last modified
- `predicted_at`: when an AI prediction was generated

---

## 11. Data Integrity Principles

The database must prevent invalid relationships and values.

Planned controls include:

- Primary-key constraints
- Foreign-key constraints
- Unique constraints
- Not-null constraints
- Check constraints
- Default values
- Controlled status values
- Transaction management

Examples:

- Every user must reference a valid role
- Every sensor must belong to a valid machine
- Every measurement must reference a valid sensor
- User email addresses must be unique
- Machine codes must be unique
- Sensor codes must be unique within their expected scope
- Alert severity must use an accepted value
- Failure probabilities must remain between 0 and 1
- Completed maintenance tasks should have a completion timestamp
- Resolved alerts should have a resolution timestamp

Some cross-field business rules may also be enforced by the Backend API.

---

## 12. Status and Category Values

The database will use controlled values for important statuses.

Possible user status:

```text
active
inactive
```

Possible machine status:

```text
operational
warning
critical
maintenance
offline
decommissioned
```

Possible sensor status:

```text
active
inactive
faulty
maintenance
```

Possible alert severity:

```text
info
warning
high
critical
```

Possible alert status:

```text
open
acknowledged
in_progress
resolved
closed
```

Possible maintenance priority:

```text
low
medium
high
critical
```

Possible maintenance status:

```text
open
assigned
in_progress
blocked
completed
cancelled
```

Possible prediction risk level:

```text
low
medium
high
critical
```

The final implementation will decide whether these values use PostgreSQL enums, constrained text columns or application-level enumerations.

---

## 13. JSONB Usage

PostgreSQL JSONB may be used when information is structured but may vary between records.

Potential JSONB fields include:

- Prediction explanations
- Model evaluation metrics
- Audit previous values
- Audit new values
- Additional model metadata

JSONB should not replace normal relational columns when the structure is stable and frequently queried.

For example, `machine_id`, `risk_level` and `predicted_at` should remain normal database columns rather than being hidden inside JSON.

---

## 14. Sensor Measurement Strategy

Each accepted sensor measurement will initially be stored as an individual row.

Conceptual example:

```text
sensor_id: SENSOR-UUID
value: 78.4
recorded_at: 2026-08-01T10:45:00Z
received_at: 2026-08-01T10:45:01Z
quality_status: valid
```

The MVP will use standard PostgreSQL tables.

The following technologies will not be introduced initially:

- TimescaleDB
- Table partitioning
- External time-series databases
- Distributed message brokers

They may be considered later if measurement volume becomes large enough to justify them.

---

## 15. Historical Data and Deletion Strategy

FactoryPulse AI should preserve important operational history.

### Users

Users should normally be deactivated rather than permanently deleted.

### Machines

Machines should normally be marked as decommissioned rather than deleted when historical measurements, alerts or maintenance records exist.

### Sensors

Sensors may be marked as inactive or retired.

### Measurements

Sensor measurements may later use a retention or archival strategy, but the MVP will keep them unless manually removed.

### Alerts

Alerts should be preserved for operational history.

### Maintenance records

Maintenance tasks and events should remain available for traceability.

### Audit logs

Audit logs should not normally be edited or deleted by ordinary application users.

---

## 16. Database Access Rules

The following access rules apply:

- Only the Backend API directly accesses the main PostgreSQL database
- The Web Application must not access PostgreSQL directly
- The Sensor Simulator must not access PostgreSQL directly
- The ML Service must not modify application data directly
- The Backend API uses SQLAlchemy for database operations
- Alembic manages database schema migrations
- Database credentials are stored in environment variables
- Database passwords must not be committed to GitHub

The ML Service receives prediction input from the Backend API and returns prediction results to it.

The Backend API is responsible for storing those results.

---

## 17. Transaction Principles

Database transactions should protect multi-step operations.

Examples include:

- Creating an alert and its notification
- Creating a maintenance task from an alert
- Saving a prediction and updating machine status
- Registering a machine with its initial sensors
- Acknowledging an alert and writing an audit record

If part of an operation fails, the transaction should prevent partially saved data where consistency is required.

---

## 18. Performance Considerations

The database should support common application queries efficiently.

Expected query patterns include:

- Find a user by email
- Find a machine by code
- Retrieve sensors for a machine
- Retrieve the latest measurements for a sensor
- Retrieve machine measurements within a time range
- Retrieve open alerts for a machine
- Retrieve maintenance tasks assigned to a user
- Retrieve recent predictions for a machine
- Retrieve unread notifications for a user
- Retrieve audit records by actor or resource

Indexes will be defined later based on these query patterns.

The measurement table requires special attention because it will receive frequent inserts.

---

## 19. Backup and Recovery

During the MVP, PostgreSQL data will be stored in a persistent Docker volume.

A Docker volume protects data when containers are recreated, but it is not a complete backup strategy.

Important backup targets include:

- PostgreSQL database
- ML model artifacts
- Database migration files
- Seed-data definitions
- Environment-variable templates

Manual database backups may be used during early development.

Automated backups may be added for a future production deployment.

---

## 20. Schema Evolution

The database schema will evolve through migrations.

Planned technology:

```text
Alembic
```

Migrations will be used to:

- Create tables
- Add or remove columns
- Add constraints
- Create indexes
- Modify relationships
- Apply controlled schema changes

Developers should not manually change production database structures without a migration.

Migration files will be stored in the repository.

---

## 21. Initial Seed Data

The database will require initial development data.

Possible seed data includes:

- Four platform roles
- One administrator account
- Example machines
- Example sensors
- Example machine assignments
- Example model-version metadata

Passwords and secrets must not be hard-coded in public seed files.

The final seed strategy will be documented separately.

---

## 22. Deferred Database Features

The following features are outside the initial MVP:

- Multiple factories
- Production-line hierarchy
- Spare-parts inventory
- Supplier management
- Detailed permission tables
- Sensor calibration history
- Database sharding
- Automatic table partitioning
- TimescaleDB
- ERP integration tables
- CMMS integration tables
- Long-term data warehouse
- Multi-tenant database architecture

These capabilities may be considered in future versions.

---

## 23. Planned Database Documentation

The `04_Database` folder will contain:

```text
04_Database/
├── Database_Overview.md
├── Entity_Relationship_Diagram.md
├── Database_Schema.md
├── Data_Dictionary.md
├── Indexing_Strategy.md
└── Migration_and_Seed_Strategy.md
```

Each document has a different purpose:

| Document | Purpose |
|---|---|
| Database Overview | Explains the general database approach |
| Entity Relationship Diagram | Shows entities and relationships visually |
| Database Schema | Defines tables, fields, keys and constraints |
| Data Dictionary | Explains the meaning of important fields |
| Indexing Strategy | Defines indexes based on expected queries |
| Migration and Seed Strategy | Explains schema migration and initial data |

---

## 24. Related Documents

- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Container_Architecture|Container Architecture]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[03_Architecture/Deployment_Architecture|Deployment Architecture]]
- [[02_Requirements/Software_Requirements_Specification|Software Requirements Specification]]
- [[02_Requirements/Functional_Requirements|Functional Requirements]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
- [[02_Requirements/Use_Cases|Use Cases]]
- [[Database_Schema]]


# FactoryPulse AI — Migration and Seed Strategy

## 1. Purpose

This document defines how the FactoryPulse AI database schema will be created, changed, versioned and populated with initial data.

It explains:

- How database migrations will be managed
- How schema changes will be introduced safely
- How migration files will be stored and reviewed
- How required system data will be inserted
- How development and demonstration data will be created
- How sensitive information will be protected
- How migrations and seed operations will work with Docker Compose

The strategy applies to the PostgreSQL database used by the FactoryPulse AI MVP.

---

## 2. Selected Technologies

FactoryPulse AI will use:

```text
PostgreSQL
SQLAlchemy
Alembic
Python
Docker Compose
```

### SQLAlchemy

SQLAlchemy will define the application’s database models and provide database access from the Backend API.

### Alembic

Alembic will manage schema migrations.

It will record which migrations have been applied and allow the database structure to evolve in a controlled manner.

### Python Seed Scripts

Python scripts will insert required system data and optional development data.

---

## 3. Migration Goals

The migration process must:

- Create the database schema consistently
- Preserve existing data whenever possible
- Keep development environments synchronized
- Make schema changes reproducible
- Support upgrade and rollback operations
- Keep database history in Git
- Avoid manual changes that are not documented
- Support future production deployment

A developer should be able to create the complete database by applying the repository’s migrations to an empty PostgreSQL database.

---

## 4. Migration Principles

FactoryPulse AI will follow these rules:

- Every schema change must use an Alembic migration
- Migration files must be committed to Git
- Applied migration files must not normally be edited
- New changes require a new migration
- Migrations should be small and focused
- Migration names should clearly describe their purpose
- Upgrade and downgrade logic should be reviewed
- Destructive operations require special care
- Schema changes should be tested before being pushed
- Application code and migrations should remain compatible

Manual database changes should not replace migrations.

---

## 5. Alembic Version Tracking

Alembic automatically creates a table named:

```text
alembic_version
```

This table records the revision currently applied to the database.

Conceptually:

```text
Migration files in repository
          ↓
Alembic revision history
          ↓
alembic_version in PostgreSQL
```

Alembic uses this information to determine which migrations still need to run.

The application should not manually modify the `alembic_version` table.

---

## 6. Planned Migration Directory

The Backend project may use a structure similar to:

```text
backend/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
└── app/
    ├── database/
    └── models/
```

Migration files will be stored in:

```text
backend/alembic/versions/
```

Each migration file will contain:

- A unique revision identifier
- A reference to the previous revision
- A descriptive message
- An `upgrade()` function
- A `downgrade()` function

---

## 7. Migration Naming Convention

Migration messages should clearly explain the change.

Good examples:

```text
create_initial_database_schema
add_last_login_to_users
add_prediction_explanation_data
create_sensor_measurement_indexes
add_notification_delivery_status
```

Avoid unclear names such as:

```text
update_database
new_changes
fix_table
migration_2
```

A migration filename may look similar to:

```text
20260801_01_create_initial_database_schema.py
```

Alembic generates the revision identifier, while the project may add a readable naming convention where practical.

---

## 8. Initial Migration Scope

The first major migration should create the thirteen MVP tables:

```text
roles
users
machines
machine_assignments
sensors
sensor_measurements
model_versions
predictions
alerts
maintenance_tasks
maintenance_events
notifications
audit_logs
```

It should also create:

- UUID-generation support
- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Default values
- Required indexes
- Controlled status validation

The initial migration should enable:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

This supports:

```sql
gen_random_uuid()
```

---

## 9. Initial Table-Creation Order

Tables must be created in an order that respects foreign-key dependencies.

Recommended order:

```text
1. roles
2. users
3. machines
4. machine_assignments
5. sensors
6. sensor_measurements
7. model_versions
8. predictions
9. alerts
10. maintenance_tasks
11. maintenance_events
12. notifications
13. audit_logs
```

This order ensures that referenced parent tables exist before child foreign keys are created.

During downgrade, tables should normally be removed in the reverse order.

---

## 10. Constraint and Index Creation

The migration process should create database objects in a controlled sequence:

```text
1. Extensions
2. Tables
3. Primary keys
4. Foreign keys
5. Unique constraints
6. Check constraints
7. Standard indexes
8. Partial or specialized indexes
```

Indexes required by primary keys and unique constraints should not be duplicated.

Mandatory indexes are defined in:

```text
Indexing_Strategy.md
```

Important initial indexes include:

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

---

## 11. Creating New Migrations

After modifying SQLAlchemy models, a developer may generate a migration using:

```powershell
alembic revision --autogenerate -m "describe the change"
```

Example:

```powershell
alembic revision --autogenerate -m "add last login timestamp to users"
```

Autogenerated migrations must always be reviewed.

Alembic may not automatically understand every intended change, especially:

- Column renaming
- Complex check constraints
- Data transformations
- Partial indexes
- Custom PostgreSQL features
- Changes that could delete data

Autogeneration is an assistant, not a replacement for migration review.

---

## 12. Applying Migrations

To apply all pending migrations:

```powershell
alembic upgrade head
```

To apply migrations through Docker Compose, a future command may be similar to:

```powershell
docker compose exec backend alembic upgrade head
```

The exact command will depend on the final Docker configuration.

The Backend service should not begin normal operation against an incompatible schema.

During development, migrations may be executed manually before starting the complete application.

---

## 13. Rollback Strategy

To undo the most recent migration:

```powershell
alembic downgrade -1
```

To move to a specific revision:

```powershell
alembic downgrade <revision_id>
```

A downgrade operation should be tested before relying on it.

Some destructive changes cannot be safely reversed without a backup.

Examples include:

- Dropping a table
- Dropping a populated column
- Changing a data type incompatibly
- Deleting records
- Replacing historical values

For these changes, the migration should document the risk clearly.

---

## 14. Safe Schema-Change Pattern

For important or populated columns, prefer gradual changes.

Example: making a new column required.

Unsafe approach:

```text
Immediately add a NOT NULL column without a default
```

Safer approach:

```text
1. Add the column as nullable
2. Populate existing records
3. Update application code
4. Verify that all records have values
5. Add the NOT NULL constraint
```

Example: renaming a field.

Safer pattern:

```text
1. Add the new field
2. Copy data from the old field
3. Update application code
4. Verify the new field
5. Remove the old field in a later migration
```

This approach becomes especially important in production environments.

---

## 15. Data Migrations

Some migrations change both schema and existing data.

Examples:

- Converting old status values
- Normalizing email addresses
- Populating a newly added required field
- Moving information from one column to another
- Creating records based on existing relationships

Data migrations should:

- Be deterministic
- Avoid depending on external APIs
- Avoid depending on temporary application behaviour
- Run inside transactions where practical
- Validate assumptions before changing data
- Preserve historical meaning

Large data migrations may need to be separated from schema migrations in a future production environment.

---

## 16. Seed Data Categories

FactoryPulse AI will use three categories of seed data.

### 16.1 Required System Seed Data

Data required for the application to operate.

Examples:

- Platform roles
- Initial administrative account
- Required system configuration
- Initial model metadata when a model exists

### 16.2 Development and Demonstration Data

Optional data used to develop or demonstrate the application.

Examples:

- Example machines
- Example sensors
- Machine assignments
- Sample alerts
- Sample maintenance tasks
- Simulated measurement history

### 16.3 Test Fixtures

Controlled data used by automated tests.

Examples:

- Test users
- Test machines
- Test sensors
- Test measurements
- Expected alerts and predictions

Test data must remain separate from normal development and production seed data.

---

## 17. Required Role Seed Data

The initial seed process must create these four roles:

| Name | Description |
|---|---|
| `administrator` | Manages users, roles, machines, sensors and platform configuration |
| `plant_manager` | Monitors factory performance, alerts, predictions and reports |
| `maintenance_engineer` | Investigates alerts and performs maintenance interventions |
| `machine_operator` | Monitors assigned machines and reports operational issues |

The role seed process must be idempotent.

Running it multiple times must not create duplicate roles.

Conceptual approach:

```text
Create role only when it does not already exist
```

---

## 18. Initial Administrator Account

The development environment requires an initial administrator account.

The administrator credentials must not be hard-coded in a public seed script.

Possible environment variables:

```text
INITIAL_ADMIN_EMAIL
INITIAL_ADMIN_PASSWORD
INITIAL_ADMIN_FIRST_NAME
INITIAL_ADMIN_LAST_NAME
```

The seed process should:

1. Read the values from environment variables.
2. Normalize the email address.
3. Securely hash the password.
4. Find the Administrator role.
5. Create the account only when it does not already exist.
6. Avoid printing the plain-text password in logs.

The `.env.example` file may include safe placeholders:

```text
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=replace_with_secure_password
INITIAL_ADMIN_FIRST_NAME=System
INITIAL_ADMIN_LAST_NAME=Administrator
```

The real `.env` file must remain excluded from Git.

---

## 19. Development Machine Seed Data

Optional development seeds may create example machines such as:

```text
PUMP-001
COMPRESSOR-001
MOTOR-001
```

Example information may include:

- Machine code
- Machine name
- Description
- Location
- Manufacturer
- Model
- Operational status

This data should clearly be identified as demonstration data.

It must not be required for the application to start successfully.

---

## 20. Development Sensor Seed Data

Example sensors may be attached to seeded machines.

Possible examples:

```text
TEMP-001
PRESS-001
VIB-001
RPM-001
VOLT-001
CURRENT-001
FLOW-001
```

Each seeded sensor may include:

- Sensor type
- Measurement unit
- Warning thresholds
- Critical thresholds
- Operational status

Example:

```text
Sensor: VIB-001
Type: vibration
Unit: mm/s
Warning maximum: 4.5
Critical maximum: 7.0
```

The final threshold values should be appropriate for the simulated scenario and clearly treated as demonstration configuration rather than universal industrial standards.

---

## 21. Model-Version Seed Data

Model-version records should only be seeded when the related model artifact exists.

Possible data:

```text
name
version
model_type
file_path
metrics
model_metadata
is_active
```

The seed process should not create an active model record that points to a missing or invalid artifact.

Model registration may eventually be handled by a dedicated administrative or ML deployment process rather than a normal database seed.

---

## 22. Sensor Measurement Generation

Large quantities of sensor measurements should not be stored directly in static seed files.

Instead, the Sensor Simulator should generate measurements dynamically.

This provides:

- Realistic timestamp progression
- Normal operating behaviour
- Abnormal events
- Gradual degradation
- Repeatable demonstration scenarios
- Reduced repository size

A small number of fixed measurements may still be created for automated tests.

---

## 23. Seed Script Structure

A possible seed-script structure is:

```text
backend/
└── scripts/
    ├── seed_required_data.py
    ├── seed_development_data.py
    └── reset_development_data.py
```

Responsibilities:

### `seed_required_data.py`

Creates:

- Roles
- Initial administrator
- Other data required for startup

### `seed_development_data.py`

Creates:

- Demo users
- Machines
- Sensors
- Assignments
- Sample operational records

### `reset_development_data.py`

May remove and recreate development-only records.

It must never be used automatically in production.

---

## 24. Seed Idempotency

Seed scripts should be safe to run multiple times.

They should identify existing records using stable values such as:

```text
roles.name
users.email
machines.code
sensors(machine_id, code)
model_versions(name, version)
```

The script should:

- Create missing records
- Skip unchanged records
- Update only fields intentionally managed by the seed
- Avoid creating duplicates
- Report what was created or skipped

Seed scripts should not silently overwrite user-created production data.

---

## 25. Environment Separation

Seed behaviour must differ by environment.

### Development

May include:

- Required roles
- Administrator
- Demo users
- Demo machines
- Demo sensors
- Example assignments
- Demonstration alerts and tasks

### Testing

Uses isolated and predictable test fixtures.

Test data should be recreated for each test run or test suite as appropriate.

### Production

Should include only:

- Required system data
- Securely configured administrator bootstrap where necessary
- Explicitly approved configuration

Production must not automatically receive demonstration machines, users or measurements.

---

## 26. Docker Development Workflow

A future local setup may follow this sequence:

```text
1. Start PostgreSQL
2. Wait for database health check
3. Run Alembic migrations
4. Run required seed script
5. Start the Backend API
6. Start the ML Service and Frontend
7. Start the Sensor Simulator
```

Possible future commands:

```powershell
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/seed_required_data.py
docker compose up
```

The exact commands may change after Dockerfiles and Compose services are implemented.

---

## 27. Automatic Migrations at Startup

Automatically running migrations whenever the Backend starts can be convenient during local development.

However, production deployment requires more control.

Possible MVP approach:

- Run migrations explicitly through a command
- Start the Backend only after migration success
- Avoid multiple Backend instances applying migrations simultaneously

A dedicated migration step is safer than allowing every application instance to modify the database during startup.

---

## 28. Migration Testing

Migrations should be tested against:

### Empty database

Verify that all migrations can create the full schema from nothing.

### Existing database

Verify that the migration preserves existing records and relationships.

### Upgrade path

Run:

```text
old revision → latest revision
```

### Downgrade path

Where safe, run:

```text
latest revision → previous revision
```

### Re-upgrade path

Verify:

```text
previous revision → latest revision
```

Automated tests should eventually verify:

- All expected tables exist
- Foreign keys are correct
- Required indexes exist
- Check constraints reject invalid values
- Seed scripts do not create duplicates
- Required roles are available

---

## 29. Backup Before Destructive Migrations

Before a destructive schema change:

- Create a PostgreSQL backup
- Confirm the backup is readable
- Review affected tables and row counts
- Document expected data loss
- Test the migration using a copy of the database
- Prepare a recovery procedure

A Docker volume is not a complete backup.

Future backup commands may use PostgreSQL tools such as:

```text
pg_dump
pg_restore
```

These will be defined when the database is implemented.

---

## 30. Migration Failure Handling

When a migration fails:

1. Stop the deployment process.
2. Review the Alembic and PostgreSQL error.
3. Determine whether the transaction was rolled back.
4. Verify the current Alembic revision.
5. Inspect the current database structure.
6. Correct the migration or create a follow-up migration.
7. Restore from backup if a destructive partial change occurred.

Do not manually mark a failed migration as successful without verifying the actual schema.

---

## 31. Version-Control Rules

The following files should be committed:

```text
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/versions/*.py
seed scripts
.env.example
database documentation
```

The following must not be committed:

```text
.env
database passwords
administrator passwords
production database dumps
private user data
secret keys
authentication tokens
```

Database dumps containing real or sensitive information should not be uploaded to a public repository.

---

## 32. Migration Review Checklist

Before committing a migration, verify:

- The migration has a clear name
- `upgrade()` performs the intended change
- `downgrade()` is correct or its limitation is documented
- Foreign keys use the intended deletion behaviour
- Required constraints are present
- Indexes are not duplicated
- Existing data is protected
- No secret values are included
- The migration works on an empty database
- The migration works against the previous revision
- Related documentation is updated

---

## 33. Seed Review Checklist

Before committing a seed change, verify:

- Required data is clearly separated from demo data
- The script is idempotent
- Passwords are not hard-coded
- Emails are normalized
- Passwords are securely hashed
- Duplicate records are prevented
- Demo data is not inserted in production automatically
- Model records reference valid artifacts
- Logs do not expose secrets
- The script reports failures clearly

---

## 34. Deferred Migration Features

The following capabilities are not required for the MVP:

- Automatic production migration pipelines
- Zero-downtime database migrations
- Multiple database schemas
- Multi-tenant migration management
- Distributed migration locking beyond normal deployment controls
- Database sharding migrations
- TimescaleDB migration management
- Automated production rollback
- Large-scale online data migrations

They may be introduced when deployment requirements justify them.

---

## 35. Related Documents

- [[04_Database/Database_Overview|Database Overview]]
- [[04_Database/Entity_Relationship_Diagram|Entity Relationship Diagram]]
- [[04_Database/Database_Schema|Database Schema]]
- [[04_Database/Data_Dictionary|Data Dictionary]]
- [[04_Database/Indexing_Strategy|Indexing Strategy]]
- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Deployment_Architecture|Deployment Architecture]]
- [[02_Requirements/Software_Requirements_Specification|Software Requirements Specification]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
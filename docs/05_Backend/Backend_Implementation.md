# Backend Implementation

## 1. Overview

The FactoryPulse AI backend is implemented using FastAPI and follows a modular architecture designed to support the platform's API, authentication, database access, monitoring services, AI/ML integration, alerts, maintenance management, notifications, and reporting.

The backend is located in:

`backend/`

The application source code is located in:

`backend/app/`

The implementation is being developed incrementally, with each major component isolated into dedicated Python packages.

---

## 2. Backend Technology Stack

The current backend stack includes:

- **FastAPI** — REST API framework
- **Uvicorn** — ASGI development server
- **Pydantic Settings** — application configuration and environment variable management
- **SQLAlchemy** — ORM and database abstraction layer
- **SQLAlchemy AsyncIO** — asynchronous database access
- **asyncpg** — asynchronous PostgreSQL driver
- **PostgreSQL** — target relational database
- **Alembic** — database schema migration management

Exact dependency versions are pinned in:

`backend/requirements.txt`

---

## 3. Current Backend Structure

The current backend structure is:

```text
backend/
├── .env
├── .env.example
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py
    │
    ├── api/
    │   ├── __init__.py
    │   └── health.py
    │
    ├── core/
    │   ├── __init__.py
    │   └── config.py
    │
    └── db/
        ├── __init__.py
        ├── base.py
        └── session.py
        
```

---

## 4. PostgreSQL Local Development Setup

PostgreSQL 18.4 is installed directly on Windows for local development.

The database server runs as a Windows service:

`postgresql-x64-18`

The PostgreSQL service has been verified as running successfully.

The default PostgreSQL port is:

`5432`

A dedicated application database user has been created:

`factorypulse`

A dedicated application database has also been created:

`factorypulse`

The database is owned by the `factorypulse` application user.

The backend connects to PostgreSQL through the environment variable:

`DATABASE_URL`

Current local development format:

```env
DATABASE_URL=postgresql+asyncpg://factorypulse:factorypulse@localhost:5432/factorypulse
```

The real database connection string is stored in:

`backend/.env`

The safe example configuration is stored in:

`backend/.env.example`

The real `.env` file is excluded from Git.

---

## 5. Alembic Migration Infrastructure

Alembic has been installed and initialized using the asynchronous template.

The migration configuration is located in:

```
backend/alembic.ini
```

The migration environment is located in:

```
backend/alembic/
```

Important generated files include:

```
backend/alembic/
├── README
├── env.py
├── script.py.mako
└── versions/
```

The `versions/` directory will contain the database migration files generated during development.

Alembic is configured to use the same database URL as the FastAPI application.

The connection URL is loaded from:

```
settings.database_url
```

inside:

```
backend/alembic/env.py
```

Alembic is also connected to SQLAlchemy metadata through:

```
target_metadata = Base.metadata
```

This allows Alembic to automatically detect changes in SQLAlchemy ORM models when generating migrations.

The Alembic configuration has been tested successfully using:

```
alembic current
```

The output confirmed that Alembic connected successfully to PostgreSQL and detected the PostgreSQL dialect.

No current migration revision is shown yet because no migration has been created.

---

## 6. Database Development Workflow

The backend database workflow will follow this process:

```
SQLAlchemy ORM Model
        ↓
Base.metadata
        ↓
Alembic detects schema changes
        ↓
Migration file generated
        ↓
Migration reviewed
        ↓
Migration applied to PostgreSQL
```

This approach provides version-controlled database schema evolution and avoids manually creating or modifying production tables.

The next major milestone is:

**Implementation of the first SQLAlchemy ORM models and generation of the first Alembic migration.**

````

Also, because we just created:

```text
backend/app/models/
````

````
---

## 7. ORM Model Architecture

SQLAlchemy ORM models are stored in:

`backend/app/models/`

Current structure:

```text
backend/app/models/
├── __init__.py
└── user.py
````

All ORM models inherit from the common SQLAlchemy declarative base defined in:

`backend/app/db/base.py`

The models package is imported by the Alembic migration environment so that model definitions are registered in `Base.metadata`.

This allows Alembic's autogeneration system to detect changes to the ORM schema.

---

## 8. User ORM Model

The first implemented ORM entity is the `User` model.

It is defined in:

`backend/app/models/user.py`

The model maps to the PostgreSQL table:

`users`

Current fields:

|Field|Type|Description|
|---|---|---|
|`id`|Integer|Primary key|
|`email`|String(255)|Unique user email|
|`full_name`|String(150)|User's full name|
|`hashed_password`|String(255)|Secure password hash|
|`is_active`|Boolean|Controls whether the account is active|
|`created_at`|DateTime|Account creation timestamp|

The `email` column is unique and indexed to support efficient user lookup.

The `id` column uses PostgreSQL's primary-key index and therefore does not define an additional redundant index.

Passwords will never be stored as plain text. The `hashed_password` field will store only password hashes once the authentication layer is implemented.

---

## 9. First Database Migration

Alembic successfully detected the `User` ORM model using:

```
alembic revision --autogenerate -m "create users table"
```

The generated migration revision is:

```
1396225e8511
```

Migration file:

```
backend/alembic/versions/1396225e8511_create_users_table.py
```

Before applying the migration, the generated schema was reviewed manually.

A redundant index on the primary key was identified and removed from the ORM definition before regenerating the migration.

The final migration creates:

- `users` table
- primary key on `users.id`
- unique index on `users.email`
- server-generated `created_at` timestamp

The migration was applied using:

```
alembic upgrade head
```

Alembic confirmed:

```
Running upgrade -> 1396225e8511, create users table
```

The current database revision was verified using:

```
alembic current
```

Current revision:

```
1396225e8511 (head)
```

This confirms that the PostgreSQL database schema and the latest Alembic migration are synchronized.

---

## 10. Current Database Migration Workflow

The working schema-development process is now:

```
Create / modify SQLAlchemy model
            ↓
Import model into models package
            ↓
Alembic reads Base.metadata
            ↓
alembic revision --autogenerate
            ↓
Review generated migration
            ↓
alembic upgrade head
            ↓
Verify current migration revision
```

Generated migrations must always be reviewed before being applied to the database.


## 11. Role ORM Model

The second implemented ORM entity is the `Role` model.

It is defined in:

`backend/app/models/role.py`

The model maps to the PostgreSQL table:

`roles`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(50) | Unique role name |
| `description` | String(255) | Optional role description |

The `name` field is unique to prevent duplicate roles.

Examples of future role values may include:

- `admin`
- `operator`
- `maintenance`

The model is registered through:

`backend/app/models/__init__.py`

which allows Alembic to detect it through `Base.metadata`.

---

## 12. Role Database Migration

Alembic detected the new `roles` table using:

`alembic revision --autogenerate -m "create roles table"`

Generated migration revision:

`add1b368d851`

Previous revision:

`1396225e8511`

This creates the migration chain:

```text
1396225e8511
    ↓
add1b368d851
````


The migration creates:

- `roles` table
- primary key on `roles.id`
- unique constraint on `roles.name`

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`add1b368d851 (head)`

The physical PostgreSQL table was verified directly using `psql`.

Current database tables include:

```
alembic_version
users
roles
```

The `roles` table structure and constraints match the SQLAlchemy ORM definition.



---

## 13. User–Role Relationship

A relationship has been implemented between the `User` and `Role` ORM models.

The `users` table now contains:

`role_id`

This column references:

`roles.id`

The database relationship is defined using a foreign key:

```text
users.role_id → roles.id
````

The `role_id` field is currently nullable, allowing a user to exist temporarily without an assigned role.

On the ORM side, the relationship is bidirectional.

From a user object:

```
user.role
```

returns the associated role.

From a role object:

```
role.users
```

returns the users assigned to that role.

The migration was generated using:

```
alembic revision --autogenerate -m "link users to roles"
```

Generated revision:

```
a523ff7903c2
```

Previous revision:

```
add1b368d851
```

The migration added:

- `users.role_id`
- foreign key from `users.role_id` to `roles.id`

The migration was applied using:

```
alembic upgrade head
```

Current migration revision:

```
a523ff7903c2 (head)
```

The relationship was verified directly in PostgreSQL.

The `users` table now contains the foreign-key constraint:

```
users_role_id_fkey
FOREIGN KEY (role_id) REFERENCES roles(id)
```

This confirms that the ORM relationship and the physical PostgreSQL schema are synchronized.


---

## 14. Machine ORM Model

The `Machine` ORM model has been implemented to represent industrial machines/assets monitored by FactoryPulse AI.

It is defined in:

`backend/app/models/machine.py`

The model maps to the PostgreSQL table:

`machines`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(120) | Human-readable machine name |
| `code` | String(50) | Unique machine identifier |
| `location` | String(150) | Optional physical location |
| `status` | String(30) | Current machine status |
| `created_at` | DateTime | Machine creation timestamp |

The `code` field is unique to prevent duplicate machine identifiers.

The default machine status is currently:

`active`

The `created_at` field uses a PostgreSQL server-generated timestamp.

---

## 15. Machine Database Migration

Alembic detected the new `machines` table using:

`alembic revision --autogenerate -m "create machines table"`

Generated migration revision:

`6564f4c87934`

Previous revision:

`a523ff7903c2`

The migration creates:

- `machines` table
- primary key on `machines.id`
- unique constraint on `machines.code`
- server-generated `created_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`6564f4c87934 (head)`

The physical PostgreSQL table was verified directly using `psql`.

The verified constraints include:

```text
machines_pkey PRIMARY KEY (id)
machines_code_key UNIQUE (code)
````

This confirms that the SQLAlchemy ORM model, Alembic migration, and PostgreSQL schema are synchronized.



---

## 16. Sensor ORM Model

The `Sensor` ORM model has been implemented to represent sensors attached to industrial machines.

It is defined in:

`backend/app/models/sensor.py`

The model maps to the PostgreSQL table:

`sensors`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `machine_id` | Integer | Foreign key referencing the owning machine |
| `name` | String(120) | Sensor display name |
| `sensor_type` | String(50) | Sensor category/type |
| `unit` | String(30) | Measurement unit |
| `status` | String(30) | Current sensor status |
| `created_at` | DateTime | Sensor creation timestamp |

The `machine_id` field is required and references:

`machines.id`

This creates the database relationship:

```text
sensors.machine_id → machines.id
````

The ORM relationship is bidirectional.

From a sensor object:

```
sensor.machine
```

returns the machine to which the sensor belongs.

From a machine object:

```
machine.sensors
```

returns the sensors associated with that machine.

---

## 17. Sensor Database Migration

Alembic detected the new `sensors` table using:

`alembic revision --autogenerate -m "create sensors table"`

Generated migration revision:

`8b5591f66360`

Previous revision:

`6564f4c87934`

The migration creates:

- `sensors` table
- primary key on `sensors.id`
- foreign key from `sensors.machine_id` to `machines.id`
- server-generated `created_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

The physical PostgreSQL table was verified directly using `psql`.

The verified foreign-key constraint is:

```
sensors_machine_id_fkey
FOREIGN KEY (machine_id) REFERENCES machines(id)
```

This confirms that the SQLAlchemy ORM model, Alembic migration, and PostgreSQL schema are synchronized.


---

## 18. SensorReading ORM Model

The `SensorReading` ORM model has been implemented to store time-series measurements produced by sensors.

It is defined in:

`backend/app/models/sensor_reading.py`

The model maps to the PostgreSQL table:

`sensor_readings`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `sensor_id` | Integer | Foreign key referencing the source sensor |
| `value` | Float | Numeric sensor measurement |
| `recorded_at` | DateTime | Timestamp when the reading was recorded |

The `sensor_id` field is required and references:

`sensors.id`

This creates the database relationship:

```text
sensor_readings.sensor_id → sensors.id
````

The ORM relationship is bidirectional.

From a sensor reading:

```
reading.sensor
```

returns the source sensor.

From a sensor:

```
sensor.readings
```

returns the collection of measurements associated with that sensor.

---

## 19. SensorReading Database Migration

Alembic detected the new `sensor_readings` table using:

`alembic revision --autogenerate -m "create sensor readings table"`

Generated migration revision:

`8735dbc45b11`

Previous revision:

`8b5591f66360`

The migration creates:

- `sensor_readings` table
- primary key on `sensor_readings.id`
- foreign key from `sensor_readings.sensor_id` to `sensors.id`
- server-generated `recorded_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`8735dbc45b11 (head)`

The physical PostgreSQL table was verified directly using `psql`.

The verified foreign-key constraint is:

```
sensor_readings_sensor_id_fkey
FOREIGN KEY (sensor_id) REFERENCES sensors(id)
```

The current core monitoring hierarchy is now:

```
Machine
   ↓
Sensor
   ↓
SensorReading
```

This structure provides the foundation for storing time-series machine data that will later be used by anomaly detection, prediction, monitoring, and alerting components.



---

## 20. Prediction ORM Model

The `Prediction` ORM model has been implemented to store AI/ML prediction outputs associated with sensors.

It is defined in:

`backend/app/models/prediction.py`

The model maps to the PostgreSQL table:

`predictions`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `sensor_id` | Integer | Foreign key referencing the related sensor |
| `predicted_value` | Float | Predicted numerical value |
| `anomaly_score` | Float | Optional anomaly or risk score |
| `is_anomaly` | Boolean | Indicates whether the prediction is considered anomalous |
| `model_name` | String(100) | Name of the model that generated the prediction |
| `model_version` | String(50) | Optional model version |
| `predicted_at` | DateTime | Timestamp when the prediction was produced |

The `sensor_id` field is required and references:

`sensors.id`

This creates the database relationship:

```text
predictions.sensor_id → sensors.id
````

The ORM relationship is bidirectional.

From a prediction:

```
prediction.sensor
```

returns the related sensor.

From a sensor:

```
sensor.predictions
```

returns the predictions associated with that sensor.

---

## 21. Prediction Database Migration

Alembic detected the new `predictions` table using:

`alembic revision --autogenerate -m "create predictions table"`

Generated migration revision:

`546cde60faa9`

Previous revision:

`8735dbc45b11`

The migration creates:

- `predictions` table
- primary key on `predictions.id`
- foreign key from `predictions.sensor_id` to `sensors.id`
- server-generated `predicted_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`546cde60faa9 (head)`

The physical PostgreSQL table was verified directly using `psql`.

The verified foreign-key constraint is:

```
predictions_sensor_id_fkey
FOREIGN KEY (sensor_id) REFERENCES sensors(id)
```

This confirms that the SQLAlchemy ORM model, Alembic migration, and PostgreSQL schema are synchronized.

The current monitoring and AI persistence structure is now:

```
Machine
   ↓
Sensor
   ├── SensorReading
   └── Prediction
```



---

## 22. Alert ORM Model

The `Alert` ORM model has been implemented to store alerts generated from abnormal sensor conditions and AI/ML prediction results.

It is defined in:

`backend/app/models/alert.py`

The model maps to the PostgreSQL table:

`alerts`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `sensor_id` | Integer | Foreign key referencing the related sensor |
| `prediction_id` | Integer | Optional foreign key referencing a prediction |
| `severity` | String(30) | Alert severity level |
| `title` | String(150) | Short alert title |
| `message` | Text | Full alert description |
| `status` | String(30) | Current alert state |
| `created_at` | DateTime | Timestamp when the alert was created |

The `sensor_id` field is required and references:

`sensors.id`

The optional `prediction_id` field references:

`predictions.id`

This allows FactoryPulse AI to support both:

- rule-based alerts generated directly from sensor conditions
- AI-generated alerts linked to anomaly or prediction results

The database relationships are:

```text
alerts.sensor_id → sensors.id
alerts.prediction_id → predictions.id
````

The ORM relationships are bidirectional.

From an alert:

```
alert.sensor
alert.prediction
```

From a sensor:

```
sensor.alerts
```

From a prediction:

```
prediction.alerts
```

---

## 23. Alert Database Migration

Alembic detected the new `alerts` table using:

`alembic revision --autogenerate -m "create alerts table"`

Generated migration revision:

`ac2ac07e6fc4`

Previous revision:

`546cde60faa9`

The migration creates:

- `alerts` table
- primary key on `alerts.id`
- foreign key from `alerts.sensor_id` to `sensors.id`
- optional foreign key from `alerts.prediction_id` to `predictions.id`
- server-generated `created_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`ac2ac07e6fc4 (head)`

The physical PostgreSQL table was verified directly using `psql`.

Verified constraints:

```
alerts_sensor_id_fkey
FOREIGN KEY (sensor_id) REFERENCES sensors(id)

alerts_prediction_id_fkey
FOREIGN KEY (prediction_id) REFERENCES predictions(id)
```

The current monitoring and alert persistence structure is now:

```
Machine
   ↓
Sensor
   ├── SensorReading
   ├── Prediction
   └── Alert
        └── optional Prediction
```


---

## 24. MaintenanceRecord ORM Model

The `MaintenanceRecord` ORM model has been implemented to store maintenance activity performed on industrial machines.

It is defined in:

`backend/app/models/maintenance_record.py`

The model maps to the PostgreSQL table:

`maintenance_records`

Current fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary key |
| `machine_id` | Integer | Foreign key referencing the maintained machine |
| `alert_id` | Integer | Optional foreign key referencing the related alert |
| `performed_by_user_id` | Integer | Optional foreign key referencing the responsible user/technician |
| `maintenance_type` | String(50) | Type of maintenance activity |
| `description` | Text | Detailed maintenance description |
| `status` | String(30) | Current maintenance state |
| `performed_at` | DateTime | Optional timestamp when maintenance was performed |
| `created_at` | DateTime | Timestamp when the record was created |

The `machine_id` field is required and references:

`machines.id`

The optional `alert_id` field references:

`alerts.id`

The optional `performed_by_user_id` field references:

`users.id`

The database relationships are:

```text
maintenance_records.machine_id → machines.id
maintenance_records.alert_id → alerts.id
maintenance_records.performed_by_user_id → users.id

````

The ORM relationships are bidirectional.
From a maintenance record:
From a maintenance record:

maintenance_record.machine

maintenance_record.alert

maintenance_record.performed_by

From a machine:

machine.maintenance_records

From an alert:

alert.maintenance_records

From a user:

user.maintenance_records

## 25. MaintenanceRecord Database Migration

Alembic detected the new `maintenance_records` table using:

`alembic revision --autogenerate -m "create maintenance records table"`

Generated migration revision:

`75faada7868d`

Previous revision:

`ac2ac07e6fc4`

The migration creates:

- `maintenance_records` table
- primary key on `maintenance_records.id`
- foreign key from `maintenance_records.machine_id` to `machines.id`
- optional foreign key from `maintenance_records.alert_id` to `alerts.id`
- optional foreign key from `maintenance_records.performed_by_user_id` to `users.id`
- server-generated `created_at` timestamp

The migration was reviewed before being applied.

It was applied using:

`alembic upgrade head`

Current database revision:

`75faada7868d (head)`

The physical PostgreSQL table was verified directly using `psql`.

Verified foreign-key constraints:

maintenance_records_alert_id_fkey

FOREIGN KEY (alert_id) REFERENCES alerts(id)

  

maintenance_records_machine_id_fkey

FOREIGN KEY (machine_id) REFERENCES machines(id)

  

maintenance_records_performed_by_user_id_fkey

FOREIGN KEY (performed_by_user_id) REFERENCES users(id)

The current operational persistence structure now includes:

Machine

   ├── Sensor

   │    ├── SensorReading

   │    ├── Prediction

   │    └── Alert

   └── MaintenanceRecord

        ├── optional Alert

        └── optional User




## 26. Notification ORM Model

The `Notification` ORM model has been implemented to persist notifications delivered to users.

It is defined in:

`backend/app/models/notification.py`

The model maps to:

`notifications`

Fields:

- `id` — primary key
- `user_id` — required foreign key to `users.id`
- `alert_id` — optional foreign key to `alerts.id`
- `title` — notification title
- `message` — notification body
- `channel` — delivery channel such as `in_app`, `email`, or `sms`
- `is_read` — tracks whether the user has read the notification
- `created_at` — server-generated creation timestamp

Relationships:

```text
notifications.user_id → users.id
notifications.alert_id → alerts.id
```

Bidirectional ORM access:

notification.user

notification.alert

  

user.notifications

alert.notifications

## 27. Notification Database Migration

Alembic generated the notification migration using:

`alembic revision --autogenerate -m "create notifications table"`

Migration revision:

`9e42d11f73be`

Previous revision:

`75faada7868d`

The migration creates the `notifications` table together with its primary key and foreign-key constraints.

The migration was applied with:

`alembic upgrade head`

The physical PostgreSQL table was verified directly using `psql`.
\


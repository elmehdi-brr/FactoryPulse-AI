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



------

## 28. Pydantic Schema Layer

The backend Pydantic schema layer has been implemented under:

`backend/app/schemas/`

Its purpose is to define the structure of data accepted by and returned from the FactoryPulse AI API.

The current schema package contains:

```text
app/schemas/
├── __init__.py
├── alert.py
├── machine.py
├── maintenance_record.py
├── notification.py
├── prediction.py
├── role.py
├── sensor.py
├── sensor_reading.py
└── user.py
```

### Machine Schemas

Implemented schemas:

- `MachineCreate`
- `MachineUpdate`
- `MachineResponse`

These schemas support machine creation, partial updates, and API responses.

### Sensor Schemas

Implemented schemas:

- `SensorCreate`
- `SensorUpdate`
- `SensorResponse`

Sensors are associated with machines through `machine_id`.

### SensorReading Schemas

Implemented schemas:

- `SensorReadingCreate`
- `SensorReadingResponse`

Sensor readings contain the sensor identifier, measured value, and recorded timestamp.

### Prediction Schemas

Implemented schemas:

- `PredictionCreate`
- `PredictionResponse`

Prediction schemas support AI-generated values, anomaly scores, anomaly state, model name, and model version.

### Alert Schemas

Implemented schemas:

- `AlertCreate`
- `AlertUpdate`
- `AlertResponse`

Alerts can be associated with both a sensor and an optional prediction.

### MaintenanceRecord Schemas

Implemented schemas:

- `MaintenanceRecordCreate`
- `MaintenanceRecordUpdate`
- `MaintenanceRecordResponse`

Maintenance records support machine maintenance tracking, optional alert references, responsible users, maintenance type, status, description, and execution time.

### Notification Schemas

Implemented schemas:

- `NotificationCreate`
- `NotificationUpdate`
- `NotificationResponse`

Notifications are associated with users and may optionally reference an alert.

They support notification channels and read/unread states.

### Role Schemas

Implemented schemas:

- `RoleCreate`
- `RoleUpdate`
- `RoleResponse`

These schemas provide validation for application roles.

### User Schemas

Implemented schemas:

- `UserCreate`
- `UserUpdate`
- `UserResponse`

The API accepts a plain `password` during user creation or password updates.

The database model itself stores the resulting hashed value in `hashed_password`.

Passwords must therefore be hashed in the service/authentication layer before persistence.

### ORM Serialization

Response schemas use:

ConfigDict(from_attributes=True)

This allows Pydantic to serialize SQLAlchemy ORM objects directly into API response models.

### Schema Package Registration

All public schemas are exported through:

`app/schemas/__init__.py`

The complete schema package was verified using:

python -c "import app.schemas; print('All schemas imported successfully')"

Result:

All schemas imported successfully

The Pydantic schema layer is now ready to be consumed by the service and API layers.


---

## 29. Machine Service Layer

The first backend service layer has been implemented for the `Machine` entity.

It is located in:

`backend/app/services/machine_service.py`

The service separates database operations from the HTTP API layer.

Implemented operations:

- `create_machine()`
- `get_machine_by_id()`
- `get_machines()`
- `update_machine()`
- `delete_machine()`

The service uses SQLAlchemy `AsyncSession` for asynchronous PostgreSQL operations.

### Create

`create_machine()` converts a validated `MachineCreate` schema into a SQLAlchemy `Machine` object.

The object is added to the database session, committed, and refreshed so PostgreSQL-generated values such as `id` and `created_at` are available.

### Read

`get_machine_by_id()` retrieves one machine using its primary key.

`get_machines()` retrieves all machines ordered by ID.

### Update

`update_machine()` uses:

```python
machine_data.model_dump(exclude_unset=True)
```

This allows PATCH operations to modify only fields explicitly provided by the client.

### Delete

`delete_machine()` removes the SQLAlchemy object and commits the transaction.

---

## 30. Machine REST API

The Machine REST API has been implemented in:

`backend/app/api/machines.py`

The router uses:

Prefix: /machines

Tag: Machines

Implemented endpoints:

POST   /machines

GET    /machines

GET    /machines/{machine_id}

PATCH  /machines/{machine_id}

DELETE /machines/{machine_id}

The router uses the Machine service layer for database operations and the Pydantic Machine schemas for request validation and response serialization.

The router is registered in:

`backend/app/main.py`

using:

app.include_router(machines_router)

### HTTP Behavior

Successful creation:

POST /machines → 201 Created

Successful reads and updates:

GET /machines → 200 OK

GET /machines/{machine_id} → 200 OK

PATCH /machines/{machine_id} → 200 OK

Successful deletion:

DELETE /machines/{machine_id} → 204 No Content

Missing machines return:

404 Not Found

with:

{

  "detail": "Machine not found"

}

---

## 31. Machine CRUD Integration Test

The complete Machine CRUD lifecycle was manually tested through FastAPI Swagger UI.

Test machine:

Name: Production Line Motor 01

Code: MOTOR-001

Location: Factory Floor A

Status: active

### Create Test

`POST /machines`

Result:

201 Created

PostgreSQL generated:

id = 1

created_at = server-generated timestamp

### Read Test

`GET /machines`

Result:

200 OK

The previously created machine was successfully retrieved from PostgreSQL.

### Update Test

`PATCH /machines/1`

Request:

{

  "location": "Factory Floor B",

  "status": "maintenance"

}

Result:

200 OK

Only the provided fields were modified.

### Read-by-ID Test

`GET /machines/1`

Result:

200 OK

The updated values were successfully retrieved from PostgreSQL.

### Delete Test

`DELETE /machines/1`

Result:

204 No Content

A subsequent request to:

`GET /machines/1`

returned:

404 Not Found

confirming that the database record had been deleted.

The first complete PostgreSQL-backed CRUD REST API in FactoryPulse AI is therefore operational.

Current architecture:

Swagger / Client

       ↓

FastAPI Router

       ↓

Pydantic Schemas

       ↓

Machine Service

       ↓

SQLAlchemy ORM

       ↓

PostgreSQL

---

## 32. Sensor Service Layer

The Sensor service layer has been implemented in:

`backend/app/services/sensor_service.py`

Implemented operations:

- `create_sensor()`
- `get_sensor_by_id()`
- `get_sensors()`
- `update_sensor()`
- `delete_sensor()`

The service uses SQLAlchemy `AsyncSession` and follows the same CRUD architecture established for machines.

---

## 33. Sensor REST API

The Sensor API has been implemented in:

`backend/app/api/sensors.py`

Implemented endpoints:

```text
POST   /sensors
GET    /sensors
GET    /sensors/{sensor_id}
PATCH  /sensors/{sensor_id}
DELETE /sensors/{sensor_id}
```


The Sensor router is registered in:

`backend/app/main.py`

The API validates the `machine_id` before creating or moving a sensor.

If the referenced machine does not exist, the API returns:

404 Not Found

with:

{

  "detail": "Machine not found"

}

This prevents sensors from being associated with nonexistent machines.

---

## 34. Machine–Sensor Integration Test

A real machine was created through:

`POST /machines`

The created machine received:

id = 2

A sensor was then created using:

{

  "machine_id": 2,

  "name": "Motor Temperature Sensor",

  "sensor_type": "temperature",

  "unit": "°C",

  "status": "active"

}

Result:

201 Created

The sensor received:

id = 1

machine_id = 2

This confirmed the working relationship:

Machine #2

   ↓

Sensor #1

The following Sensor CRUD operations were successfully tested through Swagger:

POST   /sensors              → 201 Created

GET    /sensors/{sensor_id}  → 200 OK

PATCH  /sensors/{sensor_id}  → 200 OK

DELETE /sensors/{sensor_id}  → 204 No Content

After deletion:

GET /sensors/1

returned:

404 Not Found

with:

{

  "detail": "Sensor not found"

}

The Sensor CRUD API and Machine–Sensor relationship are therefore operational.

Current backend flow:

Client / Swagger

       ↓

FastAPI Sensor Router

       ↓

Pydantic Sensor Schemas

       ↓

Sensor Service

       ↓

SQLAlchemy ORM

       ↓

PostgreSQL

       ↓

Machine ↔ Sensor relationship


---

## 35. SensorReading Service Layer

The SensorReading service layer has been implemented in:

`backend/app/services/sensor_reading_service.py`

Unlike standard CRUD entities, sensor readings are treated primarily as historical time-series data.

Implemented operations:

- `create_sensor_reading()`
- `get_sensor_reading_by_id()`
- `get_sensor_readings()`
- `get_readings_by_sensor()`

Sensor readings are ordered by `recorded_at` in descending order so the most recent measurements are returned first.

Update and delete operations have intentionally not been added at this stage because sensor measurements represent historical industrial observations.

---

## 36. SensorReading REST API

The SensorReading REST API has been implemented in:

`backend/app/api/sensor_readings.py`

Implemented endpoints:

```text
POST /sensor-readings
GET  /sensor-readings
GET  /sensor-readings/{reading_id}
GET  /sensors/{sensor_id}/readings
```

The router is registered in:

`backend/app/main.py`

Before a reading is created, the API verifies that the referenced sensor exists.

If the sensor does not exist, the API returns:

404 Not Found

with:

{

  "detail": "Sensor not found"

}

This prevents orphan sensor readings from being stored.

---

## 37. SensorReading Integration Test

A sensor reading was successfully created for an existing temperature sensor.

Example measurement:

Temperature = 72.6 °C

The complete data relationship was successfully tested:

Machine

   ↓

Sensor

   ↓

SensorReading

   ↓

PostgreSQL

The following API operations were verified through Swagger:

POST /sensor-readings

→ 201 Created

  

GET /sensor-readings

→ 200 OK

  

GET /sensor-readings/{reading_id}

→ 200 OK

  

GET /sensors/{sensor_id}/readings

→ 200 OK

The sensor-specific readings endpoint confirms that FactoryPulse can retrieve the historical measurements belonging to one sensor.

A reading creation request using a nonexistent sensor was also tested.

Example:

{

  "sensor_id": 999,

  "value": 85.3

}

Result:

404 Not Found

Response:

{

  "detail": "Sensor not found"

}

This confirms that SensorReading integrity is enforced at the API layer.

FactoryPulse can now persist actual industrial time-series measurements.

Current industrial data pipeline:

Machine

   ↓

Sensor

   ↓

SensorReading

   ↓

Historical Time-Series Data

   ↓

PostgreSQL

---

## 38. Prediction Service Layer

The Prediction service layer has been implemented in:

`backend/app/services/prediction_service.py`

Implemented operations:

- `create_prediction()`
- `get_prediction_by_id()`
- `get_predictions()`
- `get_predictions_by_sensor()`

Predictions are ordered by `predicted_at` in descending order.

The service persists AI prediction outputs such as:

- predicted value
- anomaly score
- anomaly status
- model name
- model version

At this stage, prediction values are manually supplied for backend testing.

The actual machine-learning pipeline will generate these values later.

---

## 39. Prediction REST API

The Prediction API has been implemented in:

`backend/app/api/predictions.py`

Implemented endpoints:

```text
POST /predictions
GET  /predictions
GET  /predictions/{prediction_id}
GET  /sensors/{sensor_id}/predictions
```

Before creating a prediction, the API verifies that the referenced sensor exists.

A nonexistent sensor returns:

404 Not Found

with:

{

  "detail": "Sensor not found"

}

This prevents orphan prediction records.

---

## 40. Prediction Integration Test

A test AI-style prediction was successfully persisted.

Example:
```

sensor_id = 2

predicted_value = 78.4

anomaly_score = 0.87

is_anomaly = true

model_name = xgboost

model_version = 1.0
```


The following endpoints were successfully tested:
```

POST /predictions
→ 201 Created
GET /predictions
→ 200 OK
GET /sensors/{sensor_id}/predictions
→ 200 OK
```
The current industrial intelligence pipeline is now:

Machine

   ↓

Sensor

   ↓

SensorReading

   ↓

Prediction

   ├── predicted_value

   ├── anomaly_score

   ├── is_anomaly

   ├── model_name

   └── model_version

   ↓

PostgreSQL

The Prediction persistence layer is ready to receive outputs from the future AI/anomaly-detection engine.


---

## 41. Alert Service Layer

The Alert service layer has been implemented in:

`backend/app/services/alert_service.py`

Implemented operations:

- `create_alert()`
- `get_alert_by_id()`
- `get_alerts()`
- `get_alerts_by_sensor()`
- `update_alert()`

Alerts are ordered by `created_at` in descending order.

Unlike standard CRUD entities, alerts are not deleted at this stage because they represent important operational history.

Instead, alerts can move through states such as:

`open → acknowledged → resolved`

The service supports partial updates using:

`model_dump(exclude_unset=True)`

This allows an API client to modify only selected alert fields without replacing the entire record.

---

## 42. Alert REST API

The Alert REST API has been implemented in:

`backend/app/api/alerts.py`

Implemented endpoints:

`POST /alerts`

`GET /alerts`

`GET /alerts/{alert_id}`

`GET /sensors/{sensor_id}/alerts`

`PATCH /alerts/{alert_id}`

The Alert router is registered in:

`backend/app/main.py`

Before an alert is created, FactoryPulse validates that the referenced sensor exists.

If the sensor does not exist, the API returns:

`404 Not Found`

The optional `prediction_id` is also validated.

If a prediction ID is provided, the API verifies:

1. The prediction exists.
2. The prediction belongs to the same sensor referenced by the alert.

This prevents inconsistent industrial relationships such as:

`Alert.sensor_id = 3`

while:

`Prediction.sensor_id = 2`

In that situation, the API returns:

`400 Bad Request`

with:

`Prediction does not belong to the specified sensor`

---

## 43. Alert Integration Test

A real alert was created and linked to an existing AI-style prediction.

Test alert:

`Sensor ID: 2`

`Prediction ID: 1`

`Severity: high`

`Title: Abnormal motor temperature detected`

`Message: The AI model detected an abnormal temperature pattern for this motor.`

`Status: open`

The alert was created using:

`POST /alerts`

Result:

`201 Created`

The alert received:

`id = 1`

and a server-generated `created_at` timestamp.

The following read operations were successfully tested:

`GET /alerts → 200 OK`

`GET /alerts/{alert_id} → 200 OK`

The alert status was then updated using:

`PATCH /alerts/1`

with:

`status = acknowledged`

Result:

`200 OK`

A subsequent read confirmed that the new status was persisted.

During testing, Swagger's automatically generated `"string"` example values were accidentally submitted in an earlier PATCH request.

Those values were subsequently restored correctly.

This confirmed that partial updates using `exclude_unset=True` behave as expected: only fields explicitly included in a PATCH request are changed.

---

## 44. Prediction–Sensor Consistency Validation

A second temporary sensor was created in order to test relationship consistency.

The existing prediction belonged to:

`Sensor #2`

An invalid alert creation was deliberately attempted using:

`Sensor #3`

together with:

`Prediction #1`

Because Prediction #1 belongs to Sensor #2, FactoryPulse rejected the request.

Result:

`400 Bad Request`

Response:

`Prediction does not belong to the specified sensor`

This confirms that FactoryPulse enforces the relationship:

`Alert.sensor_id = Prediction.sensor_id`

when a prediction is attached to an alert.

The temporary test sensor was then deleted successfully.

The complete operational intelligence pipeline currently implemented is:

`Machine`
`↓`
`Sensor`
`↓`
`SensorReading`
`↓`
`Prediction`
`↓`
`Alert`

At this stage:

- machines can be managed through the API
- sensors can be attached to machines
- real sensor readings can be stored
- AI-style prediction outputs can be persisted
- anomaly predictions can be converted into operational alerts
- alert status can be managed
- invalid sensor/prediction relationships are rejected

The next milestone is:

**Implement the Notification service and REST API so alerts can be delivered to FactoryPulse users.**

---

## 45. Notification Service Layer

The Notification service layer has been implemented in:

`backend/app/services/notification_service.py`

Implemented operations:

- `create_notification()`
- `get_notification_by_id()`
- `get_notifications()`
- `get_notifications_by_user()`
- `update_notification()`

Notifications are ordered by `created_at` in descending order.

At this stage, notifications are not deleted because they can be useful as historical user-facing system records.

The update operation supports partial updates using:

`model_dump(exclude_unset=True)`

This is currently used primarily to modify the read/unread state of a notification.

---

## 46. Minimal User Lookup Service

A minimal User lookup service has been implemented in:

`backend/app/services/user_service.py`

Current operation:

- `get_user_by_id()`

The purpose of this service at the current stage is to validate that a notification references a real FactoryPulse user.

The complete User and Authentication subsystem has not yet been implemented.

This service will later be expanded as part of the authentication and authorization milestone.

---

## 47. Notification REST API

The Notification REST API has been implemented in:

`backend/app/api/notifications.py`

Implemented endpoints:

`POST /notifications`

`GET /notifications`

`GET /notifications/{notification_id}`

`GET /users/{user_id}/notifications`

`PATCH /notifications/{notification_id}`

The Notification router is registered in:

`backend/app/main.py`

Before a notification is created, FactoryPulse validates that the referenced user exists.

If the user does not exist, the API returns:

`404 Not Found`

with:

`User not found`

The optional `alert_id` is also validated.

If an alert ID is provided and does not exist, the API returns:

`404 Not Found`

with:

`Alert not found`

This prevents notifications from referencing invalid users or alerts.

---

## 48. Notification Integration Test

Because the full User/Auth API has not yet been implemented, a temporary development user was inserted directly into PostgreSQL for relationship testing.

Temporary development user:

`id = 1`

`email = operator@factorypulse.local`

`full_name = Factory Operator`

`is_active = true`

The `hashed_password` field contains a temporary development placeholder only.

This is not a real password hash and will be replaced by proper password hashing when the Authentication subsystem is implemented.

A notification was then created for the development user and linked to the existing operational alert.

Test relationship:

`Alert #1`
`↓`
`Notification #1`
`↓`
`User #1`

Example notification:

`Title: High temperature alert`

`Message: An abnormal motor temperature has been detected and requires attention.`

`Channel: in_app`

`is_read: false`

The notification was created using:

`POST /notifications`

Result:

`201 Created`

The user's notifications were retrieved using:

`GET /users/1/notifications`

Result:

`200 OK`

The notification was then marked as read using:

`PATCH /notifications/{notification_id}`

with:

`is_read = true`

Result:

`200 OK`

A subsequent response confirmed:

`is_read = true`

Validation tests were also performed.

A notification using a nonexistent user:

`user_id = 999`

was rejected with:

`404 Not Found`

`User not found`

A notification using a nonexistent alert:

`alert_id = 999`

was rejected with:

`404 Not Found`

`Alert not found`

The current operational intelligence flow is now:

`Machine`
`↓`
`Sensor`
`↓`
`SensorReading`
`↓`
`Prediction`
`↓`
`Alert`
`↓`
`Notification`
`↓`
`User`

FactoryPulse can therefore now take an AI-style anomaly result, turn it into an operational alert, and deliver that alert as a notification to a user.

The next milestone is:

**Implement the MaintenanceRecord service and REST API so FactoryPulse can track the real maintenance actions performed in response to industrial alerts.**

---

## 49. MaintenanceRecord Service Layer

The MaintenanceRecord service layer has been implemented in:

`backend/app/services/maintenance_record_service.py`

Implemented operations:

- `create_maintenance_record()`
- `get_maintenance_record_by_id()`
- `get_maintenance_records()`
- `get_maintenance_records_by_machine()`
- `update_maintenance_record()`

Maintenance records are ordered by `created_at` in descending order.

At this stage, maintenance records are not deleted because they represent important industrial maintenance history and should remain traceable.

Partial updates are supported using:

`model_dump(exclude_unset=True)`

This allows FactoryPulse to update only the fields explicitly supplied by the client.

---

## 50. MaintenanceRecord REST API

The MaintenanceRecord REST API has been implemented in:

`backend/app/api/maintenance_records.py`

Implemented endpoints:

`POST /maintenance-records`

`GET /maintenance-records`

`GET /maintenance-records/{record_id}`

`GET /machines/{machine_id}/maintenance-records`

`PATCH /maintenance-records/{record_id}`

The router is registered in:

`backend/app/main.py`

Before a maintenance record is created, FactoryPulse validates that the referenced machine exists.

If the machine does not exist, the API returns:

`404 Not Found`

with:

`Machine not found`

The optional `alert_id` is also validated.

If an alert is supplied, FactoryPulse verifies:

1. The alert exists.
2. The alert references an existing sensor.
3. The sensor belongs to the same machine referenced by the maintenance record.

This enforces the relationship:

`MaintenanceRecord.machine_id = Alert → Sensor → machine_id`

If the alert belongs to another machine, FactoryPulse returns:

`400 Bad Request`

with:

`Alert does not belong to the specified machine`

The optional `performed_by_user_id` is also validated.

If the referenced user does not exist, the API returns:

`404 Not Found`

with:

`User not found`

---

## 51. MaintenanceRecord Integration Test

A real maintenance intervention was successfully created and connected to the existing industrial alert.

Test relationship:

`Machine #2`

`↓`

`Alert #1`

`↓`

`MaintenanceRecord`

`↓`

`User #1`

The maintenance record contained:

`maintenance_type = corrective`

`description = Inspected the motor cooling system and cleaned the ventilation path after the high-temperature alert.`

`status = completed`

The responsible user was:

`User #1 - Factory Operator`

The record was created using:

`POST /maintenance-records`

Result:

`201 Created`

The record received a PostgreSQL-generated:

`id`

and:

`created_at`

timestamp.

The complete maintenance history was retrieved using:

`GET /maintenance-records`

Result:

`200 OK`

Machine-specific maintenance history was retrieved using:

`GET /machines/2/maintenance-records`

Result:

`200 OK`

This confirmed that FactoryPulse can retrieve the maintenance history associated with a specific industrial machine.

---

## 52. Maintenance Update and Relationship Validation

The maintenance record was updated through:

`PATCH /maintenance-records/{record_id}`

The following fields were modified:

`status = verified`

and the maintenance description was updated to reflect that the intervention had been verified.

Result:

`200 OK`

A subsequent request using:

`GET /maintenance-records/{record_id}`

returned:

`200 OK`

and confirmed that the updated information had been persisted in PostgreSQL.

A Machine–Alert consistency test was also performed.

A temporary second machine was created.

An invalid maintenance record was then deliberately submitted using:

- the temporary machine ID
- Alert #1

Alert #1 belongs to a sensor connected to Machine #2, not the temporary machine.

FactoryPulse correctly rejected the request.

Result:

`400 Bad Request`

Response:

`Alert does not belong to the specified machine`

This confirms that FactoryPulse prevents maintenance interventions from being incorrectly linked to alerts generated by another machine.

The temporary test machine was deleted after the validation test.

---

## 53. First Complete Operational Intelligence Pipeline

FactoryPulse now supports the complete initial backend workflow:

`Machine`

`↓`

`Sensor`

`↓`

`SensorReading`

`↓`

`Prediction`

`↓`

`Alert`

`↓`

`Notification`

`↓`

`User`

`↓`

`MaintenanceRecord`

The system can now:

- manage industrial machines
- attach sensors to machines
- store time-series sensor measurements
- persist AI-style prediction outputs
- store anomaly scores and anomaly states
- convert predictions into operational alerts
- validate Prediction–Sensor consistency
- deliver alerts as notifications to users
- track read/unread notification state
- record maintenance interventions
- associate maintenance actions with machines, alerts, and responsible users
- retrieve maintenance history for individual machines
- prevent invalid Machine–Alert maintenance relationships

This completes the first full operational backend loop of FactoryPulse AI.

The AI prediction values are still manually supplied during backend testing.

The real machine-learning inference engine will be integrated in a later milestone.

The broader FactoryPulse vision is not limited to machine monitoring or predictive maintenance. This pipeline forms the first industrial core upon which additional modules such as production monitoring, energy management, quality control, inventory, work orders, industrial analytics, and multi-site management can later be added.

Next milestone:

**Review the completed core backend and begin the next major backend area, including User Authentication and Role-Based Access Control before progressing toward automated AI inference and broader industrial modules.**


---

## 54. Authentication Service

The authentication service has been implemented in:

`backend/app/services/auth_service.py`

The service provides:

`authenticate_user()`

Authentication follows this process:

`Email`
`↓`
`Normalize and find user in PostgreSQL`
`↓`
`Verify password using Argon2`
`↓`
`Verify that the user is active`
`↓`
`Return authenticated User`

If the email does not exist, the password is incorrect, or the user is inactive, authentication fails.

Plain-text passwords are never stored in PostgreSQL.

Only Argon2 password hashes are stored in:

`users.hashed_password`

---

## 55. JWT Login API

The authentication API has been implemented in:

`backend/app/api/auth.py`

Current endpoint:

`POST /auth/login`

The login endpoint uses FastAPI's OAuth2 password form.

For FactoryPulse, the OAuth2 `username` field represents the user's email address.

Authentication flow:

`Email + Password`
`↓`
`authenticate_user()`
`↓`
`Argon2 password verification`
`↓`
`JWT access token generation`
`↓`
`Bearer token returned to the client`

A successful login returns:

`200 OK`

with a response containing:

`access_token`

and:

`token_type = bearer`

The JWT subject (`sub`) contains the authenticated user's database ID.

Using the stable user ID as the JWT subject allows the user's email address to change later without invalidating the identity model.

Invalid credentials return:

`401 Unauthorized`

with:

`Incorrect email or password`

---

## 56. Current User Authentication Dependency

A reusable authentication dependency has been implemented in:

`backend/app/api/dependencies.py`

The dependency:

`get_current_user()`

uses FastAPI's OAuth2 bearer-token mechanism.

Authentication of protected requests follows this flow:

`Authorization: Bearer <JWT>`
`↓`
`Extract access token`
`↓`
`Decode and validate JWT`
`↓`
`Read user ID from JWT subject`
`↓`
`Load user from PostgreSQL`
`↓`
`Verify user exists`
`↓`
`Verify user is active`
`↓`
`Return authenticated User`

Invalid, malformed, or expired credentials return:

`401 Unauthorized`

Inactive users return:

`403 Forbidden`

This dependency can now be reused by any FactoryPulse endpoint that requires authentication.

---

## 57. Authenticated User Endpoint

The following protected endpoint has been implemented:

`GET /auth/me`

The endpoint uses:

`get_current_user()`

and returns information about the user represented by the supplied JWT.

The endpoint was tested without authentication.

Result:

`401 Unauthorized`

The user was then authenticated through Swagger using:

`operator@factorypulse.local`

with the local development password.

After authorization:

`GET /auth/me`

returned:

`200 OK`

and correctly identified:

`User #1`

`Factory Operator`

This confirms the complete authentication flow:

`Email + Password`
`↓`
`Argon2 verification`
`↓`
`POST /auth/login`
`↓`
`JWT access token`
`↓`
`Bearer authentication`
`↓`
`JWT validation`
`↓`
`User loaded from PostgreSQL`
`↓`
`GET /auth/me`
`↓`
`Authenticated FactoryPulse User`

FactoryPulse can therefore now determine both:

`Who is attempting to log in?`

and:

`Who is making an authenticated API request?`

The next authentication milestone is:

**Implement Role-Based Access Control (RBAC) so FactoryPulse can determine what each authenticated user is allowed to do.**

---

## 58. Role-Based Access Control Foundation

FactoryPulse now includes the foundation for Role-Based Access Control (RBAC).

The central role definitions are located in:

`backend/app/core/rbac.py`

The current platform roles are:

- `admin`
- `manager`
- `technician`
- `operator`

These roles are represented through the `RoleName` enum so role names do not need to be repeatedly hard-coded throughout the backend.

The current role hierarchy is conceptual rather than strictly hierarchical.

Each endpoint will explicitly define which roles are permitted to access it.

The current intended responsibilities are:

`admin`

Full administrative access to FactoryPulse, including users, roles, configuration, and industrial resources.

`manager`

Management-oriented access to industrial operations, dashboards, reporting, alerts, and maintenance oversight.

`technician`

Technical and maintenance-oriented access to machines, sensors, alerts, and maintenance operations.

`operator`

Day-to-day monitoring and limited industrial operational access.

These permissions can be refined as FactoryPulse grows.

---

## 59. Reusable RBAC Dependency

A reusable RBAC authorization dependency has been implemented in:

`backend/app/api/dependencies.py`

The function:

`require_roles()`

can be attached to protected FastAPI endpoints.

The authorization flow is:

`Bearer JWT`

`↓`

`get_current_user()`

`↓`

`Authenticated User`

`↓`

`user.role_id`

`↓`

`Role loaded from PostgreSQL`

`↓`

`Compare current role with allowed endpoint roles`

`↓`

`Access granted or 403 Forbidden`

If the authenticated user has no assigned role, FactoryPulse returns:

`403 Forbidden`

with:

`User has no assigned role`

If the referenced role no longer exists, FactoryPulse returns:

`403 Forbidden`

with:

`User role does not exist`

If the user's role exists but is not permitted to access the endpoint, FactoryPulse returns:

`403 Forbidden`

with:

`Insufficient permissions`

The user's current role is loaded from PostgreSQL during authorization.

The JWT currently stores the user's ID rather than the user's role.

This means role changes can take effect without issuing a new JWT because FactoryPulse retrieves the user's current database role when checking access.

---

## 60. Standard RBAC Role Seeding

A reusable RBAC seed script has been implemented in:

`backend/app/scripts/seed_rbac.py`

The script creates the standard FactoryPulse roles:

`admin`

`manager`

`technician`

`operator`

The script is idempotent.

Running it multiple times does not create duplicate role records.

The development user:

`operator@factorypulse.local`

was automatically assigned the:

`operator`

role when the role data was seeded.

The following roles were verified directly in PostgreSQL:

`admin`

`manager`

`technician`

`operator`

The development user relationship was also verified:

`operator@factorypulse.local → operator`

---

## 61. RBAC Integration Test

A temporary admin-only endpoint was created to validate FactoryPulse authorization behavior.

The development user initially had:

`role = operator`

The user authenticated successfully using the existing JWT authentication system.

The operator then attempted to access the admin-only endpoint.

Result:

`403 Forbidden`

Response:

`Insufficient permissions`

The same development user was then temporarily assigned:

`role = admin`

The same authenticated request was executed again.

Result:

`200 OK`

Response:

`Admin access granted`

This verified both sides of the authorization mechanism:

`operator → admin-only endpoint → 403 Forbidden`

`admin → admin-only endpoint → 200 OK`

The development user was subsequently restored to:

`operator`

The temporary RBAC test endpoint was removed after successful verification.

FactoryPulse can now determine:

`Who is making the request?`

through JWT authentication,

and:

`What is this user allowed to access?`

through RBAC.

The next milestone is:

**Apply RBAC policies to the real FactoryPulse API endpoints and define the initial permission matrix for Admin, Manager, Technician, and Operator roles.**


---

## 62. RBAC Permission Policy

The first FactoryPulse Role-Based Access Control policy has been applied to the operational API.

The standard roles are:

- `admin`
- `manager`
- `technician`
- `operator`

Reusable role groups are defined in:

`backend/app/core/rbac.py`

Current groups include:

`ALL_ROLES`

- admin
- manager
- technician
- operator

`MANAGEMENT_ROLES`

- admin
- manager

`ASSET_WRITE_ROLES`

- admin
- manager
- technician

`TECHNICAL_WRITE_ROLES`

- admin
- technician

`READING_WRITE_ROLES`

- admin
- technician
- operator

These groups allow authorization policies to remain centralized rather than repeating individual role names throughout the API.

---

## 63. Machine and Sensor RBAC

RBAC has been applied to:

`backend/app/api/machines.py`

and:

`backend/app/api/sensors.py`

Current Machine permissions:

`GET /machines`

All authenticated roles.

`GET /machines/{machine_id}`

All authenticated roles.

`POST /machines`

Admin, Manager, Technician.

`PATCH /machines/{machine_id}`

Admin, Manager, Technician.

`DELETE /machines/{machine_id}`

Admin and Manager.

Current Sensor permissions follow the same asset-management policy.

Operators can therefore monitor machines and sensors but cannot modify industrial asset configuration.

This behavior was verified using the development Operator account.

Tests:

`GET /machines → 200 OK`

`GET /sensors → 200 OK`

`POST /machines → 403 Forbidden`

`DELETE /sensors/{sensor_id} → 403 Forbidden`

---

## 64. SensorReading RBAC

RBAC has been applied to:

`backend/app/api/sensor_readings.py`

Sensor readings can be viewed by all authenticated FactoryPulse roles.

Reading creation is allowed for:

- admin
- technician
- operator

Managers currently have read-only access to sensor measurements.

Current behavior:

`GET /sensor-readings`

All authenticated roles.

`GET /sensor-readings/{reading_id}`

All authenticated roles.

`GET /sensors/{sensor_id}/readings`

All authenticated roles.

`POST /sensor-readings`

Admin, Technician, Operator.

This reflects the current design where Operators and technical systems may submit industrial measurements.

---

## 65. Prediction RBAC

RBAC has been applied to:

`backend/app/api/predictions.py`

Prediction data can be viewed by all authenticated roles.

Manual creation of Prediction records is currently restricted to:

- admin
- technician

Current behavior:

`GET /predictions`

All authenticated roles.

`GET /predictions/{prediction_id}`

All authenticated roles.

`GET /sensors/{sensor_id}/predictions`

All authenticated roles.

`POST /predictions`

Admin and Technician.

Manual prediction creation is temporary.

Once the automated AI inference engine is implemented, prediction records will primarily be generated internally by FactoryPulse rather than manually by users.

Operator testing confirmed:

`GET prediction data → allowed`

`POST /predictions → 403 Forbidden`

---

## 66. Alert RBAC

RBAC has been applied to:

`backend/app/api/alerts.py`

Alert data can be viewed by all authenticated roles.

Manual alert creation is restricted to:

- admin
- technician

Alert updates are currently available to all authenticated roles.

This allows operational users to perform actions such as:

`open → acknowledged`

Current behavior:

`GET /alerts`

All authenticated roles.

`GET /alerts/{alert_id}`

All authenticated roles.

`GET /sensors/{sensor_id}/alerts`

All authenticated roles.

`POST /alerts`

Admin and Technician.

`PATCH /alerts/{alert_id}`

All authenticated roles.

Operator testing confirmed:

`GET /alerts → 200 OK`

`POST /alerts → 403 Forbidden`

---

## 67. MaintenanceRecord RBAC

RBAC has been applied to:

`backend/app/api/maintenance_records.py`

Maintenance history can be viewed by all authenticated roles.

Maintenance creation and modification are restricted to:

- admin
- technician

Current behavior:

`GET /maintenance-records`

All authenticated roles.

`GET /maintenance-records/{record_id}`

All authenticated roles.

`GET /machines/{machine_id}/maintenance-records`

All authenticated roles.

`POST /maintenance-records`

Admin and Technician.

`PATCH /maintenance-records/{record_id}`

Admin and Technician.

Operator testing confirmed:

`POST /maintenance-records → 403 Forbidden`

This prevents Operators and Managers from directly recording technical maintenance interventions under the current policy.

---

## 68. Notification Ownership Authorization

Notifications use both:

- Role-Based Access Control
- Resource ownership authorization

The Notification API is implemented in:

`backend/app/api/notifications.py`

Global notification administration is restricted to:

- admin
- manager

Current global operations:

`GET /notifications`

Admin and Manager.

`POST /notifications`

Admin and Manager.

Individual notification access is more flexible.

All authenticated users may access a notification only when:

`notification.user_id == current_user.id`

unless the current user is Admin or Manager.

Similarly:

`GET /users/{user_id}/notifications`

allows a normal user to retrieve only their own notification collection.

Admin and Manager may access another user's notifications.

Notification updates follow the same ownership rule.

A helper function was added to:

`backend/app/api/dependencies.py`

called:

`user_has_any_role()`

Unlike `require_roles()`, this helper does not automatically reject the request.

Instead, it returns a Boolean value so endpoint logic can combine role checks with ownership rules.

The authorization logic can therefore express:

`Resource belongs to current user`

OR

`Current user has privileged management role`

This prevents users from accessing or modifying another user's private notification records.

Operator integration tests confirmed:

`GET /users/1/notifications → 200 OK`

when User #1 accessed their own notifications.

The same Operator received:

`GET /notifications → 403 Forbidden`

because global notification access requires Admin or Manager permissions.

---

## 69. First Operational RBAC Pass Complete

The first RBAC pass now protects the existing FactoryPulse operational APIs.

FactoryPulse currently enforces authorization across:

- Machines
- Sensors
- SensorReadings
- Predictions
- Alerts
- MaintenanceRecords
- Notifications

The security flow is now:

`Client Request`

`↓`

`Bearer JWT`

`↓`

`get_current_user()`

`↓`

`Authenticated User`

`↓`

`Role loaded from PostgreSQL`

`↓`

`require_roles()`

`↓`

`Optional ownership validation`

`↓`

`Authorized API operation`

The platform can now answer three separate security questions:

`Who are you?`

JWT authentication.

`What are you allowed to do?`

Role-Based Access Control.

`Are you allowed to access this specific user's resource?`

Ownership authorization.

The next major milestone is:

**Implement real User and Role administration APIs so authorized administrators can create users, assign roles, activate/deactivate accounts, and manage FactoryPulse access without directly editing PostgreSQL.**


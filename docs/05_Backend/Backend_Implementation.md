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
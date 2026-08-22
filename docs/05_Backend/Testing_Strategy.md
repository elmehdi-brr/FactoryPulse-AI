# FactoryPulse AI — Backend Testing Strategy

## Overview

FactoryPulse AI uses automated backend testing to verify API behavior, authentication, authorization, business rules, and industrial hierarchy integrity.

The backend test suite is implemented with:

- `pytest`
- `pytest-asyncio`
- `httpx`
- FastAPI ASGI testing
- PostgreSQL

Automated tests run against a dedicated PostgreSQL database and never intentionally use the normal development database.

---

## Test Dependencies

Development and testing dependencies are defined in:

`backend/requirements-dev.txt`

Current testing packages:

- `pytest==9.1.1`
- `pytest-asyncio==1.4.0`
- `httpx==0.28.1`

The development dependency file also includes the normal application requirements through:

`-r requirements.txt`

A development environment can therefore install all backend and test dependencies using:

`python -m pip install -r requirements-dev.txt`

---

## Test Directory Structure

The current testing structure is:

backend/

├── pytest.ini

├── requirements-dev.txt

└── tests/

    ├── conftest.py

    ├── test_health.py

    └── test_industrial_hierarchy.py

`pytest.ini` restricts test discovery to the FactoryPulse `tests` directory and enables asynchronous pytest support.

---

## Isolated PostgreSQL Test Database

FactoryPulse uses a dedicated PostgreSQL database:

`factorypulse_test`

The normal development database remains:

`factorypulse`

The separation is:

Development:

`factorypulse`

Automated tests:

`factorypulse_test`

This prevents automated tests from creating, modifying, or deleting normal development records.

---

## Test Environment Configuration

A dedicated private environment file is used:

`backend/.env.test`

The file is excluded from Git.

A safe committed template is provided:

`backend/.env.test.example`

The test configuration uses:

`ENVIRONMENT=test`

and points the application to:

`factorypulse_test`

The application configuration supports the environment variable:

`FACTORYPULSE_ENV_FILE`

Normal application execution loads:

`backend/.env`

Automated tests configure:

`FACTORYPULSE_ENV_FILE=backend/.env.test`

before FactoryPulse modules are imported.

This allows development and testing configuration to remain completely separate.

---

## Database Safety Test

The automated suite contains an explicit safety test verifying that:

`settings.environment == "test"`

and that the configured database URL ends with:

`/factorypulse_test`

If pytest accidentally loads the development environment, this test fails.

This provides an additional safeguard against accidentally running destructive tests against the normal FactoryPulse development database.

---

## Test Database Lifecycle

The pytest configuration automatically resets the test schema.

For each test:

1. Existing test tables are dropped.
2. The complete SQLAlchemy schema is recreated.
3. The test executes against an empty database.
4. Test tables are removed after execution.

This provides test isolation and prevents records created by one test from influencing another test.

The schema is generated from the registered SQLAlchemy ORM metadata.

Alembic migration testing remains a separate database-development concern.

---

## Async API Testing

FactoryPulse API tests use:

`httpx.AsyncClient`

with:

`ASGITransport`

This allows tests to communicate directly with the FastAPI ASGI application without starting a separate HTTP development server.

Tests are executed asynchronously through:

`pytest-asyncio`

and:

`asyncio_mode = auto`

---

## Authentication Test Fixtures

Reusable test authentication fixtures create isolated:

- Admin user
- Operator user

Test JWT tokens are generated for both identities.

The resulting authorization headers are available to test cases as:

`auth_headers["admin"]`

and:

`auth_headers["operator"]`

These are test-only users and credentials.

They are recreated inside the isolated test database.

---

## Health and Environment Tests

Implemented in:

`tests/test_health.py`

The tests verify:

- The test environment is active.
- The database configuration targets `factorypulse_test`.
- The FastAPI health endpoint responds successfully.

---

## Industrial Hierarchy Automated Tests

Implemented in:

`tests/test_industrial_hierarchy.py`

The suite automatically creates and tests the hierarchy:

Organization

↓

Site

↓

Area

↓

ProductionLine

↓

Machine

It also tests standalone assets:

Area

↓

Machine

---

## Hierarchy Navigation Tests

Automated tests verify:

`Organization → Sites`

`Site → Areas`

`Area → Production Lines`

`Area → Machines`

`Production Line → Machines`

The navigation tests are executed using an Operator identity to verify that normal authenticated roles can read the industrial hierarchy.

---

## Hierarchy RBAC Tests

Automated tests confirm that an Operator cannot perform structural hierarchy writes.

For example:

`POST /organizations`

using an Operator token must return:

`403 Forbidden`

This verifies the hierarchy RBAC policy:

Reads:

- Admin
- Manager
- Technician
- Operator

Structural hierarchy writes:

- Admin
- Manager

---

## Duplicate Code Validation Tests

The hierarchy suite verifies that duplicate Organization codes are rejected.

Attempting to create another Organization using an existing code returns:

`409 Conflict`

This confirms that duplicate validation is handled cleanly by the API rather than exposing a raw database integrity error.

---

## Invalid Parent Validation Tests

Automated tests verify invalid hierarchy relationships.

The suite confirms:

Invalid Organization for Site:

`404 Organization not found`

Invalid Site for Area:

`404 Site not found`

Invalid Area for Production Line:

`404 Area not found`

This ensures hierarchy parents are validated before database writes occur.

---

## Machine Hierarchy Consistency Tests

Machine hierarchy validation is automatically tested.

The suite verifies that a Machine cannot reference:

- an invalid Area
- an invalid Production Line
- a Production Line belonging to a different Area

A cross-Area Production Line relationship returns:

`400 Bad Request`

with:

`Production line does not belong to the selected area`

---

## Standalone Machine Test

The suite verifies that a Machine may belong directly to an Area without belonging to a Production Line.

Example:

Utilities Area

↓

Air Compressor

with:

`production_line_id = null`

This confirms that FactoryPulse supports utility and infrastructure assets without requiring artificial Production Lines.

---

## Partial PATCH Integrity Test

The automated hierarchy suite verifies partial Machine updates.

If a Machine currently belongs to:

Production Area

↓

Production Line 1

and a PATCH attempts to change only the Area to Utilities Area, the existing Production Line is also considered when validating the final state.

The inconsistent update is rejected.

The test then retrieves the Machine again and verifies that its original hierarchy relationship remains unchanged.

This ensures failed partial updates cannot silently corrupt hierarchy integrity.

---

## Current Automated Test Status

Current suite:

- 2 environment/health tests
- 6 industrial hierarchy tests

Total:

`8 tests`

Current result:

`8 passed`

The automated test suite now protects the first FactoryPulse industrial hierarchy implementation from regressions.

---

## Future Testing Expansion

Future test coverage will include:

- Authentication and login flows
- User administration
- Full RBAC matrix
- Sensors and SensorReadings
- Predictions
- Alerts
- Notifications
- Maintenance Records
- AI inference pipelines
- Production modules
- Energy management
- OEE/KPI calculations
- Integration testing
- Migration testing
- Performance testing
- CI/CD automated test execution

The testing suite will evolve alongside FactoryPulse as additional industrial modules are implemented.
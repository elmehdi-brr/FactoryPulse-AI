# FactoryPulse AI — API Overview

## 1. Purpose

This document provides a high-level overview of the FactoryPulse AI API architecture.

It defines:

- The purpose and boundaries of the API
- The clients that communicate with it
- The main API domains
- Communication protocols
- Authentication and authorization principles
- Request and response conventions
- Error-handling principles
- Pagination, filtering and sorting conventions
- Real-time communication principles
- Internal communication with the ML Service
- API documentation and versioning strategy

Detailed endpoints, request bodies, response structures and WebSocket events will be defined in later API documents.

---

## 2. API Role in FactoryPulse AI

The Backend API is the central communication layer of FactoryPulse AI.

It connects:

```text
Web Application
Sensor Simulator
PostgreSQL Database
ML Service
Email Notification Service
```

The Backend API is responsible for:

- Receiving requests from authorized clients
- Validating request data
- Authenticating users and service clients
- Enforcing role-based authorization
- Executing business rules
- Reading and writing application data
- Coordinating ML predictions
- Creating alerts and maintenance tasks
- Sending real-time updates
- Returning standardized responses
- Recording important actions in audit logs

The Backend API is the only application component allowed to access the main PostgreSQL database directly.

---

## 3. API Clients

FactoryPulse AI initially has three API communication categories.

### 3.1 Web Application

The React Web Application communicates with the Backend API.

It uses the API to:

- Authenticate users
- Retrieve profile and role information
- Manage users where authorized
- Retrieve machines and sensors
- Display sensor measurements
- Retrieve predictions
- Manage alerts
- Manage maintenance tasks
- Retrieve notifications
- Display reports
- Receive real-time updates

The Web Application must not communicate directly with PostgreSQL or the ML Service.

---

### 3.2 Sensor Simulator

The Sensor Simulator communicates with the Backend ingestion interface.

It uses the API to:

- Identify simulated machines and sensors
- Submit sensor measurements
- Report the measurement timestamp
- Submit measurement-quality information
- Receive validation results

The Sensor Simulator does not access PostgreSQL directly.

Its requests use service-level authentication rather than normal user authentication.

---

### 3.3 Internal Backend-to-ML Communication

The Backend API communicates with the ML Service through an internal HTTP API.

The Backend sends:

- Machine information required for inference
- Recent sensor measurements
- Prepared feature values
- Prediction type
- Model-selection information when necessary

The ML Service returns:

- Anomaly classification
- Anomaly score
- Failure probability
- Risk level
- Prediction explanation
- Model version information
- Validation or model errors

The ML Service does not directly modify FactoryPulse AI application data.

The Backend API is responsible for storing prediction results.

---

## 4. Communication Protocols

FactoryPulse AI uses the following communication methods:

| Communication | Protocol |
|---|---|
| Web Application → Backend API | REST over HTTP |
| Backend API → Web Application | WebSockets for real-time events |
| Sensor Simulator → Backend API | REST over HTTP |
| Backend API → ML Service | Internal REST over HTTP |
| Backend API → PostgreSQL | SQL through SQLAlchemy |
| Backend API → Email Service | SMTP or service-specific interface |

For local development, HTTP is acceptable because the services run on the developer’s computer.

A future public deployment must use HTTPS.

---

## 5. REST API Style

The main FactoryPulse AI API follows REST-oriented principles.

Resources are represented through nouns.

Preferred examples:

```text
/users
/machines
/sensors
/measurements
/predictions
/alerts
/maintenance-tasks
/notifications
```

Avoid action-oriented paths such as:

```text
/getMachines
/createAlert
/updateUser
```

HTTP methods represent the intended operation.

| Method | Typical Purpose |
|---|---|
| `GET` | Retrieve one or more resources |
| `POST` | Create a resource or trigger an operation |
| `PATCH` | Partially update an existing resource |
| `PUT` | Completely replace a resource when appropriate |
| `DELETE` | Remove a relationship or deletable resource |

Because important operational records should normally be preserved, many resources will use status changes or deactivation instead of permanent deletion.

---

## 6. Base URL and Versioning

The initial API version will use:

```text
/api/v1
```

Examples:

```text
/api/v1/auth/login
/api/v1/users
/api/v1/machines
/api/v1/alerts
/api/v1/maintenance-tasks
```

Health endpoints may remain outside the normal business version path:

```text
/health
```

Versioning allows the API to evolve without unexpectedly breaking existing clients.

A future incompatible version may use:

```text
/api/v2
```

Minor compatible additions do not require a new API version.

---

## 7. Main API Domains

## 7.1 Authentication

Responsibilities:

- User login
- Access-token issuance
- Current-user retrieval
- Logout behaviour where applicable
- Authentication failure handling

Conceptual path:

```text
/api/v1/auth
```

Detailed token handling will be defined in the authentication API design.

---

## 7.2 Users and Roles

Responsibilities:

- Retrieve users
- Create user accounts
- Update user information
- Activate or deactivate users
- Assign user roles
- Retrieve supported roles
- Retrieve the current user profile

Conceptual paths:

```text
/api/v1/users
/api/v1/roles
```

These endpoints are primarily administrative.

---

## 7.3 Machines

Responsibilities:

- Register machines
- Retrieve machine information
- Update machine details
- Change machine operational status
- Decommission machines
- Retrieve machine summaries
- Retrieve users assigned to machines

Conceptual path:

```text
/api/v1/machines
```

---

## 7.4 Machine Assignments

Responsibilities:

- Assign users to machines
- Retrieve machine assignments
- Remove assignments
- Enforce assignment compatibility with user roles
- Control machine-level access

Possible conceptual paths:

```text
/api/v1/machines/{machine_id}/assignments
/api/v1/users/{user_id}/machine-assignments
```

---

## 7.5 Sensors

Responsibilities:

- Register sensors
- Retrieve sensors attached to a machine
- Update sensor configuration
- Configure thresholds
- Change sensor status
- Retire sensors

Possible conceptual path:

```text
/api/v1/machines/{machine_id}/sensors
```

A sensor is always associated with a machine.

---

## 7.6 Sensor Ingestion

Responsibilities:

- Receive measurements from the Sensor Simulator
- Validate service credentials
- Validate sensor identity
- Validate timestamps and values
- Store accepted measurements
- Reject invalid requests
- Trigger monitoring and prediction workflows
- Publish real-time updates

Conceptual path:

```text
/api/v1/ingestion/measurements
```

The ingestion API is separate from normal user-facing measurement retrieval.

---

## 7.7 Measurements

Responsibilities:

- Retrieve recent measurements
- Retrieve measurement history
- Filter by sensor and time range
- Support dashboard charts
- Support monitoring and reporting views

Possible conceptual paths:

```text
/api/v1/sensors/{sensor_id}/measurements
/api/v1/machines/{machine_id}/measurements
```

Measurement history endpoints must use pagination and time-range filters.

---

## 7.8 Predictions

Responsibilities:

- Retrieve recent machine predictions
- Retrieve prediction history
- Retrieve prediction explanations
- Retrieve the model version used
- Trigger authorized prediction operations when required

Possible conceptual paths:

```text
/api/v1/machines/{machine_id}/predictions
/api/v1/predictions/{prediction_id}
```

The Web Application does not call the ML Service directly.

---

## 7.9 Alerts

Responsibilities:

- Retrieve alerts
- Filter alerts by machine, severity and status
- Retrieve alert details
- Create manual alerts
- Acknowledge alerts
- Move alerts into investigation
- Resolve or close alerts

Conceptual path:

```text
/api/v1/alerts
```

Alert workflow transitions must be validated by the Backend API.

---

## 7.10 Maintenance

Responsibilities:

- Create maintenance tasks
- Retrieve tasks
- Assign tasks
- Update task status
- Add intervention events or notes
- Complete or cancel tasks
- Retrieve machine-maintenance history

Possible conceptual paths:

```text
/api/v1/maintenance-tasks
/api/v1/maintenance-tasks/{task_id}/events
```

Maintenance history must remain traceable.

---

## 7.11 Notifications

Responsibilities:

- Retrieve notifications for the current user
- Retrieve unread-notification count
- Mark notifications as read
- Track delivery status
- Link notifications to alerts or maintenance tasks

Conceptual path:

```text
/api/v1/notifications
```

Users normally access only their own notifications.

---

## 7.12 Reports and Dashboard Data

Responsibilities:

- Return dashboard summary metrics
- Return machine-health summaries
- Return alert statistics
- Return maintenance statistics
- Return prediction-risk summaries
- Return measurement trends

Possible conceptual paths:

```text
/api/v1/dashboard
/api/v1/reports
```

Reports should return aggregated data rather than exposing unrestricted database queries.

---

## 7.13 Audit Records

Responsibilities:

- Retrieve audit history
- Filter by actor, action or resource
- Support authorized administrative investigation

Conceptual path:

```text
/api/v1/audit-logs
```

Audit records are read-only through normal API operations.

Access should normally be limited to Administrators.

---

## 8. Authentication Principles

Protected user endpoints require authentication.

The initial API will use token-based authentication.

Conceptual request header:

```http
Authorization: Bearer <access_token>
```

The token identifies:

- The authenticated user
- The user’s role
- Token validity information

The Backend API must validate the token before allowing access to protected functionality.

Detailed decisions about:

- Token lifetime
- Token renewal
- Logout behaviour
- Secure frontend storage
- Refresh-token support

will be documented separately before authentication is implemented.

Passwords are submitted only to the authentication endpoint and are never returned in API responses.

---

## 9. Sensor Simulator Authentication

The Sensor Simulator does not authenticate as a normal platform user.

It should use a dedicated service credential.

A possible request header is:

```http
X-Sensor-API-Key: <sensor_service_key>
```

The actual key must be stored in environment variables.

It must not be:

- Hard-coded in source code
- Committed to GitHub
- Printed in application logs
- Returned through API responses

A future production system may use stronger device or service authentication.

---

## 10. Authorization Principles

Authentication identifies who is making the request.

Authorization determines whether that identity is allowed to perform the requested operation.

The Backend API enforces role-based access control.

Initial roles:

```text
administrator
plant_manager
maintenance_engineer
machine_operator
```

Examples:

### Administrator

May:

- Manage users
- Assign roles
- Register machines and sensors
- Review audit logs
- Access all operational information

### Plant Manager

May:

- View operational dashboards
- Review machines, alerts and predictions
- Review maintenance performance
- Access reports

### Maintenance Engineer

May:

- Review relevant alerts
- Access assigned machines
- Manage assigned maintenance tasks
- Add intervention events
- View prediction explanations

### Machine Operator

May:

- View assigned machines
- View relevant measurements
- Review relevant warnings
- Create manual reports
- Acknowledge permitted alerts

Authorization must be enforced by the Backend API, not only hidden in the frontend interface.

---

## 11. Resource-Level Authorization

Role permission alone may not be sufficient.

Machine-level assignments must also be considered.

Example:

```text
Machine Operator A
  → assigned to PUMP-001

Machine Operator A
  → may access PUMP-001
  → may not automatically access COMPRESSOR-004
```

The Backend API must check:

- The user’s role
- The requested operation
- The machine or resource involved
- The user’s assignment when required

Administrators and Plant Managers may have broader access according to the final authorization rules.

---

## 12. Request Format

Most REST requests and responses use JSON.

Request header:

```http
Content-Type: application/json
```

Example request:

```json
{
  "email": "engineer@example.com",
  "password": "user-supplied-password"
}
```

Field names use:

```text
snake_case
```

Examples:

```text
machine_id
recorded_at
failure_probability
assigned_user_id
```

UUID identifiers are represented as strings in JSON.

Timestamps use ISO 8601 format with timezone information.

Example:

```text
2026-08-01T15:30:00Z
```

---

## 13. Successful Response Format

A consistent response envelope may be used.

Example single-resource response:

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "PUMP-001",
    "name": "Main Cooling Pump",
    "status": "operational"
  }
}
```

Example collection response:

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "code": "PUMP-001",
      "status": "operational"
    }
  ],
  "meta": {
    "limit": 20,
    "has_more": false
  }
}
```

The final API conventions document will decide where response envelopes are required and how metadata is represented.

---

## 14. Error Response Format

API errors must use a predictable structure.

Conceptual format:

```json
{
  "error": {
    "code": "machine_not_found",
    "message": "The requested machine does not exist.",
    "details": [],
    "request_id": "req_123456"
  }
}
```

Fields:

| Field | Meaning |
|---|---|
| `code` | Stable machine-readable error identifier |
| `message` | Human-readable explanation |
| `details` | Additional validation or field information |
| `request_id` | Identifier used to trace the request in logs |

Validation-error example:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid values.",
    "details": [
      {
        "field": "failure_probability",
        "message": "Value must be between 0 and 1."
      }
    ],
    "request_id": "req_123457"
  }
}
```

Error responses must not expose:

- Stack traces
- Database credentials
- SQL statements containing sensitive values
- Authentication tokens
- Password hashes
- Internal file paths unnecessarily

---

## 15. HTTP Status Codes

The API will use standard HTTP status codes.

| Status | Usage |
|---:|---|
| `200 OK` | Request completed successfully |
| `201 Created` | Resource created successfully |
| `202 Accepted` | Long-running or asynchronous operation accepted |
| `204 No Content` | Operation succeeded without response content |
| `400 Bad Request` | Invalid request or business rule violation |
| `401 Unauthorized` | Authentication is missing or invalid |
| `403 Forbidden` | Authenticated user lacks permission |
| `404 Not Found` | Requested resource does not exist or is inaccessible |
| `409 Conflict` | Duplicate or conflicting resource state |
| `422 Unprocessable Entity` | Request validation failed |
| `429 Too Many Requests` | Rate limit exceeded where enabled |
| `500 Internal Server Error` | Unexpected server failure |
| `503 Service Unavailable` | Required dependency is temporarily unavailable |

The API must not return `200 OK` for failed operations.

---

## 16. Filtering

Collection endpoints may support filters through query parameters.

Examples:

```text
GET /api/v1/alerts?status=open
GET /api/v1/alerts?severity=critical
GET /api/v1/machines?status=operational
GET /api/v1/maintenance-tasks?assigned_user_id=<uuid>
GET /api/v1/predictions?risk_level=high
```

Filters must be explicitly supported and validated.

Clients must not be allowed to construct arbitrary database queries.

---

## 17. Sorting

Collection endpoints may support controlled sorting.

Example:

```text
GET /api/v1/alerts?sort=-created_at
```

Possible convention:

```text
created_at
```

means ascending order.

```text
-created_at
```

means descending order.

Only approved fields should be sortable.

Default sorting should be appropriate for the resource.

Examples:

- Measurements: newest first
- Alerts: newest first
- Notifications: newest first
- Maintenance events: oldest first for chronological history

---

## 18. Pagination

Large collections must use pagination.

Resources requiring pagination include:

- Sensor measurements
- Predictions
- Alerts
- Maintenance tasks
- Maintenance events
- Notifications
- Audit logs

Normal administrative collections may use page- or limit-based pagination.

High-volume time-ordered resources should use cursor-based pagination.

Conceptual cursor request:

```text
GET /api/v1/sensors/{sensor_id}/measurements?limit=100&cursor=<cursor>
```

Conceptual response:

```json
{
  "data": [],
  "meta": {
    "limit": 100,
    "next_cursor": null,
    "has_more": false
  }
}
```

The exact cursor format must remain opaque to API clients.

---

## 19. Time-Range Queries

Measurement, prediction, alert and audit endpoints may support time-range filters.

Example:

```text
GET /api/v1/sensors/{sensor_id}/measurements
    ?start_time=2026-08-01T00:00:00Z
    &end_time=2026-08-01T23:59:59Z
```

The API must validate:

- Timestamp format
- Start time before end time
- Maximum permitted range where necessary
- User authorization for the requested resource

Time-range limits may protect the API from extremely expensive queries.

---

## 20. Real-Time Communication

FactoryPulse AI uses WebSockets for near-real-time updates.

Potential events include:

```text
measurement.received
machine.status_changed
prediction.created
alert.created
alert.updated
maintenance_task.created
maintenance_task.updated
notification.created
```

Conceptual WebSocket endpoint:

```text
/api/v1/ws
```

A WebSocket message may use a structure such as:

```json
{
  "event": "alert.created",
  "timestamp": "2026-08-01T15:30:00Z",
  "data": {
    "alert_id": "550e8400-e29b-41d4-a716-446655440000",
    "machine_id": "2c1f7f02-3b4f-4e75-b517-9636f06c43c0",
    "severity": "critical"
  }
}
```

The Backend API must ensure that connected users receive only events they are authorized to view.

Detailed connection, authentication, event and reconnection behaviour will be defined in a dedicated WebSocket document.

---

## 21. Backend-to-ML API Boundary

The ML Service exposes an internal API.

Possible conceptual endpoints include:

```text
POST /predict/anomaly
POST /predict/failure-risk
POST /predict/combined
GET /health
GET /models
```

These endpoints are not part of the public frontend API.

The Backend Prediction Orchestrator is responsible for:

- Preparing ML requests
- Applying timeouts
- Handling unavailable ML responses
- Validating ML results
- Saving predictions
- Triggering alert logic

The ML Service must not receive normal user passwords or unnecessary personal information.

---

## 22. Health Checks

The Backend API exposes a health endpoint.

Conceptual endpoint:

```text
GET /health
```

A basic response may contain:

```json
{
  "status": "healthy"
}
```

A more detailed internal health response may include:

```json
{
  "status": "healthy",
  "database": "available",
  "ml_service": "available"
}
```

Public health responses should not expose sensitive infrastructure information.

The ML Service will expose its own health endpoint.

---

## 23. API Documentation

FastAPI will generate OpenAPI documentation automatically.

Development documentation interfaces may include:

```text
/docs
/redoc
/openapi.json
```

These interfaces help developers:

- Review endpoints
- Inspect request and response schemas
- Test local API requests
- Understand authentication requirements
- Review generated models

In a public production deployment, documentation access may be restricted or configured differently.

The written API documents in `docs/09_API` remain important because they explain business meaning, decisions and workflows beyond generated endpoint schemas.

---

## 24. Logging and Request Traceability

API requests should receive a request identifier.

Example:

```text
X-Request-ID
```

The request identifier may be:

- Supplied by a trusted client
- Generated by the Backend API
- Included in logs
- Returned in error responses

Logs may contain:

- Request identifier
- HTTP method
- Endpoint path
- Response status
- Execution duration
- Authenticated user identifier where appropriate

Logs must not contain:

- Plain-text passwords
- Complete access tokens
- API keys
- Database passwords
- Secret environment variables

---

## 25. Idempotency and Duplicate Protection

Some operations may be retried because of network problems.

Examples:

- Sensor measurement submission
- Alert-generated maintenance-task creation
- Notification generation

The detailed API design must define how duplicate processing is prevented.

Possible mechanisms include:

- Stable client-generated identifiers
- Idempotency keys
- Unique database constraints
- Duplicate-detection windows
- Transactional workflow rules

The exact mechanism will be selected per operation rather than applied unnecessarily to every endpoint.

---

## 26. Rate Limiting

Rate limiting is not required for the first isolated local implementation.

A future public deployment should consider rate limits for:

- Login attempts
- Sensor ingestion
- Expensive report endpoints
- Prediction-triggering operations
- Administrative endpoints

Rate-limit responses should use:

```text
429 Too Many Requests
```

Authentication failure protection should also include login-attempt controls.

---

## 27. API Security Principles

The API must follow these security rules:

- Validate every request
- Authenticate protected operations
- Authorize every protected resource
- Never trust frontend permission checks alone
- Hash passwords securely
- Keep secrets in environment variables
- Protect service API keys
- Prevent direct database access
- Prevent direct frontend-to-ML access
- Avoid exposing internal exception details
- Apply reasonable request-size limits
- Use parameterized database operations through SQLAlchemy
- Record sensitive administrative actions in audit logs
- Use HTTPS for public deployment
- Restrict CORS to approved frontend origins

---

## 28. API Compatibility Principles

Compatible changes may include:

- Adding optional response fields
- Adding new endpoints
- Adding optional query parameters
- Adding new event types
- Adding new error codes

Potentially breaking changes include:

- Renaming existing fields
- Removing fields
- Changing field meaning
- Changing required request values
- Changing response structure
- Changing URL paths
- Changing authentication behaviour

Breaking changes require careful migration and may require a new API version.

---

## 29. Planned API Documentation

The `09_API` folder may contain:

```text
09_API/
├── API_Overview.md
├── API_Conventions.md
├── Authentication_API.md
├── User_and_Access_API.md
├── Machine_and_Sensor_API.md
├── Monitoring_and_Prediction_API.md
├── Alert_and_Maintenance_API.md
├── Notification_and_Reporting_API.md
└── WebSocket_Events.md
```

The final file structure may be adjusted if combining related endpoints makes the documentation clearer.

---

## 30. Related Documents

- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[04_Database/Database_Schema|Database Schema]]
- [[02_Requirements/Functional_Requirements|Functional Requirements]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
- [[02_Requirements/Use_Cases|Use Cases]]
- [[API_Conventions]]
- [[Authentication_API]]
- [[User_and_Access_API]]
- [[Machine_and_Sensor_API]]
- [[Alert_and_Maintenance_API]]
- [[Notification_and_Reporting_API]]
- [[WebSocket_Events]]
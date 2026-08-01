# FactoryPulse AI — API Conventions

## 1. Purpose

This document defines the shared conventions used by the FactoryPulse AI REST API.

Its purpose is to ensure that all endpoints use consistent rules for:

- URLs and resource naming
- HTTP methods
- JSON field names
- Request bodies
- Successful responses
- Error responses
- HTTP status codes
- Resource identifiers
- Date and time values
- Pagination
- Filtering
- Sorting
- Validation
- Partial updates
- Idempotency
- Request traceability
- API compatibility and deprecation

These conventions apply to the public Backend API used by the Web Application and Sensor Simulator.

Internal ML Service endpoints may follow the same principles but will be documented separately where their behaviour differs.

---

## 2. Base API Path

All versioned business endpoints use:

```text
/api/v1
```

Examples:

```text
/api/v1/users
/api/v1/machines
/api/v1/alerts
/api/v1/maintenance-tasks
```

Infrastructure endpoints may remain outside the versioned business path.

Examples:

```text
/health
/docs
/redoc
/openapi.json
```

---

## 3. URL Naming

URLs use:

```text
lowercase-kebab-case
```

Examples:

```text
/maintenance-tasks
/machine-assignments
/failure-risk
```

Resource paths should use nouns rather than action verbs.

Preferred:

```text
POST /api/v1/machines
GET /api/v1/alerts
PATCH /api/v1/maintenance-tasks/{task_id}
```

Avoid:

```text
POST /api/v1/createMachine
GET /api/v1/getAlerts
POST /api/v1/updateTask
```

---

## 4. Resource Hierarchy

Nested paths may be used when a child resource belongs clearly to a parent.

Examples:

```text
GET /api/v1/machines/{machine_id}/sensors
GET /api/v1/sensors/{sensor_id}/measurements
GET /api/v1/maintenance-tasks/{task_id}/events
```

Top-level endpoints should still be available where cross-parent filtering is required.

Example:

```text
GET /api/v1/alerts?machine_id={machine_id}
```

Nesting should normally remain limited to one parent level.

Avoid excessively deep paths such as:

```text
/api/v1/machines/{machine_id}/sensors/{sensor_id}/measurements/{measurement_id}/details
```

---

## 5. Resource Identifiers

Main application resources use UUID identifiers.

Example:

```text
550e8400-e29b-41d4-a716-446655440000
```

UUIDs are represented as strings in JSON.

Example:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Invalid UUID syntax should return a validation error.

Clients must treat identifiers as opaque values and must not infer meaning from them.

---

## 6. HTTP Methods

The API uses HTTP methods according to their standard meaning.

| Method | Purpose |
|---|---|
| `GET` | Retrieve resources |
| `POST` | Create a resource or trigger a defined operation |
| `PATCH` | Partially update a resource |
| `PUT` | Fully replace a resource when explicitly supported |
| `DELETE` | Delete a removable resource or relationship |

### GET

`GET` requests must not change application state.

Examples:

```text
GET /api/v1/machines
GET /api/v1/alerts/{alert_id}
```

### POST

`POST` normally creates a resource.

Example:

```text
POST /api/v1/machines
```

It may also represent a business action when that action cannot be expressed clearly as a normal resource update.

Example:

```text
POST /api/v1/alerts/{alert_id}/acknowledgements
```

### PATCH

`PATCH` modifies only the fields included in the request.

Example:

```text
PATCH /api/v1/machines/{machine_id}
```

### PUT

`PUT` is not used by default.

It should only be introduced where complete replacement of a resource is meaningful.

### DELETE

`DELETE` may be used for removable relationships.

Example:

```text
DELETE /api/v1/machines/{machine_id}/assignments/{assignment_id}
```

Historical operational resources such as measurements, predictions, alerts, maintenance events and audit logs should not normally be deleted through the public API.

---

## 7. Request Content Type

JSON requests use:

```http
Content-Type: application/json
```

The API may reject unsupported content types using:

```text
415 Unsupported Media Type
```

File uploads are outside the initial MVP unless a confirmed requirement introduces them.

---

## 8. JSON Naming Convention

JSON field names use:

```text
snake_case
```

Examples:

```text
first_name
machine_id
recorded_at
failure_probability
assigned_user_id
```

Avoid mixing naming styles such as:

```text
firstName
machineID
RecordedAt
```

API field names should normally match their corresponding domain and database terminology unless exposing the database name would be misleading or insecure.

---

## 9. Date and Time Format

All API date-time values use ISO 8601 with timezone information.

Preferred UTC format:

```text
2026-08-01T15:30:00Z
```

Example:

```json
{
  "created_at": "2026-08-01T15:30:00Z"
}
```

The API stores and returns timestamps in UTC.

The frontend is responsible for converting UTC values into the user’s local timezone for display.

Date-only values use:

```text
YYYY-MM-DD
```

Example:

```json
{
  "installation_date": "2026-07-15"
}
```

Requests without required timezone information should be rejected where time interpretation would be ambiguous.

---

## 10. Boolean and Null Values

Boolean fields use JSON boolean values:

```json
{
  "is_active": true,
  "is_read": false
}
```

Do not represent booleans using:

```text
"true"
"false"
1
0
yes
no
```

Nullable values use JSON `null`.

Example:

```json
{
  "resolved_at": null
}
```

A missing field and a field explicitly set to `null` may have different meanings in a `PATCH` request.

---

## 11. Numeric Values

Probabilities are represented as decimal values between `0` and `1`.

Example:

```json
{
  "failure_probability": 0.8742
}
```

Measurement values are returned as JSON numbers.

Example:

```json
{
  "value": 78.4,
  "measurement_unit": "°C"
}
```

The API must not return numeric values as formatted strings unless the field is intentionally textual.

Avoid:

```json
{
  "failure_probability": "87.42%"
}
```

The frontend may format numeric values for display.

---

## 12. Successful Single-Resource Response

A successful response containing one resource uses a `data` envelope.

Example:

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "PUMP-001",
    "name": "Main Cooling Pump",
    "status": "operational",
    "created_at": "2026-08-01T15:30:00Z"
  }
}
```

The `data` field contains the requested resource.

---

## 13. Successful Collection Response

A collection response uses:

```json
{
  "data": [],
  "meta": {}
}
```

Example:

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "code": "PUMP-001",
      "status": "operational"
    },
    {
      "id": "8b57c604-319d-4f18-b655-872b37b173a2",
      "code": "PUMP-002",
      "status": "warning"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 2,
    "total_pages": 1
  }
}
```

High-volume cursor-based endpoints use different pagination metadata, as defined later in this document.

---

## 14. Resource-Creation Response

Successful resource creation returns:

```text
201 Created
```

The response should contain the created resource.

Example:

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

The response may also include a `Location` header.

Example:

```http
Location: /api/v1/machines/550e8400-e29b-41d4-a716-446655440000
```

---

## 15. No-Content Response

When an operation succeeds and no response body is needed, the API returns:

```text
204 No Content
```

A `204` response must not contain a JSON body.

Possible use:

```text
DELETE /api/v1/machines/{machine_id}/assignments/{assignment_id}
```

---

## 16. Error Response Format

All handled API errors use the following structure:

```json
{
  "error": {
    "code": "machine_not_found",
    "message": "The requested machine does not exist.",
    "details": [],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

### Fields

| Field | Purpose |
|---|---|
| `code` | Stable machine-readable error identifier |
| `message` | Human-readable summary |
| `details` | Additional structured error information |
| `request_id` | Identifier used to trace the request in logs |

The frontend should use `code` for application logic and `message` for user-facing feedback.

---

## 17. Error-Code Naming

Error codes use lowercase `snake_case`.

Examples:

```text
validation_error
authentication_required
invalid_credentials
permission_denied
machine_not_found
duplicate_machine_code
invalid_alert_transition
ml_service_unavailable
```

Error codes should remain stable even when the human-readable message changes.

Avoid using database exception names or Python exception names as public error codes.

---

## 18. Validation Error Format

Validation errors use:

```text
422 Unprocessable Entity
```

Example:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid values.",
    "details": [
      {
        "field": "email",
        "message": "A valid email address is required.",
        "type": "value_error"
      },
      {
        "field": "first_name",
        "message": "This field is required.",
        "type": "missing"
      }
    ],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

Nested field paths may use dot notation.

Example:

```text
sensors.0.measurement_unit
```

Validation messages must not expose internal code or stack traces.

---

## 19. Business-Rule Error Format

Requests that are structurally valid but violate business rules normally return:

```text
400 Bad Request
```

or:

```text
409 Conflict
```

Example invalid workflow transition:

```json
{
  "error": {
    "code": "invalid_alert_transition",
    "message": "A closed alert cannot return directly to the open state.",
    "details": [
      {
        "current_status": "closed",
        "requested_status": "open"
      }
    ],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

Use `409 Conflict` when the request conflicts with the current resource state or uniqueness rules.

Example:

```text
duplicate_machine_code
```

---

## 20. Standard HTTP Status Codes

| Status | Meaning in FactoryPulse AI |
|---:|---|
| `200 OK` | Successful retrieval or update |
| `201 Created` | Resource created |
| `202 Accepted` | Processing accepted but not completed |
| `204 No Content` | Successful operation without response body |
| `400 Bad Request` | Invalid business request |
| `401 Unauthorized` | Authentication missing or invalid |
| `403 Forbidden` | Authenticated identity lacks permission |
| `404 Not Found` | Resource does not exist or is inaccessible |
| `409 Conflict` | Duplicate data or resource-state conflict |
| `415 Unsupported Media Type` | Unsupported request content type |
| `422 Unprocessable Entity` | Request-field validation failed |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server failure |
| `503 Service Unavailable` | Required dependency is unavailable |

The API must not use `200 OK` to represent failed operations.

---

## 21. Authentication Errors

Missing or invalid authentication returns:

```text
401 Unauthorized
```

Example:

```json
{
  "error": {
    "code": "authentication_required",
    "message": "A valid access token is required.",
    "details": [],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

The response should include an appropriate authentication header where applicable.

Example:

```http
WWW-Authenticate: Bearer
```

Invalid login credentials should not reveal whether the email address exists.

Preferred message:

```text
The email address or password is incorrect.
```

---

## 22. Authorization Errors

An authenticated user without permission receives:

```text
403 Forbidden
```

Example:

```json
{
  "error": {
    "code": "permission_denied",
    "message": "You are not authorized to perform this operation.",
    "details": [],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

For sensitive resources, the API may return `404 Not Found` instead of revealing that an inaccessible resource exists.

---

## 23. Not-Found Responses

Missing resources return:

```text
404 Not Found
```

Example:

```json
{
  "error": {
    "code": "machine_not_found",
    "message": "The requested machine does not exist.",
    "details": [],
    "request_id": "req_01J4A7QAX4N12Q3X5F20R8T9MN"
  }
}
```

Resource-specific error codes are preferred over a generic `not_found` code.

---

## 24. PATCH Request Semantics

`PATCH` updates only fields included in the request.

Example:

```http
PATCH /api/v1/machines/{machine_id}
```

Request:

```json
{
  "name": "Updated Cooling Pump",
  "location": "Production Area B"
}
```

Fields not included remain unchanged.

An explicitly provided `null` means the client is requesting that the field be cleared, but only when the field is nullable.

Example:

```json
{
  "description": null
}
```

Read-only fields must not be accepted in update requests.

Examples of read-only fields:

```text
id
created_at
updated_at
password_hash
predicted_at
```

---

## 25. Field Selection and Response Safety

API response models must explicitly define which fields are exposed.

Database models must not be returned directly without response validation.

Fields that must never appear in normal responses include:

```text
password_hash
database credentials
secret keys
access tokens
sensor service API keys
internal exception details
```

Administrative endpoints may expose additional operational fields, but only where authorized.

---

## 26. Page-Based Pagination

Page-based pagination is used for relatively stable administrative collections.

Examples:

```text
users
machines
sensors
machine assignments
maintenance tasks
```

Request parameters:

```text
page
page_size
```

Example:

```text
GET /api/v1/machines?page=1&page_size=20
```

Default values:

```text
page = 1
page_size = 20
```

Maximum page size:

```text
100
```

Example response:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 86,
    "total_pages": 5
  }
}
```

Invalid page values return a validation error.

---

## 27. Cursor-Based Pagination

Cursor pagination is used for high-volume or continuously changing chronological data.

Resources include:

```text
sensor measurements
predictions
alerts
notifications
maintenance events
audit logs
```

Request parameters:

```text
limit
cursor
```

Example:

```text
GET /api/v1/sensors/{sensor_id}/measurements?limit=100&cursor=<opaque_cursor>
```

Default limit:

```text
50
```

Maximum limit:

```text
200
```

Example response:

```json
{
  "data": [],
  "meta": {
    "limit": 100,
    "next_cursor": "eyJyZWNvcmRlZF9hdCI6IjIwMjYtMDgtMDFUMTU6MzA6MDBaIn0",
    "has_more": true
  }
}
```

The cursor must remain opaque to clients.

Clients must not construct or modify cursor values manually.

---

## 28. Filtering Convention

Filters use query parameters.

Examples:

```text
GET /api/v1/machines?status=operational
GET /api/v1/alerts?severity=critical&status=open
GET /api/v1/maintenance-tasks?assigned_user_id={user_id}
```

Filter names use the same `snake_case` names as the resource fields.

Multiple filters are combined using logical `AND` unless an endpoint documents otherwise.

Unsupported filters should return a validation error rather than being silently ignored.

---

## 29. Multiple-Value Filters

When an endpoint supports several accepted values for one field, comma-separated values may be used.

Example:

```text
GET /api/v1/alerts?status=open,acknowledged,in_progress
```

This means:

```text
status IN ('open', 'acknowledged', 'in_progress')
```

The endpoint documentation must explicitly state which filters support multiple values.

---

## 30. Sorting Convention

Sorting uses the query parameter:

```text
sort
```

Ascending order:

```text
sort=created_at
```

Descending order:

```text
sort=-created_at
```

Multiple fields may be supported using commas where justified.

Example:

```text
sort=-severity,-created_at
```

Only approved fields may be used for sorting.

Unsupported sort fields return a validation error.

Default sorting examples:

| Resource | Default Sort |
|---|---|
| Machines | `code` ascending |
| Measurements | `recorded_at` descending |
| Predictions | `predicted_at` descending |
| Alerts | `created_at` descending |
| Maintenance events | `created_at` ascending |
| Notifications | `created_at` descending |
| Audit logs | `created_at` descending |

---

## 31. Time-Range Filtering

Chronological endpoints may support:

```text
start_time
end_time
```

Example:

```text
GET /api/v1/sensors/{sensor_id}/measurements
    ?start_time=2026-08-01T00:00:00Z
    &end_time=2026-08-01T23:59:59Z
```

Rules:

- Both values must be valid ISO 8601 timestamps.
- `start_time` must not be later than `end_time`.
- The endpoint may enforce a maximum time range.
- The requester must be authorized to access the related resource.

When no range is supplied, the endpoint should use a documented default rather than returning unlimited history.

---

## 32. Search Convention

Simple text search may use:

```text
search
```

Example:

```text
GET /api/v1/machines?search=pump
```

Searchable fields must be documented per endpoint.

For machines, this may search:

```text
code
name
location
manufacturer
model
```

Search must not be interpreted as arbitrary SQL.

The MVP does not initially provide full-text search syntax.

---

## 33. Idempotency

Operations likely to be retried may support an idempotency identifier.

Possible header:

```http
Idempotency-Key: <client-generated-value>
```

Sensor ingestion should use a stable measurement identifier or batch identifier when duplicate submission is possible.

The API should return the original successful result when an identical idempotent request is repeated within the supported retention period.

Idempotency should be added only to operations that need it.

Likely candidates:

- Sensor measurement ingestion
- Batch measurement ingestion
- Alert-generated maintenance creation
- External notification requests

Normal `GET`, `PUT` and `DELETE` operations are expected to follow their usual idempotent behaviour.

---

## 34. Request Identification

Every API request should have a request identifier.

Preferred header:

```http
X-Request-ID
```

The Backend API should:

1. Accept a valid request ID from trusted clients where appropriate.
2. Generate one when none is supplied.
3. Include it in logs.
4. Return it in the response header.
5. Include it in error responses.

Example response header:

```http
X-Request-ID: req_01J4A7QAX4N12Q3X5F20R8T9MN
```

This helps trace failures across the frontend, backend and internal services.

---

## 35. Correlation with the ML Service

When the Backend API calls the ML Service, it should forward or create a correlation identifier.

Possible header:

```http
X-Correlation-ID
```

This allows one prediction workflow to be traced across:

```text
Frontend or Simulator
    → Backend API
    → ML Service
    → Backend API
    → Database and alert workflow
```

Sensitive authentication credentials must not be forwarded unnecessarily.

---

## 36. Language and Human-Readable Messages

Stable error codes remain in English technical form.

Example:

```text
machine_not_found
```

Human-readable API messages will initially be written in English.

The frontend may later translate user-facing messages using error codes.

Database or backend exception messages must not be shown directly to users.

---

## 37. Empty Collections

A successful collection request with no matching records returns:

```text
200 OK
```

with an empty array.

Example:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0
  }
}
```

It should not return `404 Not Found`.

---

## 38. API Version Compatibility

The initial public API version is:

```text
v1
```

Compatible changes include:

- Adding optional response fields
- Adding new endpoints
- Adding optional filters
- Adding new error codes
- Adding new WebSocket event types

Breaking changes include:

- Removing a field
- Renaming a field
- Changing field meaning
- Changing a required request field
- Changing response-envelope structure
- Changing authentication behaviour
- Replacing an endpoint path

Breaking changes require a migration strategy and may require:

```text
/api/v2
```

---

## 39. Deprecation Convention

Deprecated endpoints should remain available for a defined transition period where practical.

A deprecated response may include headers such as:

```http
Deprecation: true
Sunset: Sat, 01 Aug 2027 00:00:00 GMT
```

Documentation must identify:

- The deprecated endpoint or field
- The recommended replacement
- The planned removal date
- Any migration instructions

The MVP is not expected to contain deprecated endpoints initially, but the convention is defined for future evolution.

---

## 40. CORS Convention

The Backend API should allow requests only from approved frontend origins.

Development example:

```text
http://localhost:5173
```

CORS must not use unrestricted origins together with credentials in a public deployment.

Allowed methods, headers and origins should be configured using environment variables where appropriate.

---

## 41. Request-Size Limits

The API should apply reasonable request-size limits.

This is especially relevant for:

- Sensor measurement batches
- Long maintenance notes
- JSON explanation data
- Report filters

The API should reject excessively large requests instead of allowing uncontrolled memory usage.

The exact limits will be chosen during implementation and documented for affected endpoints.

---

## 42. Batch Operations

Batch endpoints may be introduced where they provide a clear performance benefit.

Primary MVP candidate:

```text
POST /api/v1/ingestion/measurements/batch
```

A batch response should distinguish accepted and rejected items.

Conceptual example:

```json
{
  "data": {
    "accepted_count": 98,
    "rejected_count": 2,
    "rejected_items": [
      {
        "index": 15,
        "code": "unknown_sensor",
        "message": "The sensor identifier does not exist."
      }
    ]
  }
}
```

Batch operations must define whether processing is:

- Fully transactional
- Partially accepted
- All-or-nothing

This decision must be explicit for each batch endpoint.

---

## 43. OpenAPI Documentation

FastAPI generates the OpenAPI specification from:

- Endpoint definitions
- Request models
- Response models
- Authentication requirements
- Validation rules
- Status codes

Development interfaces include:

```text
/docs
/redoc
/openapi.json
```

Endpoint implementation must document:

- Summary
- Description
- Required permissions
- Request schema
- Successful responses
- Error responses
- Example values

Generated OpenAPI documentation complements but does not replace written API design documents.

---

## 44. Convention Enforcement

These conventions should be enforced through:

- Shared Pydantic response models
- Shared error handlers
- Shared pagination utilities
- Authentication dependencies
- Authorization dependencies
- Consistent router structure
- Automated API tests
- OpenAPI review
- Code-review checklists

Individual endpoint modules should not invent incompatible response or error formats.

---

## 45. Related Documents

- [[09_API/API_Overview|API Overview]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[04_Database/Database_Schema|Database Schema]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
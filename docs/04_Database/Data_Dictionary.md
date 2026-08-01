# FactoryPulse AI — Data Dictionary

## 1. Purpose

This document explains the business meaning and expected usage of the data stored in the FactoryPulse AI database.

While the Database Schema defines technical details such as PostgreSQL data types, keys and constraints, this Data Dictionary explains:

- What each important field represents
- Where the value originates
- How the value is used
- Which component may update it
- Whether the field contains sensitive information
- Which controlled values are allowed
- Whether the value is expected to remain immutable

This document covers the thirteen database tables included in the MVP.

---

## 2. Data Classification

FactoryPulse AI data is classified into the following categories.

### 2.1 Public or General Data

Information that does not normally require special protection.

Examples:

- Machine names
- Sensor types
- Measurement units
- Model version names

---

### 2.2 Internal Operational Data

Information used internally to operate and monitor the platform.

Examples:

- Sensor measurements
- Machine status
- Alerts
- Predictions
- Maintenance tasks
- Model metrics

This information should only be accessible to authorized users.

---

### 2.3 Personal Data

Information that identifies or relates to a platform user.

Examples:

- First name
- Last name
- Email address
- User assignments
- IP address

Access to this information should be restricted according to user roles.

---

### 2.4 Security-Sensitive Data

Information that requires strong protection and must never be publicly exposed.

Examples:

- Password hashes
- Authentication-related audit information
- Database credentials
- Tokens and secret keys

Secrets and authentication tokens are not stored in the application database unless a future requirement explicitly introduces secure session storage.

---

## 3. General Field Conventions

### 3.1 Identifier Fields

Fields named `id` contain the UUID primary key of a record.

Fields ending in `_id` contain references to other entities.

Examples:

```text
machine_id
sensor_id
user_id
model_version_id
```

---

### 3.2 Timestamp Fields

Timestamp fields are stored in UTC.

Common meanings include:

| Field | Meaning |
|---|---|
| `created_at` | Time the record was created |
| `updated_at` | Time the record was last modified |
| `recorded_at` | Time a sensor produced a measurement |
| `received_at` | Time the Backend API received a measurement |
| `predicted_at` | Time an AI prediction was generated |
| `acknowledged_at` | Time an alert was acknowledged |
| `resolved_at` | Time an alert was resolved |
| `completed_at` | Time a maintenance task was completed |

The frontend may convert UTC timestamps to the user's local timezone for display.

---

### 3.3 Status Fields

Status fields use controlled values.

The Backend API must validate workflow transitions before changing a status.

For example, a maintenance task should not move directly from `open` to `completed` without satisfying the required business rules.

---

## 4. Identity and Access Domain

## 4.1 `roles`

Stores the roles supported by FactoryPulse AI.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the role | Database | Used by users through `role_id` |
| `name` | Technical role identifier | Initial seed data | Used by authorization rules |
| `description` | Human-readable explanation of the role | Administrator or seed process | Displayed in administrative interfaces |
| `created_at` | Time the role was created | Database | Used for traceability |

### Controlled Role Values

#### `administrator`

Has full administrative access.

Typical responsibilities:

- Manage users and roles
- Register machines and sensors
- Review audit information
- Access all platform functions

#### `plant_manager`

Monitors operations and performance.

Typical responsibilities:

- View dashboards
- Review alerts and predictions
- View reports
- Monitor maintenance performance

#### `maintenance_engineer`

Handles maintenance interventions.

Typical responsibilities:

- Review alerts
- Receive maintenance assignments
- Update maintenance tasks
- Record intervention events

#### `machine_operator`

Monitors assigned machines.

Typical responsibilities:

- View assigned equipment
- Monitor measurements
- Review relevant warnings
- Report visible problems

### Sensitivity

Role data is internal but not highly sensitive.

---

## 4.2 `users`

Stores user accounts and profile information.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the user | Database | Used throughout assignments, alerts, maintenance and auditing |
| `role_id` | Role assigned to the user | Administrator | Determines authorization level |
| `first_name` | User's given name | Administrator or user-management process | Displayed in the interface |
| `last_name` | User's family name | Administrator or user-management process | Displayed in the interface |
| `email` | User's normalized login address | Administrator or user-management process | Used for login and email notifications |
| `password_hash` | Secure hash of the user's password | Authentication component | Must never contain or expose the original password |
| `is_active` | Whether the account may authenticate | Administrator | Inactive users cannot log in |
| `last_login_at` | Most recent successful authentication time | Authentication component | Used for security monitoring |
| `created_at` | Account creation time | Database | Used for traceability |
| `updated_at` | Most recent account modification time | Backend API | Updated when account details change |

### Important Rules

- `email` must be lowercase and unique.
- `password_hash` must never be returned by the API.
- Password changes should replace the previous hash securely.
- Users should normally be deactivated using `is_active = false` rather than deleted.
- Role changes and account-status changes should create audit records.

### Sensitivity

| Field | Classification |
|---|---|
| `first_name` | Personal data |
| `last_name` | Personal data |
| `email` | Personal data |
| `password_hash` | Security-sensitive |
| `last_login_at` | Security-sensitive operational data |

---

## 5. Industrial Asset Domain

## 5.1 `machines`

Stores industrial equipment monitored by FactoryPulse AI.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the machine | Database | Referenced by sensors, predictions, alerts and maintenance |
| `code` | Stable business identifier of the machine | Administrator | Used for search, display and integration |
| `name` | Human-readable machine name | Administrator | Displayed in dashboards |
| `description` | Additional machine information | Administrator | Optional explanatory text |
| `location` | Physical area where the machine operates | Administrator | Used for filtering and operational context |
| `manufacturer` | Company that produced the machine | Administrator | Used for technical reference |
| `model` | Manufacturer model designation | Administrator | Used for technical reference |
| `installation_date` | Date the machine was installed | Administrator | Used for asset history |
| `status` | Current operational condition | Monitoring component, maintenance workflow or authorized user | Displayed in dashboards and used for filtering |
| `created_at` | Machine registration time | Database | Used for traceability |
| `updated_at` | Last machine-record update | Backend API | Updated when machine details or status change |

### Machine Status Values

| Value | Meaning |
|---|---|
| `operational` | Machine is functioning normally |
| `warning` | Machine requires attention but remains operational |
| `critical` | Machine condition presents serious risk |
| `maintenance` | Machine is undergoing maintenance |
| `offline` | Machine is not currently communicating or operating |
| `decommissioned` | Machine is permanently retired from active operation |

### Important Rules

- `code` should remain stable after registration.
- A machine with historical records should be decommissioned rather than deleted.
- Automated status changes should preserve the reason through alerts or audit records.

### Sensitivity

Machine information is internal operational data.

---

## 5.2 `machine_assignments`

Associates users with machines they may operate, maintain or supervise.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the assignment | Database | Internal relationship identifier |
| `user_id` | User assigned to the machine | Administrator or authorized manager | Controls machine-level access |
| `machine_id` | Machine assigned to the user | Administrator or authorized manager | Connects the user to an asset |
| `assignment_type` | Reason or responsibility for the assignment | Administrator or authorized manager | Supports role-specific access |
| `assigned_by` | User who created the assignment | Backend API | Used for accountability |
| `assigned_at` | Time the assignment was created | Database | Used for traceability |

### Assignment Types

| Value | Meaning |
|---|---|
| `operation` | User operates or monitors the machine |
| `maintenance` | User is responsible for maintaining the machine |
| `supervision` | User supervises the machine or its performance |

### Important Rules

- One user should not have duplicate assignments to the same machine.
- Assignment type should be compatible with the user's role.
- Assignment creation and removal should create audit records.

### Sensitivity

Assignments are internal personal and operational data.

---

## 5.3 `sensors`

Stores sensors attached to machines.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the sensor | Database | Referenced by measurements and alerts |
| `machine_id` | Machine containing the sensor | Administrator | Defines asset ownership |
| `code` | Sensor identifier within its machine | Administrator | Used by ingestion and display |
| `name` | Human-readable sensor name | Administrator | Displayed in dashboards |
| `sensor_type` | Category of quantity measured | Administrator | Determines processing and visualization |
| `measurement_unit` | Unit associated with sensor values | Administrator | Displayed with measurements |
| `warning_min` | Lower warning boundary | Administrator or configuration process | Used by monitoring logic |
| `warning_max` | Upper warning boundary | Administrator or configuration process | Used by monitoring logic |
| `critical_min` | Lower critical boundary | Administrator or configuration process | Used for critical alerts |
| `critical_max` | Upper critical boundary | Administrator or configuration process | Used for critical alerts |
| `status` | Current sensor state | Administrator, monitoring or maintenance process | Determines whether data should be accepted |
| `created_at` | Sensor registration time | Database | Used for traceability |
| `updated_at` | Last sensor configuration update | Backend API | Updated after changes |

### Initial Sensor Types

| Value | Meaning | Example Unit |
|---|---|---|
| `temperature` | Measures temperature | `°C` |
| `pressure` | Measures pressure | `bar` |
| `vibration` | Measures equipment vibration | `mm/s` |
| `rotational_speed` | Measures rotating speed | `RPM` |
| `voltage` | Measures electrical voltage | `V` |
| `current` | Measures electrical current | `A` |
| `flow_rate` | Measures liquid or gas flow | `L/min` |

### Sensor Status Values

| Value | Meaning |
|---|---|
| `active` | Sensor is operating normally |
| `inactive` | Sensor is temporarily disabled |
| `faulty` | Sensor may be producing unreliable data |
| `maintenance` | Sensor is being serviced |
| `retired` | Sensor is permanently removed from active use |

### Important Rules

- Thresholds must use the same unit as the sensor.
- Critical thresholds represent more severe conditions than warning thresholds.
- Threshold changes should be audited.
- Historical sensors should be retired rather than deleted.

---

## 6. Sensor Data Domain

## 6.1 `sensor_measurements`

Stores individual values produced by sensors.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the measurement | Database | Internal traceability |
| `sensor_id` | Sensor that produced the value | Sensor Simulator or ingestion request | Links the value to its configuration |
| `value` | Numeric measurement received from the sensor | Sensor Simulator or future IoT device | Used for monitoring, charts and ML |
| `quality_status` | Reliability classification of the measurement | Sensor Ingestion component | Determines whether data may be trusted |
| `recorded_at` | Time the sensor generated the value | Sensor Simulator or IoT device | Used for time-series analysis |
| `received_at` | Time FactoryPulse AI received the value | Backend API or database | Used to measure ingestion delay |

### Quality Status Values

| Value | Meaning |
|---|---|
| `valid` | Value passed all validation rules |
| `suspect` | Value may be usable but requires caution |
| `invalid` | Value failed validation and should not be used normally |
| `missing` | Expected measurement was not available |
| `simulated` | Value was produced by the Sensor Simulator |

### Important Rules

- Measurements are normally immutable.
- `recorded_at` and `received_at` are different events.
- The value must be interpreted using the linked sensor's unit.
- Invalid measurements may be stored for traceability but should not normally influence predictions.
- This table will receive frequent inserts and requires efficient indexing.

### Sensitivity

Measurements are internal operational data.

---

## 7. Artificial Intelligence Domain

## 7.1 `model_versions`

Stores metadata about trained ML models.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the model version | Database | Referenced by predictions |
| `name` | Logical model name | ML development or registration process | Groups versions of the same model |
| `version` | Version identifier | ML development process | Distinguishes model releases |
| `model_type` | Purpose of the model | ML development process | Determines supported prediction type |
| `file_path` | Location of the model artifact | ML deployment configuration | Used by the ML Service to load the model |
| `metrics` | Evaluation results from training or validation | ML training process | Used to evaluate model quality |
| `model_metadata` | Additional structured model information | ML training or registration process | May include features, algorithm and training details |
| `is_active` | Whether the model version is currently available for inference | Administrator or model-management process | Selects the active model |
| `created_at` | Time the version was registered | Database | Used for traceability |

### Model Type Values

| Value | Meaning |
|---|---|
| `anomaly_detection` | Detects unusual machine behaviour |
| `failure_prediction` | Estimates equipment-failure risk |
| `combined` | Supports both anomaly and failure-risk outputs |

### Example `metrics`

```json
{
  "precision": 0.91,
  "recall": 0.87,
  "f1_score": 0.89
}
```

### Example `model_metadata`

```json
{
  "algorithm": "RandomForestClassifier",
  "feature_names": [
    "temperature",
    "pressure",
    "vibration"
  ],
  "training_dataset_version": "1.0"
}
```

### Important Rules

- The database stores model metadata, not the model file itself.
- Activating or deactivating models should be audited.
- Predictions must preserve the model version used.
- Model paths should not expose credentials or secret values.

---

## 7.2 `predictions`

Stores outputs produced by the ML Service.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the prediction | Database | Referenced by alerts |
| `machine_id` | Machine evaluated by the model | Prediction Orchestrator | Used for machine history |
| `model_version_id` | Model version used for inference | ML Service or Prediction Orchestrator | Provides traceability |
| `prediction_type` | Category of prediction produced | ML Service | Determines required output fields |
| `is_anomaly` | Whether the evaluated behaviour is abnormal | Anomaly-detection model | Used by alert logic |
| `anomaly_score` | Numeric measure of abnormality | Anomaly-detection model | Model-specific interpretation |
| `failure_probability` | Estimated probability of failure | Failure-prediction model | Must remain between 0 and 1 |
| `risk_level` | Human-readable risk classification | ML Service or Backend risk logic | Displayed in dashboards |
| `explanation_data` | Structured explanation of the result | Explainability component | Used to explain influential features |
| `input_window_start` | Beginning of evaluated measurement period | Prediction Orchestrator | Defines model-input scope |
| `input_window_end` | End of evaluated measurement period | Prediction Orchestrator | Defines model-input scope |
| `predicted_at` | Time the prediction was generated | ML Service or Backend API | Used for history and ordering |

### Prediction Type Values

| Value | Meaning |
|---|---|
| `anomaly` | Anomaly-detection result |
| `failure_risk` | Failure-probability result |
| `combined` | Contains both anomaly and failure-risk information |

### Risk Level Values

| Value | Meaning |
|---|---|
| `low` | No immediate concern |
| `medium` | Condition should be observed |
| `high` | Maintenance attention is recommended |
| `critical` | Immediate action may be required |

### Example `explanation_data`

```json
{
  "top_features": [
    {
      "feature": "vibration",
      "contribution": 0.48
    },
    {
      "feature": "temperature",
      "contribution": 0.31
    }
  ],
  "summary": "High vibration and temperature increased the predicted risk."
}
```

### Important Rules

- Predictions should normally remain immutable.
- The meaning of `anomaly_score` depends on the model and must be documented in model metadata.
- Risk thresholds must remain consistent between the ML Service and Backend API.
- Predictions with high or critical risk may generate alerts.

---

## 8. Alert Domain

## 8.1 `alerts`

Stores operational warnings and critical events.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the alert | Database | Referenced by maintenance tasks and notifications |
| `machine_id` | Machine affected by the alert | Monitoring, prediction or manual-report process | Required for all alerts |
| `sensor_id` | Sensor associated with the alert | Monitoring component | Optional |
| `prediction_id` | Prediction associated with the alert | Prediction Orchestrator | Optional |
| `alert_type` | Source or category of the alert | Alert Management component | Determines alert context |
| `severity` | Importance of the alert | Alert Management component | Used for prioritization |
| `status` | Current workflow state | Authorized users or workflow logic | Used to track handling progress |
| `title` | Short alert summary | Alert Management component or user | Displayed in lists |
| `message` | Detailed alert information | Alert Management component or user | Provides investigation context |
| `acknowledged_by` | User who confirmed awareness of the alert | Authorized user | Optional until acknowledged |
| `resolved_by` | User who marked the alert as resolved | Authorized user | Optional until resolved |
| `created_at` | Time the alert was created | Database | Used for ordering and response-time metrics |
| `acknowledged_at` | Time the alert was acknowledged | Backend API | Used for response metrics |
| `resolved_at` | Time the alert was resolved | Backend API | Used for resolution metrics |

### Alert Type Values

| Value | Meaning |
|---|---|
| `threshold` | Sensor measurement exceeded a configured threshold |
| `anomaly` | Anomaly-detection model identified abnormal behaviour |
| `failure_risk` | Model identified elevated failure probability |
| `manual` | User manually reported an issue |
| `system` | Platform or integration issue |

### Severity Values

| Value | Meaning |
|---|---|
| `info` | Informational event |
| `warning` | Requires observation |
| `high` | Requires timely attention |
| `critical` | Requires urgent action |

### Alert Status Values

| Value | Meaning |
|---|---|
| `open` | Alert has not yet been handled |
| `acknowledged` | User has confirmed awareness |
| `in_progress` | Investigation or intervention is underway |
| `resolved` | Underlying issue has been addressed |
| `closed` | Alert workflow is complete |

### Important Rules

- Every alert must reference a machine.
- Threshold alerts should normally reference a sensor.
- AI alerts should normally reference a prediction.
- Acknowledgement and resolution actions must be audited.
- Important alerts may generate notifications and maintenance tasks.

---

## 9. Maintenance Domain

## 9.1 `maintenance_tasks`

Stores planned and active maintenance work.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the maintenance task | Database | Referenced by events and notifications |
| `machine_id` | Machine requiring intervention | Task creator or alert workflow | Required |
| `source_alert_id` | Alert that caused the task | Alert workflow | Optional for manually created tasks |
| `assigned_user_id` | User responsible for performing the task | Manager, administrator or assignment process | May be empty initially |
| `created_by` | User who created the task | Backend API | May be empty for automated tasks |
| `title` | Short task description | Task creator or system | Displayed in task lists |
| `description` | Detailed instructions or context | Task creator | Supports maintenance work |
| `priority` | Urgency of the task | Task creator or alert workflow | Used for sorting |
| `status` | Current task state | Assigned engineer or authorized user | Controls maintenance workflow |
| `due_date` | Expected completion deadline | Task creator or manager | Used to identify overdue work |
| `started_at` | Time work began | Maintenance workflow | Required for active work states |
| `completed_at` | Time work was completed | Maintenance workflow | Required when completed |
| `created_at` | Task creation time | Database | Used for traceability |
| `updated_at` | Last task update time | Backend API | Updated after task modifications |

### Priority Values

| Value | Meaning |
|---|---|
| `low` | Can be handled during normal planning |
| `medium` | Requires standard attention |
| `high` | Should be prioritized |
| `critical` | Requires immediate intervention |

### Maintenance Status Values

| Value | Meaning |
|---|---|
| `open` | Task exists but has not been assigned |
| `assigned` | Task has an assigned user |
| `in_progress` | Maintenance work has started |
| `blocked` | Work cannot continue temporarily |
| `completed` | Required work has been completed |
| `cancelled` | Task is no longer required |

### Important Rules

- Every task belongs to one machine.
- Assigned users should normally have the Maintenance Engineer role.
- State changes should create maintenance events.
- Completion should not erase earlier intervention history.

---

## 9.2 `maintenance_events`

Stores chronological history for maintenance tasks.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the event | Database | Internal traceability |
| `maintenance_task_id` | Task associated with the event | Maintenance workflow | Required |
| `performed_by` | User responsible for the action | Backend API | Optional for system-generated events |
| `event_type` | Category of action performed | Maintenance workflow | Used to build task history |
| `notes` | Additional intervention details | Maintenance Engineer or system | Optional |
| `created_at` | Time the event occurred | Database | Used for chronological ordering |

### Initial Event Types

| Value | Meaning |
|---|---|
| `task_created` | Maintenance task was created |
| `assigned` | Task was assigned to a user |
| `started` | Maintenance work began |
| `note_added` | Additional information was recorded |
| `inspection_completed` | Inspection was completed |
| `component_replaced` | A component was replaced |
| `blocked` | Work became blocked |
| `resumed` | Blocked work resumed |
| `completed` | Maintenance was completed |
| `cancelled` | Task was cancelled |

### Important Rules

- Maintenance events are append-only.
- Existing events should not be silently modified.
- Notes must not contain passwords, tokens or unrelated personal information.
- Events should reflect the real order of work performed.

---

## 10. Notification Domain

## 10.1 `notifications`

Stores user-facing notifications and delivery information.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the notification | Database | Internal traceability |
| `user_id` | Recipient of the notification | Notification component | Required |
| `alert_id` | Related alert | Notification component | Optional |
| `maintenance_task_id` | Related maintenance task | Notification component | Optional |
| `notification_type` | Category of notification | Notification component | Determines content and context |
| `delivery_channel` | Method used to notify the user | Notification rules | In-app, email or both |
| `delivery_status` | Current external-delivery state | Notification component | Tracks email success or failure |
| `title` | Short notification summary | Notification component | Displayed to the user |
| `message` | Detailed notification content | Notification component | Displayed or sent by email |
| `is_read` | Whether the user opened the in-app notification | User action | Used for unread counts |
| `created_at` | Notification creation time | Database | Used for ordering |
| `read_at` | Time the notification was opened | Backend API | Optional until read |
| `sent_at` | Time external delivery succeeded | Email-delivery process | Optional |

### Notification Type Values

| Value | Meaning |
|---|---|
| `alert` | Notification about an alert |
| `maintenance` | Notification about maintenance progress |
| `assignment` | Notification about a new assignment |
| `system` | General platform notification |

### Delivery Channel Values

| Value | Meaning |
|---|---|
| `in_app` | Displayed inside FactoryPulse AI |
| `email` | Sent by email |
| `both` | Displayed in-app and sent by email |

### Delivery Status Values

| Value | Meaning |
|---|---|
| `pending` | External delivery has not completed |
| `sent` | External delivery succeeded |
| `failed` | External delivery failed |
| `not_applicable` | No external delivery was required |

### Important Rules

- Every notification must have one recipient.
- Email failure should not remove the in-app notification.
- Notification content should not expose sensitive secrets.
- Duplicate notifications should be prevented by application logic.

---

## 11. Audit Domain

## 11.1 `audit_logs`

Stores important security and business actions.

### Field Dictionary

| Field | Business Meaning | Source or Updated By | Usage and Notes |
|---|---|---|---|
| `id` | Unique identifier of the audit event | Database | Internal traceability |
| `actor_user_id` | User responsible for the action | Backend API | Optional for system actions |
| `action` | Technical identifier describing what occurred | Audit Logging component | Used for filtering and analysis |
| `resource_type` | Type of entity affected | Audit Logging component | Examples: `user`, `machine`, `alert` |
| `resource_id` | Identifier of the affected record | Audit Logging component | Optional for non-resource events |
| `previous_values` | Selected values before a change | Audit Logging component | Stored as JSONB |
| `new_values` | Selected values after a change | Audit Logging component | Stored as JSONB |
| `ip_address` | Client network address associated with the action | Backend API | Security-sensitive personal data |
| `created_at` | Time the action was recorded | Database | Used for chronological investigation |

### Example Action Values

```text
user.created
user.role_changed
user.deactivated
machine.created
machine.status_changed
sensor.threshold_updated
alert.acknowledged
alert.resolved
maintenance_task.assigned
maintenance_task.completed
model_version.activated
authentication.login_failed
```

### Example Resource Types

```text
user
role
machine
sensor
machine_assignment
prediction
alert
maintenance_task
model_version
```

### Important Rules

- Audit records are append-only.
- Normal users must not modify or delete audit records.
- Password hashes, passwords, authentication tokens and secrets must never appear in `previous_values` or `new_values`.
- System-generated events may have no actor.
- Audit access should normally be limited to administrators.

### Sensitivity

Audit data may contain:

- Personal information
- Security events
- IP addresses
- Operational history

It must be protected from unauthorized access.

---

## 12. Data Ownership and Modification Summary

| Data Area | Primary Creator | Primary Modifier |
|---|---|---|
| Roles | Seed process | Administrator |
| Users | Administrator | Administrator or user-management process |
| Machines | Administrator | Administrator, monitoring or maintenance logic |
| Machine assignments | Administrator or manager | Administrator or manager |
| Sensors | Administrator | Administrator or maintenance process |
| Measurements | Sensor Simulator or IoT source | Normally immutable |
| Model versions | ML registration process | Model-management process |
| Predictions | ML Service and Backend API | Normally immutable |
| Alerts | Monitoring, AI or user | Authorized users and workflow logic |
| Maintenance tasks | User or alert workflow | Assigned engineer or authorized manager |
| Maintenance events | Maintenance workflow | Append-only |
| Notifications | Notification component | User read action or delivery process |
| Audit logs | Audit component | Append-only |

---

## 13. Sensitive Field Handling

The following fields require special protection:

| Field | Protection Requirement |
|---|---|
| `users.password_hash` | Never expose through API responses or logs |
| `users.email` | Return only to authorized users |
| `users.last_login_at` | Restrict to account owner or administrator |
| `audit_logs.ip_address` | Restrict to administrators |
| `audit_logs.previous_values` | Remove passwords, tokens and secrets |
| `audit_logs.new_values` | Remove passwords, tokens and secrets |
| Model paths | Must not contain embedded credentials |
| Notification messages | Must not expose secrets |

---

## 14. Null-Value Meaning

A nullable field must have a clear business meaning.

Examples:

| Field | Meaning When `NULL` |
|---|---|
| `machines.installation_date` | Installation date is unknown |
| `sensors.warning_min` | No lower warning threshold is configured |
| `predictions.failure_probability` | Prediction did not include failure probability |
| `alerts.sensor_id` | Alert did not originate from one specific sensor |
| `alerts.prediction_id` | Alert did not originate from an AI prediction |
| `alerts.acknowledged_by` | Alert has not been acknowledged |
| `alerts.resolved_at` | Alert has not been resolved |
| `maintenance_tasks.assigned_user_id` | Task is not yet assigned |
| `maintenance_tasks.source_alert_id` | Task was created manually |
| `maintenance_events.performed_by` | Event was generated automatically |
| `notifications.alert_id` | Notification is not linked to an alert |
| `audit_logs.actor_user_id` | Action was performed by the system |

A null value must not be used when a controlled value such as `unknown` would communicate a different meaning.

---

## 15. Immutable and Historical Data

The following data should normally remain unchanged after creation:

- Sensor measurements
- Predictions
- Maintenance events
- Audit logs

When corrections are necessary, the preferred approach is to:

- Create a replacement record
- Add a correction event
- Add an audit explanation
- Preserve the original historical information

This protects traceability.

---

## 16. Related Documents

- [[04_Database/Database_Overview|Database Overview]]
- [[04_Database/Entity_Relationship_Diagram|Entity Relationship Diagram]]
- [[04_Database/Database_Schema|Database Schema]]
- [[03_Architecture/Architecture_Overview|Architecture Overview]]
- [[03_Architecture/Component_Architecture|Component Architecture]]
- [[02_Requirements/Software_Requirements_Specification|Software Requirements Specification]]
- [[02_Requirements/Functional_Requirements|Functional Requirements]]
- [[02_Requirements/Non_Functional_Requirements|Non-Functional Requirements]]
- [[02_Requirements/Use_Cases|Use Cases]]
- [[Indexing_Strategy]]
- [[Migration_and_Seed_Strategy]]

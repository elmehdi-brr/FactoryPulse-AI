# FactoryPulse AI — AI Integration

## Overview

Phase 4 introduces automated intelligence into FactoryPulse AI.

The long-term automation flow is:

SensorReading

↓

AI Inference / Anomaly Detection

↓

Prediction

↓

Risk Evaluation

↓

Alert

↓

Notification / Maintenance Intelligence

The AI layer is intentionally separated from the existing CRUD services.

The existing services remain responsible for persistence, while dedicated AI orchestration and inference components will decide when Predictions and Alerts should be created.

This keeps the backend modular and allows different models to be integrated later without tightly coupling machine-learning logic to FastAPI routes or database CRUD functions.

---

## AI Automation Architecture

The planned architecture is:

SensorReading ingestion

↓

Persist SensorReading

↓

AI Orchestration Service

↓

Inference Engine

↓

Prediction persistence

↓

Anomaly / Risk Evaluation

↓

Alert generation when required

Future model implementations may include:

- Statistical anomaly detection
- XGBoost
- Forecasting models
- Failure-risk models
- Sensor-specific models
- Multi-sensor models
- Future deep-learning models

The orchestration layer will provide a consistent interface between FactoryPulse operational data and these model implementations.

---

## Prediction Traceability

Before implementing automated inference, Prediction traceability was strengthened.

Previously, a Prediction referenced only:

`sensor_id`

This identified which Sensor the prediction belonged to, but not which SensorReading triggered the inference.

Phase 4 adds:

`source_reading_id`

to the Prediction model.

The traceability chain is now:

SensorReading

↓

Prediction

↓

Alert

This allows FactoryPulse to determine exactly which reading contributed to a Prediction and which Prediction generated an Alert.

---

## Prediction Source Reading Database Relationship

The `predictions` table now includes:

`source_reading_id`

The field is:

- nullable
- indexed
- a foreign key to `sensor_readings.id`

Foreign-key relationship:

`predictions.source_reading_id → sensor_readings.id`

Constraint:

`fk_predictions_source_reading_id`

Index:

`ix_predictions_source_reading_id`

The field remains nullable for two reasons:

1. Existing/manual Predictions remain supported.
2. Future prediction workflows may be generated from windows or aggregated data rather than one individual SensorReading.

Automatically generated single-reading Predictions will use `source_reading_id`.

---

## ORM Relationships

The ORM now supports:

`Prediction.source_reading`

and:

`SensorReading.predictions`

The relationship is:

`SensorReading 1 → many Predictions`

This allows multiple AI models to analyze the same SensorReading in the future.

For example:

SensorReading

├── Statistical anomaly Prediction

├── XGBoost Prediction

└── Failure-risk Prediction

---

## Prediction Schema Integration

The Prediction Pydantic schema now includes:

`source_reading_id: int | None`

Manual Prediction creation remains valid with:

`source_reading_id = null`

Traceable Prediction creation can provide:

`source_reading_id = <reading ID>`

The field is also returned through the Prediction response model.

---

## Prediction Source Validation

API-level validation was added for Prediction creation.

If `source_reading_id` is provided, FactoryPulse verifies:

1. The selected Sensor exists.
2. The source SensorReading exists.
3. The source SensorReading belongs to the same Sensor referenced by the Prediction.

This prevents logically inconsistent relationships such as:

Prediction:

`sensor_id = Sensor A`

Source Reading:

`Sensor B Reading`

Such a request is rejected with:

`400 Bad Request`

and:

`Source reading does not belong to the selected sensor`

A nonexistent source reading is rejected with:

`404 Not Found`

and:

`Source sensor reading not found`

---

## Prediction Traceability Migration

Alembic migration:

`518a97cf035b_link_predictions_to_source_readings.py`

Previous revision:

`0b543b737a18`

The migration adds:

- `predictions.source_reading_id`
- index `ix_predictions_source_reading_id`
- foreign key `fk_predictions_source_reading_id`

The migration was inspected before being applied.

The foreign-key constraint was explicitly named instead of relying on an automatically generated anonymous constraint.

The migration was applied successfully and verified directly in PostgreSQL.

---

## PostgreSQL Verification

The `predictions` table was verified after migration.

Confirmed:

`source_reading_id` exists and is nullable.

Confirmed index:

`ix_predictions_source_reading_id`

Confirmed foreign key:

`fk_predictions_source_reading_id`

Relationship:

`source_reading_id → sensor_readings.id`

Existing relationship:

`Alert.prediction_id → predictions.id`

The resulting persistent traceability chain is:

SensorReading

↓

Prediction

↓

Alert

---

## Automated Traceability Tests

Automated tests were added in:

`tests/test_prediction_traceability.py`

The test suite verifies four scenarios.

### Valid Source Reading

A Prediction can reference a SensorReading belonging to the selected Sensor.

Expected result:

`201 Created`

The returned Prediction contains the correct:

`source_reading_id`

### Missing Source Reading

A Prediction referencing a nonexistent SensorReading is rejected.

Expected:

`404 Not Found`

### Wrong Sensor Relationship

A Prediction cannot use a SensorReading belonging to another Sensor.

Expected:

`400 Bad Request`

### Manual Prediction Compatibility

A Prediction may still be created with:

`source_reading_id = null`

This preserves compatibility with manual and future non-single-reading prediction workflows.

---

## Current Automated Test Status

Previous backend suite:

`8 passed`

New Prediction traceability tests:

`4 passed`

Current total:

`12 passed`

The existing Industrial Hierarchy regression tests continue passing after the Phase 4 persistence changes.

---

## Current Phase 4 Status

Completed:

- Phase 4 feature branch created
- Existing Prediction and Alert persistence architecture reviewed
- SensorReading ingestion flow reviewed
- Prediction source traceability designed
- `source_reading_id` added to Prediction
- SensorReading ↔ Prediction ORM relationships added
- Prediction schema updated
- Prediction source validation added
- Alembic migration created and verified
- PostgreSQL relationship verified
- Prediction traceability tests added
- Full backend regression suite passing

Next milestone:

**Implement the AI inference and orchestration foundation that automatically processes SensorReadings and produces Predictions.**



---

## AI Inference Engine Foundation

FactoryPulse now includes a model-independent AI inference layer.

Implemented package:

`backend/app/ai/`

Current structure:

- `base.py`
- `baseline.py`

The purpose of this layer is to separate machine-learning inference from:

- FastAPI routes
- database persistence
- operational CRUD services

The architecture is:

SensorReading

↓

AI Orchestration

↓

Inference Engine

↓

Inference Result

↓

Prediction

This allows FactoryPulse to replace or extend inference models without rewriting the surrounding backend workflow.

---

## Inference Result

The common inference result is represented by:

`InferenceResult`

It contains:

- `predicted_value`
- `anomaly_score`
- `is_anomaly`
- `model_name`
- `model_version`

All inference engines return this common structure.

This creates a stable contract between AI models and the FactoryPulse backend.

---

## Inference Engine Interface

FactoryPulse defines the:

`InferenceEngine`

protocol.

An inference engine receives:

- the current SensorReading value
- historical values for the same Sensor

and returns an:

`InferenceResult`

Future implementations may include:

- Statistical anomaly detection
- XGBoost
- forecasting models
- failure-risk models
- deep-learning models
- sensor-specific models
- multi-sensor models

The orchestration layer therefore depends on an interface rather than a specific machine-learning implementation.

---

## Statistical Z-Score Baseline

The first inference implementation is:

`StatisticalZScoreEngine`

Model name:

`statistical-zscore`

Model version:

`1.0`

The engine uses recent SensorReading history to calculate:

- historical mean
- population standard deviation
- absolute Z-score of the current reading

Default configuration:

`threshold = 3.0`

`min_history = 10`

A reading is classified as anomalous when:

`anomaly_score >= threshold`

This model is a deterministic baseline used to validate the complete AI automation architecture before integrating more advanced trained models.

It is not intended to be the final FactoryPulse AI model.

---

## Insufficient History Behavior

When no historical values exist, the engine:

- uses the current value as the predicted value
- does not calculate an anomaly score
- does not classify the reading as anomalous

When history exists but is below the configured minimum history requirement:

- the historical mean becomes the predicted value
- anomaly detection remains inactive
- `anomaly_score = null`

This prevents FactoryPulse from producing unreliable anomaly classifications when insufficient historical context exists.

---

## Zero-Variance Handling

Constant sensor history produces a standard deviation of zero.

FactoryPulse handles this explicitly.

If:

`current value == historical mean`

then:

`anomaly_score = 0`

and the reading is normal.

If the current value differs from a completely constant historical baseline, the reading receives an anomaly score above the configured threshold and is classified as anomalous.

This avoids division-by-zero errors while still detecting meaningful departures from a stable sensor baseline.

---

## Historical Reading Query

The SensorReading service now supports:

`get_recent_readings_before()`

The function retrieves historical readings belonging to the same Sensor.

The current reading is never included in its own historical baseline.

The query also supports historical reprocessing by selecting only readings occurring before the target reading.

Ordering uses:

- `recorded_at`
- `id`

This ensures deterministic historical ordering even when multiple readings have identical timestamps.

The current history limit is:

`50 readings`

The value can be changed or made configurable later.

---

## AI Automation Service

Implemented in:

`backend/app/services/ai_automation_service.py`

The main orchestration function is:

`process_sensor_reading()`

Its workflow is:

SensorReading

↓

Load previous readings for the Sensor

↓

Convert historical readings to numerical history

↓

Run the selected InferenceEngine

↓

Receive InferenceResult

↓

Create Prediction

↓

Persist Prediction

The automatically generated Prediction includes:

`source_reading_id = reading.id`

This maintains the Phase 4 traceability chain:

SensorReading

↓

Prediction

↓

Alert

---

## Default Inference Engine

FactoryPulse currently configures:

`StatisticalZScoreEngine`

as the default inference engine.

Default configuration:

`threshold = 3.0`

`min_history = 10`

The orchestration function accepts an `InferenceEngine` parameter, allowing another engine to be injected without rewriting the workflow.

For example, future integrations may use:

`process_sensor_reading(..., engine=XGBoostEngine(...))`

while the surrounding SensorReading and Prediction persistence flow remains unchanged.

---

## AI Baseline Unit Tests

Implemented in:

`tests/test_ai_baseline.py`

The tests verify:

- no-history behavior
- insufficient-history behavior
- normal-reading classification
- anomalous-reading classification
- constant-history normal readings
- constant-history deviations
- invalid engine configuration

Total baseline inference tests:

`7`

---

## AI Automation Tests

Implemented in:

`tests/test_ai_automation.py`

The tests verify that:

1. A persisted SensorReading can be processed by the AI orchestration service.
2. A real Prediction is automatically created.
3. The Prediction references the source SensorReading.
4. The model metadata is persisted.
5. Historical values are used as the inference baseline.
6. The current reading is not included in its own historical baseline.
7. An extreme reading is correctly classified as an anomaly.

One automated scenario creates ten historical readings with:

`value = 50`

followed by:

`value = 80`

The resulting Prediction keeps:

`predicted_value ≈ 50`

and classifies the new reading as anomalous.

This confirms that the current reading does not contaminate its own baseline.

---

## Current Automated Test Status

Previous backend suite:

`12 passed`

AI baseline tests:

`7 passed`

AI orchestration tests:

`2 passed`

Current total:

`21 passed`

All previous Industrial Hierarchy and Prediction traceability tests continue passing.

---

## Current AI Automation Architecture

The implemented architecture is now:

SensorReading

↓

Historical Sensor Data

↓

AI Orchestration Service

↓

InferenceEngine

↓

StatisticalZScoreEngine

↓

InferenceResult

↓

Prediction

The orchestration layer and inference engine currently operate correctly when explicitly invoked.

The SensorReading API has not yet been connected to automatic inference.

---

## Next AI Milestone

The next milestone is automatic ingestion integration.

Target flow:

POST `/sensor-readings`

↓

Validate Sensor

↓

Persist SensorReading

↓

Automatically process the SensorReading

↓

Automatically create Prediction

After this integration, clients will no longer need to manually call:

POST `/predictions`

for the normal automated inference workflow.

Manual Prediction creation may remain available for development, testing, and specialized workflows.



---

## Automatic SensorReading Inference Integration

The SensorReading ingestion API is now connected directly to the FactoryPulse AI automation layer.

Previously, the AI orchestration service could process a SensorReading when explicitly called by backend code.

The normal ingestion workflow is now automatic.

Current flow:

POST `/sensor-readings`

↓

Validate Sensor

↓

Persist SensorReading

↓

Run `process_sensor_reading()`

↓

Load historical readings

↓

Run the configured InferenceEngine

↓

Create Prediction automatically

↓

Return SensorReading response

The API contract for SensorReading creation remains unchanged.

Clients submit sensor data normally and receive the created SensorReading, while AI inference runs automatically as part of the ingestion workflow.

---

## Automatic Prediction Generation

A client no longer needs to manually call:

POST `/predictions`

for the standard AI workflow.

When a SensorReading is created, FactoryPulse automatically generates a Prediction containing:

- `sensor_id`
- `source_reading_id`
- `predicted_value`
- `anomaly_score`
- `is_anomaly`
- `model_name`
- `model_version`

The Prediction is therefore directly traceable to the SensorReading that triggered inference.

The automatic chain is:

SensorReading

↓

Prediction

with:

`Prediction.source_reading_id = SensorReading.id`

---

## API Integration Strategy

Automatic inference is currently synchronous.

This means:

1. The SensorReading is persisted.
2. FactoryPulse immediately performs inference.
3. The resulting Prediction is persisted.
4. The SensorReading API request completes.

This approach is appropriate for the current development phase because the baseline inference engine is lightweight and deterministic.

Future high-volume industrial ingestion may move AI processing to:

- background workers
- task queues
- event-driven processing
- streaming infrastructure

This would allow SensorReading ingestion to remain fast even when advanced models require heavier computation.

The current orchestration architecture is intentionally model-independent so that this evolution can occur without redesigning the complete ingestion API.

---

## Automatic Inference API Test

An end-to-end automated test verifies the new workflow.

The test performs:

POST `/sensor-readings`

↓

receives `201 Created`

↓

GET `/sensors/{sensor_id}/predictions`

↓

verifies that a Prediction was automatically created

The test confirms:

- the Prediction belongs to the correct Sensor
- `source_reading_id` matches the newly created SensorReading
- the baseline model name is persisted
- the model version is persisted
- the inference result is returned correctly
- no manual Prediction creation request is required

---

## Manual Swagger Verification

The automatic workflow was also verified manually through FastAPI Swagger.

A SensorReading was created using:

POST `/sensor-readings`

No manual request was made to:

POST `/predictions`

The Predictions API was then queried using:

GET `/sensors/{sensor_id}/predictions`

The automatically generated Prediction was present and contained:

`source_reading_id = created SensorReading ID`

`model_name = statistical-zscore`

`model_version = 1.0`

This confirms that automatic inference works through the real API workflow in addition to the automated test suite.

---

## Current Automated Test Status

Previous test suite:

`21 passed`

Automatic ingestion integration test:

`1 passed`

Current total:

`22 passed`

All previous Industrial Hierarchy, traceability, inference, and AI orchestration regression tests continue passing.

---

## Current Automated Intelligence Flow

FactoryPulse now supports:

SensorReading

↓

Historical Sensor Data

↓

AI Orchestration Service

↓

StatisticalZScoreEngine

↓

InferenceResult

↓

Prediction automatically persisted

The next AI milestone is:

**Automatically generate an Alert when an automatically generated Prediction is classified as anomalous.**

Target flow:

SensorReading

↓

Prediction

↓

`is_anomaly = true`

↓

Risk evaluation

↓

Alert automatically generated






---

## Automatic AI Alert Generation

FactoryPulse now automatically generates Alerts from anomalous AI Predictions.

The automated intelligence workflow is:

SensorReading

↓

Historical Sensor Data

↓

Inference Engine

↓

Prediction

↓

Risk Evaluation

↓

Alert when required

The inference model remains responsible for determining whether a reading is anomalous.

Alert severity is determined separately by the risk-evaluation layer.

This separation keeps model inference independent from operational alert policy.

---

## Risk Evaluation Layer

Implemented in:

`backend/app/ai/risk.py`

The main components are:

- `RiskAssessment`
- `AnomalyRiskEvaluator`

`RiskAssessment` contains:

- `should_alert`
- `severity`

The risk evaluator receives:

- `is_anomaly`
- `anomaly_score`

and determines whether an Alert should be generated.

Current baseline policy:

`not anomalous → no Alert`

`anomaly score < 5 → medium`

`5 <= anomaly score < 8 → high`

`anomaly score >= 8 → critical`

If a Prediction is anomalous but does not contain an anomaly score, the baseline severity is:

`medium`

The risk thresholds are intentionally separated from the inference model so they can later become:

- configurable
- sensor-specific
- machine-specific
- organization-specific
- model-specific

without modifying the underlying machine-learning implementation.

---

## Automatic Alert Service

Implemented in:

`backend/app/services/alert_automation_service.py`

The main function is:

`create_alert_for_prediction()`

The service receives:

- the SensorReading
- the generated Prediction
- a risk evaluator

The workflow is:

Prediction

↓

Risk Assessment

↓

No Alert if normal

or

↓

Create Alert if anomalous

Automatically generated Alerts contain:

- `sensor_id`
- `prediction_id`
- `severity`
- `title`
- `message`
- `status`

Default title:

`AI anomaly detected`

Default status:

`open`

The generated message includes contextual information such as:

- SensorReading ID
- actual SensorReading value
- predicted/expected value
- anomaly score
- model name
- model version

---

## Complete AI Traceability Chain

The automated operational chain is now:

SensorReading

↓

Prediction

↓

Alert

Database traceability is maintained through:

`Prediction.source_reading_id → SensorReading.id`

and:

`Alert.prediction_id → Prediction.id`

This allows FactoryPulse to trace an Alert back to:

1. the Prediction that generated it
2. the SensorReading that triggered inference
3. the Sensor that produced the reading
4. the Machine and industrial hierarchy above that Sensor

---

## AI Orchestration Alert Integration

The existing:

`process_sensor_reading()`

workflow now performs:

1. Load historical SensorReadings.
2. Run the configured InferenceEngine.
3. Persist the Prediction.
4. Evaluate Prediction risk.
5. Automatically create an Alert when required.
6. Return the generated Prediction.

Normal Predictions do not generate Alerts.

Anomalous Predictions are passed to the risk evaluator and may generate an Alert.

---

## Risk Evaluation Unit Tests

Implemented in:

`tests/test_ai_risk.py`

Tests verify:

- normal Predictions do not generate Alerts
- anomalous Predictions without scores receive medium severity
- medium-severity classification
- high-severity classification
- critical-severity classification
- invalid risk configuration is rejected

Total risk-evaluation tests:

`6`

---

## Automatic Alert Integration Tests

The AI automation test suite verifies:

### Normal Reading

A normal SensorReading automatically generates a Prediction but does not generate an Alert.

Expected:

`GET /sensors/{sensor_id}/alerts`

returns an empty list.

### Anomalous Reading

The automated test creates a stable baseline consisting of ten SensorReadings with:

`value = 50`

It then creates a new SensorReading with:

`value = 80`

FactoryPulse automatically:

1. persists the SensorReading
2. generates a Prediction
3. classifies the Prediction as anomalous
4. evaluates the risk
5. creates an Alert

The test verifies:

- `Prediction.is_anomaly = true`
- an anomaly score is present
- exactly one Alert is created
- Alert `sensor_id` matches the Sensor
- Alert `prediction_id` matches the anomalous Prediction
- Alert status is `open`
- Alert title is `AI anomaly detected`
- baseline severity is `medium`

---

## Minimum History Behavior

The default StatisticalZScoreEngine requires:

`min_history = 10`

Anomaly classification remains inactive until the Sensor has enough previous readings.

This behavior was confirmed manually.

For example, when a Sensor had only:

`50`

as historical data and then received:

`80`

FactoryPulse generated:

`predicted_value = 50`

but:

`anomaly_score = null`

`is_anomaly = false`

because insufficient history existed.

This is intentional and prevents FactoryPulse from declaring anomalies before a reliable baseline has been established.

---

## Manual Swagger Verification

The complete automatic intelligence loop was manually verified through FastAPI Swagger.

A fresh Sensor was created.

Ten SensorReadings with:

`value = 50`

were submitted to establish a baseline.

An eleventh SensorReading with:

`value = 80`

was then submitted.

No manual Prediction or Alert was created.

FactoryPulse automatically produced an anomalous Prediction.

The Prediction API confirmed:

- expected historical value around `50`
- `is_anomaly = true`
- model `statistical-zscore`

The Alerts API then confirmed that an Alert had automatically been generated.

This manually verifies the same behavior protected by the automated test suite.

---

## Current Automated Test Status

Previous backend suite:

`22 passed`

New risk and Alert automation coverage increased the full suite to:

`30 passed`

Current result:

`30 passed`

All previous hierarchy, authentication fixtures, Prediction traceability, baseline inference, and automatic Prediction tests continue passing.

---

## Current Automated Intelligence Pipeline

FactoryPulse now supports:

SensorReading ingestion

↓

Historical Sensor Data

↓

StatisticalZScoreEngine

↓

InferenceResult

↓

Prediction automatically persisted

↓

Anomaly Risk Evaluation

↓

Alert automatically persisted when required

This is the first complete automated industrial intelligence loop in FactoryPulse.

---

## Next AI Automation Milestone

The next automation layer will build on generated Alerts.

Possible next workflow:

Alert

↓

Notification policy

↓

Notify relevant users

This would extend the current pipeline to:

SensorReading

↓

Prediction

↓

Alert

↓

Notification

Before implementing that layer, the current automatic Alert milestone will be committed and pushed as an independent checkpoint.

---

## Automatic AI Alert Notifications

FactoryPulse now automatically creates in-app Notifications for relevant users when AI anomaly detection generates an Alert.

The complete automated intelligence pipeline is now:

SensorReading

↓

Historical Sensor Data

↓

AI Inference

↓

Prediction

↓

Risk Evaluation

↓

Alert

↓

Notification Policy

↓

Notification

No manual Prediction, Alert, or Notification creation is required during the normal automated workflow.

---

## Notification Recipient Policy

The first FactoryPulse automatic notification policy is role-based.

Automatically generated AI Alerts notify active users with the following roles:

- Admin
- Manager
- Technician

Operators are not automatically notified of every AI anomaly.

Inactive users are excluded.

The current policy is intentionally temporary and role-based because FactoryPulse does not yet contain responsibility assignments such as:

- User → Site
- User → Area
- User → Production Line
- User → Machine

Future versions can evolve toward targeted notifications based on industrial responsibility.

For example:

Alert

↓

Machine

↓

Area / Site

↓

Responsible users

↓

Notification

without changing the existing Alert or Notification persistence architecture.

---

## Eligible User Lookup

The User service now supports:

`get_active_users_by_roles()`

The function retrieves users whose:

- account is active
- Role belongs to the requested role list

The automatic AI notification policy currently requests:

`admin`

`manager`

`technician`

This avoids hardcoding specific user IDs into the automation workflow.

---

## Batch Notification Persistence

The Notification service now supports:

`create_notifications()`

Multiple Notifications can therefore be persisted together using a single database commit.

This is more efficient than committing each recipient Notification independently.

The Notification service also supports:

`get_notified_user_ids_for_alert()`

which is used to determine which users have already received a Notification for a specific Alert.

---

## Notification Automation Service

Implemented in:

`backend/app/services/notification_automation_service.py`

The main function is:

`create_notifications_for_alert()`

Workflow:

Alert

↓

Find eligible active users

↓

Find users already notified for the Alert

↓

Exclude duplicate recipients

↓

Create one in-app Notification per remaining user

Automatically generated Notifications contain:

- `user_id`
- `alert_id`
- `title`
- `message`
- `channel`
- `is_read`

Default channel:

`in_app`

Initial read state:

`false`

The Notification title includes Alert severity.

Example:

`[MEDIUM] AI anomaly detected`

---

## Notification Idempotency

Notification generation is designed to be idempotent at the service level.

If:

`create_notifications_for_alert()`

is called again for the same Alert, FactoryPulse checks which users have already been notified.

Existing recipients are skipped.

This prevents repeated processing of an Alert from generating duplicate in-app Notifications for the same user.

---

## Alert Automation Integration

The automatic Alert service now performs:

Prediction

↓

Risk Assessment

↓

Create Alert

↓

Create Notifications for eligible users

Therefore:

`create_alert_for_prediction()`

does not stop after persisting the Alert.

When an Alert is created successfully, FactoryPulse automatically invokes the Notification automation layer.

Normal Predictions still generate:

- no Alert
- no Notification

---

## Notification Automation Tests

Implemented in:

`tests/test_notification_automation.py`

The automated suite verifies:

### Eligible Roles

An automatically generated AI Alert creates Notifications for:

- active Admin
- active Manager
- active Technician

### Operator Exclusion

An Operator does not automatically receive the AI Alert Notification.

### Inactive User Exclusion

An inactive user with an otherwise eligible role does not receive the Notification.

### Idempotency

Calling Notification generation again for the same Alert does not create duplicate Notifications.

The number of Notifications remains unchanged.

---

## Test Authentication Expansion

The shared automated test environment now includes all four standard FactoryPulse roles:

- Admin
- Manager
- Technician
- Operator

This better reflects the production RBAC model and provides reusable authentication identities for future API and authorization tests.

---

## Current Automated Test Status

Previous backend suite:

`30 passed`

Notification automation tests:

`4 passed`

Current total:

`34 passed`

All previous tests continue passing, including:

- Industrial Hierarchy
- RBAC
- Prediction traceability
- baseline anomaly inference
- AI orchestration
- automatic Prediction generation
- automatic Alert generation
- risk evaluation

---

## Manual Swagger Verification

The complete Notification workflow was also verified manually through FastAPI Swagger.

A fresh Sensor was created.

Ten readings with:

`value = 50`

were submitted to establish the statistical baseline.

An eleventh reading with:

`value = 80`

was then submitted.

Only the SensorReading API was called manually.

FactoryPulse automatically generated:

1. SensorReading
2. Prediction
3. Alert
4. Notification

The generated Prediction was confirmed through:

GET `/sensors/{sensor_id}/predictions`

The generated Alert was confirmed through:

GET `/sensors/{sensor_id}/alerts`

The generated Notification was confirmed through:

GET `/users/{user_id}/notifications`

An eligible Admin user received the Notification.

The Operator did not receive a Notification linked to the new AI Alert.

This confirms that the automatic Notification policy works through the real API workflow as well as through automated tests.

---

## Complete Automated Intelligence Loop

FactoryPulse currently supports:

SensorReading

↓

Historical Sensor Data

↓

StatisticalZScoreEngine

↓

Prediction

↓

Anomaly Detection

↓

Risk Evaluation

↓

Alert

↓

Recipient Policy

↓

In-App Notifications

This completes the first end-to-end automated operational intelligence loop in FactoryPulse AI.



---

## Sensor-Specific AI Configuration Foundation

FactoryPulse now supports persistent AI configuration at the individual Sensor level.

The relationship is:

Sensor

↓

0..1 SensorAIConfig

A Sensor can therefore operate with the FactoryPulse default AI behavior when no custom configuration exists, while selected Sensors can receive their own AI settings.

This prepares the platform for heterogeneous industrial environments where different sensor types and machines require different anomaly-detection behavior.

---

## Sensor AI Configuration Model

Implemented in:

`backend/app/models/sensor_ai_config.py`

Database table:

`sensor_ai_configs`

The model contains:

- `id`
- `sensor_id`
- `is_enabled`
- `engine_name`
- `anomaly_threshold`
- `min_history`
- `history_limit`
- `high_risk_threshold`
- `critical_risk_threshold`
- `created_at`

The relationship is one-to-one from Sensor to SensorAIConfig.

`Sensor.ai_config`

uses:

`uselist=False`

and SensorAIConfig uses a unique `sensor_id`.

Therefore a Sensor cannot have multiple AI configuration rows.

---

## Referential Integrity

`SensorAIConfig.sensor_id`

references:

`sensors.id`

with:

`ON DELETE CASCADE`

Deleting a Sensor therefore automatically removes its AI configuration.

The database constraints use explicit names:

`uq_sensor_ai_configs_sensor_id`

for the unique Sensor relationship.

`fk_sensor_ai_configs_sensor_id`

for the Sensor foreign key.

This was verified directly through PostgreSQL.

---

## Configuration Fields

The current AI configuration supports:

### AI Enablement

`is_enabled`

Controls whether automated AI processing is enabled for the Sensor.

Default:

`true`

### Inference Engine

`engine_name`

Current supported engine:

`statistical-zscore`

The API does not currently accept unsupported engine names because no other production inference implementation exists yet.

### Anomaly Threshold

`anomaly_threshold`

Default:

`3.0`

Determines the Z-score threshold used to classify an observation as anomalous.

### Minimum History

`min_history`

Default:

`10`

Defines how many historical SensorReadings are required before statistical anomaly scoring begins.

### History Limit

`history_limit`

Default:

`50`

Controls the maximum number of previous SensorReadings loaded for inference.

### High Risk Threshold

`high_risk_threshold`

Default:

`5.0`

### Critical Risk Threshold

`critical_risk_threshold`

Default:

`8.0`

These thresholds are used by the anomaly risk evaluation layer.

---

## Backward-Compatible Defaults

The Sensor AI configuration defaults intentionally match the AI behavior that FactoryPulse already used before per-Sensor configuration was introduced:

- anomaly threshold: `3.0`
- minimum history: `10`
- history limit: `50`
- high risk threshold: `5.0`
- critical risk threshold: `8.0`
- engine: `statistical-zscore`

This allows the runtime integration to preserve existing behavior for Sensors without custom configuration.

---

## Sensor AI Configuration Validation

Implemented in:

`backend/app/schemas/sensor_ai_config.py`

Validation rules include:

`anomaly_threshold > 0`

`min_history >= 2`

`history_limit >= 2`

`history_limit >= min_history`

`high_risk_threshold > 0`

`critical_risk_threshold > 0`

`critical_risk_threshold > high_risk_threshold`

Explicit `null` values are rejected during PATCH requests.

---

## Final-State PATCH Validation

Partial configuration updates are validated against the resulting complete configuration rather than validating fields independently.

Example:

Current configuration:

`min_history = 10`

`history_limit = 50`

PATCH:

`min_history = 100`

The resulting configuration would become invalid because:

`history_limit < min_history`

FactoryPulse therefore rejects the request with HTTP 422 and leaves the existing configuration unchanged.

This prevents partial updates from creating internally inconsistent AI settings.

---

## Sensor AI Configuration Service

Implemented in:

`backend/app/services/sensor_ai_config_service.py`

The service supports:

`get_sensor_ai_config_by_sensor_id()`

`create_sensor_ai_config()`

`update_sensor_ai_config()`

The update service merges:

Existing configuration

+

PATCH fields

↓

Complete candidate configuration

↓

Pydantic validation

↓

Database update

A dedicated:

`SensorAIConfigValidationError`

is used to translate final-state configuration errors cleanly into HTTP API responses.

---

## Sensor AI Configuration API

The configuration API is exposed through the Sensor router.

### Create Configuration

POST `/sensors/{sensor_id}/ai-config`

Allowed roles:

- Admin
- Manager

Response:

`201 Created`

Duplicate configuration:

`409 Conflict`

### Read Configuration

GET `/sensors/{sensor_id}/ai-config`

Allowed roles:

- Admin
- Manager
- Technician
- Operator

Response:

`200 OK`

A Sensor without configuration returns:

`404 Sensor AI configuration not found`

### Update Configuration

PATCH `/sensors/{sensor_id}/ai-config`

Allowed roles:

- Admin
- Manager

Response:

`200 OK`

Invalid resulting configuration returns:

`422 Unprocessable Content`

---

## Configuration RBAC

Reading AI configuration is available to all authenticated FactoryPulse roles.

Changing AI configuration is restricted to:

- Admin
- Manager

Technicians and Operators cannot create or modify AI configuration.

This policy reflects the operational impact of changing anomaly thresholds because those settings influence:

Prediction

↓

Anomaly classification

↓

Alert generation

↓

Notification generation

---

## Automated AI Configuration Tests

Implemented in:

`tests/test_sensor_ai_config.py`

The test suite verifies:

- valid configuration creation
- configuration retrieval
- partial PATCH updates
- unchanged fields remain unchanged during PATCH
- duplicate configuration prevention
- unknown Sensor handling
- Sensor without configuration handling
- Technician write restriction
- Operator write restriction
- invalid anomaly threshold rejection
- invalid history relationship rejection
- invalid risk threshold relationship rejection
- explicit null PATCH rejection

The parameterized RBAC test produces separate Technician and Operator test cases.

Dedicated Sensor AI configuration tests:

`12 passed`

Previous FactoryPulse backend total:

`34 passed`

Current backend total:

`46 passed`

---

## Manual Swagger Verification

The Sensor AI configuration API was also verified manually through FastAPI Swagger.

A new Sensor was created and initially confirmed to have no configuration.

GET:

`/sensors/{sensor_id}/ai-config`

correctly returned:

`404 Sensor AI configuration not found`

A custom configuration was then created using:

- anomaly threshold `2.5`
- minimum history `8`
- history limit `40`
- high risk threshold `4.5`
- critical risk threshold `7.0`

The configuration was successfully persisted and retrieved.

A partial PATCH then changed selected values while preserving fields that were not included in the request.

Duplicate configuration creation correctly returned:

`409 Conflict`

An invalid PATCH setting:

`min_history = 100`

while:

`history_limit = 30`

correctly returned:

`422 Unprocessable Content`

A subsequent GET confirmed that the invalid change was not persisted.

---

## Current Configuration Architecture

The current architecture is:

Sensor

↓

SensorAIConfig

↓

Persistent configuration management

↓

Validation

↓

RBAC-controlled API

The next integration stage is:

SensorReading

↓

Load SensorAIConfig

↓

Resolve inference engine and Sensor-specific settings

↓

Load configured history window

↓

Inference

↓

Prediction

↓

Sensor-specific risk evaluation

↓

Alert

↓

Notification

At this stage, SensorAIConfig is fully persisted and managed but has not yet replaced the existing runtime AI defaults.


---

## Sensor-Specific AI Runtime Integration

FactoryPulse now uses Sensor-specific AI configuration during the real SensorReading automation workflow.

Previously, every Sensor used the same globally defined AI behavior.

The runtime now resolves AI settings individually for each Sensor.

The operational flow is:

SensorReading

↓

Resolve Sensor AI settings

↓

Check AI enablement

↓

Build configured inference engine

↓

Load configured historical window

↓

Inference

↓

Prediction

↓

Build configured risk evaluator

↓

Alert

↓

Notification

---

## Runtime AI Settings

Implemented in:

`backend/app/ai/settings.py`

The runtime configuration is represented by:

`AISettings`

It contains:

- `is_enabled`
- `engine_name`
- `anomaly_threshold`
- `min_history`
- `history_limit`
- `high_risk_threshold`
- `critical_risk_threshold`

FactoryPulse also defines:

`DEFAULT_AI_SETTINGS`

with:

- AI enabled: `true`
- engine: `statistical-zscore`
- anomaly threshold: `3.0`
- minimum history: `10`
- history limit: `50`
- high risk threshold: `5.0`
- critical risk threshold: `8.0`

These defaults preserve the behavior that existed before Sensor-specific configuration was introduced.

---

## Runtime Configuration Resolution

Implemented through:

`resolve_sensor_ai_settings()`

The runtime first searches for a SensorAIConfig associated with the current Sensor.

If a configuration exists:

Sensor

↓

SensorAIConfig

↓

AISettings

If no configuration exists:

Sensor

↓

DEFAULT_AI_SETTINGS

This preserves backward compatibility for existing Sensors and avoids requiring configuration rows to be created for every Sensor.

---

## Inference Engine Construction

The runtime now uses:

`build_inference_engine()`

The current supported engine is:

`statistical-zscore`

The Sensor configuration controls:

- anomaly threshold
- minimum history

For example:

`anomaly_threshold = 2.0`

and:

`min_history = 5`

produce a StatisticalZScoreEngine configured specifically for that Sensor.

Unsupported inference engines raise an explicit error.

The architecture therefore provides a clean extension point for future engines such as:

- XGBoost
- Isolation Forest
- Autoencoders
- forecasting-based anomaly detection

without coupling SensorReading ingestion directly to a specific implementation.

---

## Configurable Historical Window

The Sensor-specific:

`history_limit`

is now used by the SensorReading automation service.

FactoryPulse loads only the configured number of previous readings before inference.

Example:

`history_limit = 3`

means the AI engine receives only the three most recent historical readings.

Older SensorReadings remain stored in PostgreSQL but do not participate in that inference operation.

---

## Runtime AI Enablement

The Sensor configuration field:

`is_enabled`

now controls actual AI automation.

When:

`is_enabled = true`

the workflow is:

SensorReading

↓

Prediction

↓

Risk Evaluation

↓

Possible Alert

↓

Possible Notification

When:

`is_enabled = false`

the incoming SensorReading is still persisted.

However FactoryPulse skips:

- Prediction generation
- anomaly classification
- Alert generation
- Notification generation

The behavior becomes:

SensorReading ✅

Prediction ❌

Alert ❌

Notification ❌

This allows AI automation to be disabled for individual Sensors without disabling telemetry ingestion.

---

## Sensor-Specific Risk Evaluation

FactoryPulse now builds an AnomalyRiskEvaluator using the current Sensor's configuration.

The runtime uses:

`build_risk_evaluator()`

with:

- `high_risk_threshold`
- `critical_risk_threshold`

Therefore two Sensors can receive the same anomaly score but classify its operational severity differently.

Example:

Anomaly score:

`2.83`

Sensor A:

`high_risk_threshold = 2.5`

Result:

`HIGH`

Sensor B:

`high_risk_threshold = 3.0`

Result:

`MEDIUM`

This allows Alert severity to reflect the operational sensitivity of different industrial assets.

---

## Updated AI Automation Service

Implemented in:

`backend/app/services/ai_automation_service.py`

`process_sensor_reading()`

now performs:

1. Resolve Sensor AI settings
2. Check `is_enabled`
3. Build the configured inference engine
4. Use the configured history limit
5. Run inference
6. Persist the Prediction
7. Build the configured risk evaluator
8. Generate an Alert when appropriate
9. Continue into Notification automation

The method still allows optional dependency injection of:

`engine`

and:

`history_limit`

for testing and future internal processing.

Normal SensorReading API ingestion does not pass these manually and therefore uses the Sensor-specific configuration automatically.

---

## Runtime Configuration Tests

Implemented in:

`tests/test_sensor_ai_runtime_config.py`

Four dedicated integration tests verify the runtime behavior.

### Sensor-Specific Anomaly Threshold

Two Sensors receive identical historical values:

`48, 49, 50, 51, 52`

and the same new reading:

`54`

The calculated anomaly score is approximately:

`2.83`

Sensor A uses:

`anomaly_threshold = 3.0`

Result:

`is_anomaly = false`

No Alert is generated.

Sensor B uses:

`anomaly_threshold = 2.0`

Result:

`is_anomaly = true`

An Alert is generated.

This proves SensorAIConfig directly influences inference decisions.

### AI Disablement

A Sensor configured with:

`is_enabled = false`

still accepts and stores SensorReadings.

However no:

- Prediction
- Alert
- Notification

is generated.

### Sensor-Specific Risk Thresholds

Two Sensors receive the same anomaly score.

Different risk thresholds result in different Alert severity classifications.

This proves risk evaluation is also controlled per Sensor.

### Configured History Window

A Sensor configured with:

`history_limit = 3`

uses only its three most recent historical readings during inference.

Older readings are excluded from the inference window.

---

## Current Automated Test Status

Previous backend total:

`46 passed`

New runtime configuration tests:

`4 passed`

Current backend total:

`50 passed`

All previous functionality continues passing.

This includes:

- authentication and RBAC
- industrial hierarchy
- Prediction traceability
- statistical anomaly inference
- automatic Prediction generation
- automatic Alert generation
- automatic Notification generation
- Sensor AI configuration API
- Sensor-specific runtime AI behavior

---

## Manual Swagger Runtime Verification

The Sensor-specific runtime behavior was also verified manually through FastAPI Swagger.

Two fresh Sensors were created with identical:

- Sensor type
- historical readings
- test reading
- risk thresholds

The only difference was their anomaly threshold.

Strict Sensor:

`anomaly_threshold = 3.0`

Sensitive Sensor:

`anomaly_threshold = 2.0`

Both Sensors received:

`48, 49, 50, 51, 52`

followed by:

`54`

Both produced approximately the same anomaly score:

`2.83`

The Strict Sensor classified the reading as normal because:

`2.83 < 3.0`

No Alert was generated.

The Sensitive Sensor classified the same reading as anomalous because:

`2.83 >= 2.0`

An AI Alert was generated.

This manually confirms that Sensor-specific configuration controls real inference behavior.

---

## Manual AI Disablement Verification

A separate Sensor was configured with:

`is_enabled = false`

A reading with:

`value = 999`

was submitted.

The SensorReading was successfully persisted.

Subsequent checks confirmed:

SensorReading ✅

Prediction ❌

Alert ❌

This verifies that AI automation can be disabled independently from telemetry ingestion.

---

## Current AI Runtime Architecture

FactoryPulse now supports:

SensorReading

↓

Sensor-specific AI settings

↓

Configured inference engine

↓

Configured history window

↓

Prediction

↓

Configured risk evaluator

↓

Alert

↓

Notification

Each Sensor can therefore have its own anomaly sensitivity and operational risk behavior while remaining part of the same FactoryPulse platform.

This completes the first Sensor-specific configurable AI runtime foundation.


---

## AI Processing Idempotency and Retry Safety

FactoryPulse AI now supports safe reprocessing of already persisted SensorReadings.

Industrial systems may retry work because of:

- worker restarts
- temporary application failures
- network interruptions
- background job retries
- message redelivery
- manual reprocessing
- concurrent processing attempts

Without idempotency protection, processing the same SensorReading more than once could create duplicate:

- Predictions
- Alerts
- Notifications

FactoryPulse now protects the complete automated downstream chain.

---

## Idempotency Scope

Idempotency applies to reprocessing the same persisted SensorReading.

It does not deduplicate separate telemetry events that happen to contain the same value.

Example:

SensorReading #100

`value = 50`

and:

SensorReading #101

`value = 50`

are two legitimate separate readings.

Both may independently produce Predictions.

The protected case is:

SensorReading #100

↓

AI processing

↓

Prediction

followed by another processing attempt of:

SensorReading #100

The second processing attempt must reuse the existing result rather than create a duplicate.

---

## Automated Prediction Identity

An automatically generated Prediction is identified by:

`source_reading_id`

+

`model_name`

+

`model_version`

Example:

SensorReading:

`125`

Model:

`statistical-zscore`

Version:

`1.0`

This combination may exist only once.

This design intentionally does not make:

`source_reading_id`

globally unique.

The same SensorReading may therefore be evaluated by different models or model versions in future FactoryPulse implementations.

Example:

SensorReading #125

↓

`statistical-zscore 1.0`

and:

SensorReading #125

↓

`xgboost 2.0`

can coexist as separate Predictions.

---

## Prediction Database Protection

The Prediction model now includes a PostgreSQL partial unique index:

`ux_predictions_source_model_version`

The protected columns are:

- `source_reading_id`
- `model_name`
- `model_version`

The index applies only when:

`source_reading_id IS NOT NULL`

This means manually created Predictions without a source SensorReading remain unrestricted by this automated-processing identity.

The index also uses:

`NULLS NOT DISTINCT`

so a nullable model version cannot bypass uniqueness.

Database rule:

`(source_reading_id, model_name, model_version)`

must be unique for automatically traceable Predictions.

---

## Prediction Retry Service

The Prediction service now supports:

`get_prediction_by_source_and_model()`

and:

`create_prediction_idempotently()`

The workflow is:

Prediction request

↓

Source reading exists?

↓

Check existing Prediction using:

`source_reading_id + model_name + model_version`

↓

Existing Prediction found?

YES

↓

Return existing Prediction

NO

↓

Attempt creation

↓

Concurrent insert conflict?

NO

↓

Return newly created Prediction

YES

↓

Rollback failed transaction

↓

Load the Prediction created by the competing worker

↓

Return existing Prediction

This provides both:

- application-level graceful reuse
- database-level uniqueness enforcement

Manual Predictions where:

`source_reading_id = null`

continue using ordinary Prediction creation.

---

## Alert Identity

An AI-generated Prediction can produce at most one Alert.

The Alert identity is therefore:

`prediction_id`

A Prediction-linked Alert must not be duplicated during retries.

Manual Alerts with:

`prediction_id = null`

remain unrestricted.

---

## Alert Database Protection

The Alert model now includes the PostgreSQL partial unique index:

`ux_alerts_prediction_id`

The index enforces:

`UNIQUE (prediction_id)`

when:

`prediction_id IS NOT NULL`

Therefore:

Prediction #25

↓

Alert #10

is valid.

A second Alert referencing:

Prediction #25

is rejected by PostgreSQL.

Manual Alerts without a Prediction reference remain unaffected.

---

## Alert Retry Service

The Alert service now supports:

`get_alert_by_prediction_id()`

and:

`create_alert_idempotently()`

The workflow is:

Prediction

↓

Evaluate risk

↓

Alert required?

↓

Check existing Alert for Prediction

↓

Existing Alert?

YES

↓

Reuse it

NO

↓

Attempt creation

↓

Concurrent insert conflict?

YES

↓

Rollback

↓

Retrieve Alert created by the competing worker

↓

Reuse it

The automatic Alert workflow now uses this idempotent creation path.

---

## Notification Identity

For Alert-based notifications, delivery identity is defined by:

`user_id`

+

`alert_id`

+

`channel`

This allows one recipient to receive the same Alert through multiple channels in future.

Example:

User #5 + Alert #12 + `in_app` ✅

User #5 + Alert #12 + `email` ✅

User #5 + Alert #12 + `sms` ✅

However:

User #5 + Alert #12 + `in_app`

cannot be stored twice.

---

## Notification Database Protection

The Notification model now includes:

`ux_notifications_user_alert_channel`

The partial unique index protects:

- `user_id`
- `alert_id`
- `channel`

when:

`alert_id IS NOT NULL`

Notifications unrelated to an Alert remain unrestricted.

This gives FactoryPulse database-level duplicate protection for Alert delivery records.

---

## Concurrency-Safe Notification Persistence

Notification persistence now uses PostgreSQL:

`INSERT ... ON CONFLICT DO NOTHING`

for automatic batch Notification generation.

The workflow is:

Find eligible recipients

↓

Remove users already notified

↓

Attempt batch Notification insert

↓

PostgreSQL unique index verifies:

`user_id + alert_id + channel`

↓

Non-conflicting Notifications are inserted

↓

Concurrent duplicate attempts are ignored

↓

Only newly created Notification IDs are returned

This prevents an IntegrityError from escaping when two workers attempt to create the same Alert Notification concurrently.

FactoryPulse therefore combines:

- recipient pre-filtering
- database uniqueness
- PostgreSQL conflict handling

for Notification retry safety.

---

## Complete Retry-Safe AI Pipeline

The automated pipeline now behaves as:

SensorReading

↓

Resolve Sensor-specific AI settings

↓

Resolve model identity

↓

Prediction

├── application-level reuse

└── database uniqueness

↓

Risk Evaluation

↓

Alert

├── application-level reuse

└── database uniqueness

↓

Recipient Resolution

↓

Notification

├── existing-recipient filtering

├── database uniqueness

└── `ON CONFLICT DO NOTHING`

This allows the same persisted SensorReading to be processed repeatedly without duplicating downstream operational records.

---

## Database Idempotency Constraints

The current database-backed protections are:

### Prediction

Index:

`ux_predictions_source_model_version`

Identity:

`source_reading_id + model_name + model_version`

### Alert

Index:

`ux_alerts_prediction_id`

Identity:

`prediction_id`

### Notification

Index:

`ux_notifications_user_alert_channel`

Identity:

`user_id + alert_id + channel`

Together these indexes act as the final concurrency-safety layer even if multiple application workers process the same event.

---

## Retry Integration Test

Implemented in:

`tests/test_ai_idempotency.py`

The test creates:

- one industrial hierarchy
- one Sensor
- ten baseline SensorReadings
- one anomalous SensorReading

The anomalous SensorReading initially triggers the normal automatic pipeline.

FactoryPulse creates:

1. Prediction
2. Alert
3. Notifications

The test then deliberately calls:

`process_sensor_reading()`

multiple additional times using the exact same persisted anomalous SensorReading.

After repeated processing, the database is verified.

Expected result:

SensorReading:

`1`

Prediction for the reading/model/version:

`1`

Alert for the Prediction:

`1`

Automatic in-app Notifications:

`3`

The Notifications correspond to the eligible test roles:

- Admin
- Manager
- Technician

Each recipient appears only once.

The Operator remains excluded by the existing automatic Notification policy.

The retry calls also return the same persisted Prediction ID.

This proves application-level reuse and database-level protections work together.

---

## Automated Test Status

Previous backend total:

`50 passed`

New explicit retry/idempotency integration test:

`1 passed`

Current backend total:

`51 passed`

All previous tests remain passing.

The complete test suite now covers:

- health and test environment isolation
- authentication and RBAC
- industrial hierarchy
- Prediction source traceability
- baseline statistical inference
- automatic Prediction generation
- anomaly risk evaluation
- automatic Alert generation
- automatic Notification generation
- Notification recipient policy
- Sensor-specific AI configuration
- Sensor-specific runtime inference behavior
- configurable history windows
- AI enablement and disablement
- Sensor-specific risk thresholds
- Prediction retry safety
- Alert retry safety
- Notification duplicate protection
- end-to-end AI pipeline idempotency

---

## Current AI Reliability Architecture

FactoryPulse now combines:

Configuration

↓

Automated inference

↓

Traceability

↓

Risk evaluation

↓

Operational Alerting

↓

Notification routing

↓

Idempotent persistence

↓

Database concurrency protection

The same persisted industrial event can therefore be safely retried without producing duplicate AI Predictions, operational Alerts, or Alert Notifications.

This establishes the first robust retry-safe processing foundation for future background workers, message queues, distributed processing, and asynchronous AI execution.


## AI Processing State and Observability

FactoryPulse AI now persists the execution state of AI processing for each sensor reading.

This provides operational visibility into whether a reading was processed successfully, skipped, retried, or failed.

### Processing State Model

AI processing state is stored separately from `SensorReading` using the `AIProcessingState` model.

The relationship is:

```text
SensorReading
    ├── Prediction(s)
    └── AIProcessingState(s)
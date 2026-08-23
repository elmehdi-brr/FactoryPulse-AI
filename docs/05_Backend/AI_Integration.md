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
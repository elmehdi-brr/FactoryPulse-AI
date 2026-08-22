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
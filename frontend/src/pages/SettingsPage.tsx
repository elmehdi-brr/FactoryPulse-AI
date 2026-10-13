import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Gauge,
  Save,
  ShieldCheck,
  SlidersHorizontal,
} from 'lucide-react'
import { motion } from 'motion/react'
import { useEffect, useMemo, useState } from 'react'

import { useAuth } from '../auth/authContext'
import { ApiError } from '../services/api'
import {
  createSensorAIConfig,
  getSensorAIConfig,
  getSensors,
  updateSensorAIConfig,
} from '../services/sensors'
import { getMachines } from '../services/machines'

import type { Machine, MachineSensor } from '../types/machine'
import type {
  SensorAIConfig,
  SensorAIConfigValues,
} from '../types/sensor-ai-config'

const DEFAULT_CONFIG: SensorAIConfigValues = {
  is_enabled: true,
  engine_name: 'statistical-zscore',
  anomaly_threshold: 3,
  min_history: 10,
  history_limit: 50,
  high_risk_threshold: 5,
  critical_risk_threshold: 8,
}

function getErrorMessage(
  error: unknown,
  fallback: string,
): string {
  return error instanceof ApiError
    ? error.message
    : fallback
}

function toConfigValues(
  config: SensorAIConfig,
): SensorAIConfigValues {
  return {
    is_enabled: config.is_enabled,
    engine_name: config.engine_name,
    anomaly_threshold: config.anomaly_threshold,
    min_history: config.min_history,
    history_limit: config.history_limit,
    high_risk_threshold: config.high_risk_threshold,
    critical_risk_threshold: config.critical_risk_threshold,
  }
}

function formatLabel(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function SettingsPage() {
  const { user } = useAuth()

  const canManage =
    user?.role_name === 'admin' ||
    user?.role_name === 'manager'

  const [sensors, setSensors] = useState<MachineSensor[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [selectedSensorId, setSelectedSensorId] =
    useState<number | null>(null)

  const [configuration, setConfiguration] =
    useState<SensorAIConfig | null>(null)

  const [draft, setDraft] =
    useState<SensorAIConfigValues | null>(null)

  const [loadingSensors, setLoadingSensors] = useState(true)
  const [loadingConfig, setLoadingConfig] = useState(false)
  const [saving, setSaving] = useState(false)

  const [pageError, setPageError] = useState<string | null>(null)
  const [configError, setConfigError] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadWorkspace() {
      setLoadingSensors(true)
      setPageError(null)

      try {
        const [sensorResults, machineResults] =
          await Promise.all([
            getSensors(),
            getMachines(),
          ])

        if (cancelled) return

        setSensors(sensorResults)
        setMachines(machineResults)
      } catch (error) {
        if (!cancelled) {
          setPageError(
            getErrorMessage(
              error,
              'Unable to load sensors and machines.',
            ),
          )
        }
      } finally {
        if (!cancelled) {
          setLoadingSensors(false)
        }
      }
    }

    void loadWorkspace()

    return () => {
      cancelled = true
    }
  }, [])

  const machinesById = useMemo(
    () => new Map(machines.map((machine) => [machine.id, machine])),
    [machines],
  )

  const selectedSensor = sensors.find(
    (sensor) => sensor.id === selectedSensorId,
  ) ?? null

  const selectedMachine = selectedSensor
    ? machinesById.get(selectedSensor.machine_id)
    : undefined

  useEffect(() => {
    if (selectedSensorId === null) return

    const sensorId = selectedSensorId
    let cancelled = false

    async function loadConfiguration() {
      setLoadingConfig(true)
      setConfiguration(null)
      setDraft({ ...DEFAULT_CONFIG })
      setConfigError(null)
      setFormError(null)
      setFeedback(null)

      try {
        const result = await getSensorAIConfig(sensorId)

        if (cancelled) return

        setConfiguration(result)
        setDraft(
          result
            ? toConfigValues(result)
            : { ...DEFAULT_CONFIG },
        )
      } catch (error) {
        if (!cancelled) {
          setConfigError(
            getErrorMessage(
              error,
              'Unable to load this sensor configuration.',
            ),
          )
          setDraft(null)
        }
      } finally {
        if (!cancelled) {
          setLoadingConfig(false)
        }
      }
    }

    void loadConfiguration()

    return () => {
      cancelled = true
    }
  }, [selectedSensorId])

  function updateDraft<K extends keyof SensorAIConfigValues>(
    key: K,
    value: SensorAIConfigValues[K],
  ) {
    setDraft((current) =>
      current
        ? { ...current, [key]: value }
        : current,
    )

    setFormError(null)
    setFeedback(null)
  }

  async function handleSave() {
    if (!selectedSensor || !draft || !canManage) return

    if (
      !Number.isFinite(draft.anomaly_threshold) ||
      !Number.isFinite(draft.min_history) ||
      !Number.isFinite(draft.history_limit) ||
      !Number.isFinite(draft.high_risk_threshold) ||
      !Number.isFinite(draft.critical_risk_threshold) ||
      draft.anomaly_threshold <= 0 ||
      draft.min_history < 2 ||
      !Number.isInteger(draft.min_history) ||
      draft.history_limit < 2 ||
      !Number.isInteger(draft.history_limit) ||
      draft.high_risk_threshold <= 0 ||
      draft.critical_risk_threshold <= 0
    ) {
      setFormError(
        'Thresholds must be positive. History values must be integers of at least 2.',
      )
      return
    }

    if (draft.history_limit < draft.min_history) {
      setFormError(
        'History limit must be greater than or equal to minimum history.',
      )
      return
    }

    if (draft.critical_risk_threshold <= draft.high_risk_threshold) {
      setFormError(
        'Critical risk threshold must be greater than high risk threshold.',
      )
      return
    }

    setSaving(true)
    setFormError(null)
    setConfigError(null)
    setFeedback(null)

    try {
      const saved = configuration
        ? await updateSensorAIConfig(selectedSensor.id, draft)
        : await createSensorAIConfig(selectedSensor.id, draft)

      setConfiguration(saved)
      setDraft(toConfigValues(saved))
      setFeedback('AI configuration saved successfully.')
    } catch (error) {
      setFormError(
        getErrorMessage(
          error,
          'Unable to save this configuration.',
        ),
      )
    } finally {
      setSaving(false)
    }
  }

  const configured = configuration !== null

  return (
    <div className="settings-page">
      <section className="page-heading settings-heading">
        <div>
          <p className="page-eyebrow">
            Platform configuration
          </p>

          <h1>Settings.</h1>

          <p>
            Configure sensor-level anomaly detection,
            history windows, and risk thresholds.
          </p>
        </div>

        <div className="settings-access-pill">
          <ShieldCheck size={16} />
          {canManage ? 'Configuration access' : 'Read-only access'}
        </div>
      </section>

      {pageError && (
        <div className="dashboard-data-error" role="alert">
          <AlertTriangle size={17} />
          <div>
            <strong>Settings unavailable</strong>
            <span>{pageError}</span>
          </div>
        </div>
      )}

      <section className="settings-summary-grid">
        <motion.article
          className="settings-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="settings-summary-icon">
            <Cpu size={19} />
          </div>
          <span>Available sensors</span>
          <strong>
            {loadingSensors ? '—' : sensors.length}
          </strong>
          <small>Sensors available for configuration</small>
        </motion.article>

        <motion.article
          className="settings-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <div className="settings-summary-icon">
            <Gauge size={19} />
          </div>
          <span>Selected sensor</span>
          <strong>
            {selectedSensor ? `#${selectedSensor.id}` : '—'}
          </strong>
          <small>
            {selectedSensor?.name ?? 'Select a sensor to continue'}
          </small>
        </motion.article>

        <motion.article
          className="settings-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="settings-summary-icon">
            <Activity size={19} />
          </div>
          <span>Configuration state</span>
          <strong>
            {loadingConfig
              ? 'Loading'
              : !selectedSensor
                ? '—'
                : configured
                  ? 'Saved'
                  : configError
                    ? 'Error'
                    : 'Not saved'}
          </strong>
          <small>
            {configured
              ? 'Stored in the database'
              : 'Settings are not persisted until saved'}
          </small>
        </motion.article>
      </section>

      <section className="settings-workspace">
        <aside className="settings-sensor-panel">
          <div className="settings-panel-heading">
            <div>
              <span className="panel-eyebrow">
                Configuration scope
              </span>
              <h2>Sensors</h2>
            </div>

            <span className="settings-count">
              {sensors.length}
            </span>
          </div>

          {loadingSensors ? (
            <div className="settings-state">
              Loading sensors...
            </div>
          ) : sensors.length === 0 ? (
            <div className="settings-empty">
              <Cpu size={24} />
              <strong>No sensors found</strong>
              <span>
                Add a sensor to a machine before configuring AI detection.
              </span>
            </div>
          ) : (
            <div className="settings-sensor-list">
              {sensors.map((sensor) => {
                const machine = machinesById.get(sensor.machine_id)
                const active = sensor.id === selectedSensorId

                return (
                  <button
                    key={sensor.id}
                    type="button"
                    className={
                      active
                        ? 'settings-sensor-option settings-sensor-option-selected'
                        : 'settings-sensor-option'
                    }
                    onClick={() => {
                        if (selectedSensorId === sensor.id) {
                            setSelectedSensorId(null)
                            setConfiguration(null)
                            setDraft(null)
                            setConfigError(null)
                            setFormError(null)
                            setFeedback(null)
                            setLoadingConfig(false)
                        } else {
                            setSelectedSensorId(sensor.id)
                        }
                    }}
                    aria-pressed={active}
                  >
                    <span className="settings-sensor-icon">
                      <Cpu size={17} />
                    </span>

                    <span className="settings-sensor-copy">
                      <strong>{sensor.name}</strong>
                      <small>
                        {machine?.name ?? `Machine #${sensor.machine_id}`}
                      </small>
                      <small>
                        {formatLabel(sensor.sensor_type)} · {sensor.unit}
                      </small>
                    </span>

                    <span
                      className={
                        sensor.status.toLowerCase() === 'active'
                          ? 'settings-sensor-status settings-sensor-status-active'
                          : 'settings-sensor-status'
                      }
                    >
                      {formatLabel(sensor.status)}
                    </span>
                  </button>
                )
              })}
            </div>
          )}
        </aside>

        <div className="settings-config-panel">
          {!selectedSensor ? (
            <div className="settings-empty settings-config-empty">
              <SlidersHorizontal size={26} />
              <strong>Select a sensor</strong>
              <span>
                Choose a sensor from the list to inspect its AI detection settings.
              </span>
            </div>
          ) : (
            <>
              <header className="settings-config-heading">
                <div>
                  <span className="panel-eyebrow">
                    Sensor AI configuration
                  </span>
                  <h2>{selectedSensor.name}</h2>
                  <p>
                    {selectedMachine?.name ?? `Machine #${selectedSensor.machine_id}`}
                    {' · '}
                    Sensor #{selectedSensor.id}
                  </p>
                </div>

                <span
                  className={
                    configured
                      ? 'settings-config-badge settings-config-badge-saved'
                      : 'settings-config-badge settings-config-badge-unsaved'
                  }
                >
                  {configured ? 'Configuration saved' : 'Not configured'}
                </span>
              </header>

              <p className="settings-config-intro">
                The selected configuration controls how this sensor's readings
                are evaluated for anomalies and assigned a risk level.
              </p>

              {loadingConfig ? (
                <div className="settings-state">
                  Loading sensor configuration...
                </div>
              ) : configError ? (
                <div className="dashboard-data-error" role="alert">
                  <AlertTriangle size={17} />
                  <div>
                    <strong>Could not load configuration</strong>
                    <span>{configError}</span>
                  </div>
                </div>
              ) : draft ? (
                <>
                  {!configured && (
                    <div className="settings-default-notice">
                      <SlidersHorizontal size={17} />
                      <span>
                        Default values are shown below. They haven't been
                        saved for this sensor yet.
                      </span>
                    </div>
                  )}

                  <div className="settings-config-form">
                    <div className="settings-section-heading">
                      <SlidersHorizontal size={17} />
                      <h3>Detection engine</h3>
                    </div>

                    <div className="settings-engine-card">
                      <div className="settings-engine-icon">
                        <Activity size={21} />
                      </div>
                      <div>
                        <strong>Statistical Z-score</strong>
                        <p>
                          Detects unusual readings using deviation from the
                          sensor's recent history.
                        </p>
                      </div>
                      <span className="settings-engine-tag">
                        Available
                      </span>
                    </div>

                    <label className="settings-toggle-row">
                      <span className="settings-toggle-copy">
                        <strong>Enable AI detection</strong>
                        <small>
                          Allow this sensor's AI configuration to be used by
                          the detection service.
                        </small>
                      </span>
                      <input
                        type="checkbox"
                        checked={draft.is_enabled}
                        disabled={!canManage || saving}
                        onChange={(event) =>
                          updateDraft('is_enabled', event.target.checked)
                        }
                      />
                    </label>

                    <div className="settings-section-heading">
                      <Gauge size={17} />
                      <h3>Detection sensitivity</h3>
                    </div>

                    <div className="settings-field-grid">
                      <label className="settings-field">
                        <span>Anomaly threshold</span>
                        <small>
                          Z-score at which a reading is flagged.
                        </small>
                        <input
                          type="number"
                          className="settings-input"
                          min={0.1}
                          step={0.1}
                          value={draft.anomaly_threshold}
                          disabled={!canManage || saving}
                          onChange={(event) =>
                            updateDraft(
                              'anomaly_threshold',
                              Number(event.target.value),
                            )
                          }
                        />
                      </label>

                      <label className="settings-field">
                        <span>Minimum history</span>
                        <small>
                          Minimum readings required before detection.
                        </small>
                        <input
                          type="number"
                          className="settings-input"
                          min={2}
                          step={1}
                          value={draft.min_history}
                          disabled={!canManage || saving}
                          onChange={(event) =>
                            updateDraft(
                              'min_history',
                              Number(event.target.value),
                            )
                          }
                        />
                      </label>

                      <label className="settings-field">
                        <span>History limit</span>
                        <small>
                          Maximum number of historical readings retained.
                        </small>
                        <input
                          type="number"
                          className="settings-input"
                          min={2}
                          step={1}
                          value={draft.history_limit}
                          disabled={!canManage || saving}
                          onChange={(event) =>
                            updateDraft(
                              'history_limit',
                              Number(event.target.value),
                            )
                          }
                        />
                      </label>
                    </div>

                    <div className="settings-section-heading">
                      <Gauge size={17} />
                      <h3>Risk classification</h3>
                    </div>

                    <div className="settings-field-grid">
                      <label className="settings-field">
                        <span>High risk threshold</span>
                        <small>
                          Minimum score for the high-risk level.
                        </small>
                        <input
                          type="number"
                          className="settings-input"
                          min={0.1}
                          step={0.1}
                          value={draft.high_risk_threshold}
                          disabled={!canManage || saving}
                          onChange={(event) =>
                            updateDraft(
                              'high_risk_threshold',
                              Number(event.target.value),
                            )
                          }
                        />
                      </label>

                      <label className="settings-field">
                        <span>Critical risk threshold</span>
                        <small>
                          Minimum score for the critical level.
                        </small>
                        <input
                          type="number"
                          className="settings-input"
                          min={0.1}
                          step={0.1}
                          value={draft.critical_risk_threshold}
                          disabled={!canManage || saving}
                          onChange={(event) =>
                            updateDraft(
                              'critical_risk_threshold',
                              Number(event.target.value),
                            )
                          }
                        />
                      </label>
                    </div>

                    <div className="settings-validation-note">
                      Critical risk must exceed high risk. History limit
                      must be at least the minimum history value.
                    </div>
                  </div>

                  {!canManage && (
                    <div className="settings-readonly-note">
                      <ShieldCheck size={17} />
                      <span>
                        Your role allows you to inspect these settings but
                        not modify them.
                      </span>
                    </div>
                  )}

                  {formError && (
                    <div
                      className="settings-feedback settings-feedback-error"
                      role="alert"
                    >
                      <AlertTriangle size={17} />
                      {formError}
                    </div>
                  )}

                  {feedback && (
                    <div
                      className="settings-feedback settings-feedback-success"
                      role="status"
                    >
                      <CheckCircle2 size={17} />
                      {feedback}
                    </div>
                  )}

                  {canManage && (
                    <div className="settings-save-row">
                      <span>
                        {configured
                          ? `Configuration #${configuration?.id}`
                          : 'New configuration · defaults can be adjusted'}
                      </span>

                      <button
                        type="button"
                        className="settings-save-button"
                        disabled={saving}
                        onClick={() => void handleSave()}
                      >
                        <Save size={16} />
                        {saving
                          ? 'Saving...'
                          : configured
                            ? 'Save changes'
                            : 'Create configuration'}
                      </button>
                    </div>
                  )}
                </>
              ) : null}
            </>
          )}
        </div>
      </section>
    </div>
  )
}
import {
  Activity,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Search,
  UserRound,
  Wrench,
} from 'lucide-react'
import { motion } from 'motion/react'
import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import { useAuth } from '../auth/authContext'
import { ApiError } from '../services/api'
import {
  getMaintenanceRecords,
  updateMaintenanceRecord,
} from '../services/maintenance'
import {
  getMachineMaintenanceEffectiveness,
  getMachines,
} from '../services/machines'
import type {
  Machine,
  MachineMaintenanceEffectiveness,
  MachineMaintenanceRecord,
} from '../types/machine'

type MaintenancePageData = {
  records: MachineMaintenanceRecord[]
  machines: Machine[]
}

const STATUS_OPTIONS = [
  'planned',
  'in_progress',
  'completed',
  'verified',
  'cancelled',
] as const

type MaintenanceStatus = MachineMaintenanceRecord['status']

type MaintenanceStatusAction = {
  status: MaintenanceStatus
  label: string
}

const STATUS_ACTIONS: Record<
  MaintenanceStatus,
  MaintenanceStatusAction[]
> = {
  planned: [
    { status: 'in_progress', label: 'Start intervention' },
    { status: 'cancelled', label: 'Cancel intervention' },
  ],
  in_progress: [
    { status: 'completed', label: 'Mark as completed' },
    { status: 'cancelled', label: 'Cancel intervention' },
  ],
  completed: [
    { status: 'verified', label: 'Verify intervention' },
  ],
  verified: [],
  cancelled: [],
}

function normalizeValue(value: string): string {
  return value.trim().toLowerCase()
}

function formatLabel(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    )
}

function formatMaintenanceDate(
  value: string | null,
): string {
  if (!value) {
    return 'Not performed'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown date'
  }

  return date.toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function getStatusClass(status: string): string {
  const normalized = normalizeValue(status)
    .replace(/[^a-z0-9-]/g, '-')

  return `maintenance-status maintenance-status-${normalized}`
}

function getTypeClass(type: string): string {
  return `maintenance-type maintenance-type-${normalizeValue(type)}`
}

function formatMaintenanceRate(
  value: number | null,
): string {
  if (value === null) {
    return '—'
  }

  return `${(value * 100).toFixed(1)}%`
}

function formatResponseDuration(
  seconds: number | null,
): string {
  if (seconds === null) {
    return '—'
  }

  if (seconds < 60) {
    return `${Math.round(seconds)} sec`
  }

  if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)} min`
  }

  return `${(seconds / 3600).toFixed(1)} h`
}

export function MaintenancePage() {

  const { user } = useAuth()

  const canUpdateMaintenance =
    user?.role_name === 'admin' ||
    user?.role_name === 'technician'

  const [updatingRecordId, setUpdatingRecordId] =
    useState<number | null>(null)

  const [actionError, setActionError] =
    useState<string | null>(null)

  const [actionNotice, setActionNotice] =
    useState<string | null>(null)

  const [maintenanceRefreshToken, setMaintenanceRefreshToken] =
    useState(0)
  const [data, setData] =
    useState<MaintenancePageData | null>(null)

  const [loading, setLoading] = useState(true)

  const [error, setError] = useState<string | null>(
    null,
  )

  const [search, setSearch] = useState('')

  const [statusFilter, setStatusFilter] =
    useState('all')

  const [typeFilter, setTypeFilter] =
    useState('all')

  const [selectedRecordId, setSelectedRecordId] =
    useState<number | null>(null)


  const [
    maintenanceEffectiveness,
    setMaintenanceEffectiveness,
  ] = useState<MachineMaintenanceEffectiveness | null>(
    null,
  )

  const [
    loadingEffectiveness,
    setLoadingEffectiveness,
  ] = useState(false)

  const [
    effectivenessError,
    setEffectivenessError,
  ] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadMaintenanceWorkspace() {
      setLoading(true)
      setError(null)

      try {
        const [records, machines] =
          await Promise.all([
            getMaintenanceRecords(),
            getMachines(),
          ])

        if (!cancelled) {
          setData({
            records,
            machines,
          })
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load the maintenance workspace.',
        )
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadMaintenanceWorkspace()

    return () => {
      cancelled = true
    }
  }, [])

  const records = useMemo(
    () => data?.records ?? [],
    [data],
  )

  const machines = useMemo(
    () => data?.machines ?? [],
    [data],
  )

  const machinesById = useMemo(
    () =>
      new Map(
        machines.map((machine) => [
          machine.id,
          machine,
        ]),
      ),
    [machines],
  )

  const filteredRecords = useMemo(() => {
    const query = normalizeValue(search)

    return [...records]
      .filter((record) => {
        const machine = machinesById.get(
          record.machine_id,
        )

        const searchFields = [
          String(record.id),
          record.description,
          record.maintenance_type,
          record.status,
          machine?.name ?? '',
          machine?.code ?? '',
          String(record.machine_id),
          String(record.alert_id ?? ''),
          String(record.performed_by_user_id ?? ''),
        ]

        const matchesSearch =
          !query ||
          searchFields.some((value) =>
            normalizeValue(value).includes(query),
          )

        const matchesStatus =
          statusFilter === 'all' ||
          normalizeValue(record.status) ===
            normalizeValue(statusFilter)

        const matchesType =
          typeFilter === 'all' ||
          normalizeValue(record.maintenance_type) ===
            normalizeValue(typeFilter)

        return (
          matchesSearch &&
          matchesStatus &&
          matchesType
        )
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      )
  }, [
    records,
    machinesById,
    search,
    statusFilter,
    typeFilter,
  ])

  const selectedRecord =
    filteredRecords.find(
        (record) => record.id === selectedRecordId,
    ) ?? null

  const selectedMachine = selectedRecord
    ? machinesById.get(selectedRecord.machine_id)
    : undefined
  const selectedMachineId =
    selectedRecord?.machine_id ?? null

  const statusActions = selectedRecord
    ? STATUS_ACTIONS[selectedRecord.status]
    : []

  useEffect(() => {
  if (selectedMachineId === null) {
    return
  }

  const machineId = selectedMachineId
    let cancelled = false

    async function loadEffectiveness() {
      setLoadingEffectiveness(true)
      setEffectivenessError(null)
      setMaintenanceEffectiveness(null)

      try {
        const response =
          await getMachineMaintenanceEffectiveness(
            machineId,
          )

        if (!cancelled) {
          setMaintenanceEffectiveness(response)
        }
      } catch (requestError) {
        if (cancelled) {
          return
        }

        setEffectivenessError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Unable to load maintenance effectiveness.',
        )

        setMaintenanceEffectiveness(null)
      } finally {
        if (!cancelled) {
          setLoadingEffectiveness(false)
        }
      }
    }

    void loadEffectiveness()

    return () => {
      cancelled = true
    }
  }, [selectedMachineId, maintenanceRefreshToken])

  async function handleStatusChange(
    nextStatus: MaintenanceStatus,
  ) {
    if (
      !selectedRecord ||
      !canUpdateMaintenance ||
      updatingRecordId !== null
    ) {
      return
    }

    const recordId = selectedRecord.id

    setUpdatingRecordId(recordId)
    setActionError(null)
    setActionNotice(null)

    try {
      const updatedRecord = await updateMaintenanceRecord(
        recordId,
        { status: nextStatus },
      )

      setData((current) => {
        if (!current) {
          return current
        }

        return {
          ...current,
          records: current.records.map((record) =>
            record.id === updatedRecord.id
              ? updatedRecord
              : record,
          ),
        }
      })

      setActionNotice(
        `Record #${updatedRecord.id} updated to ${formatLabel(updatedRecord.status)}.`,
      )

      setMaintenanceRefreshToken((current) => current + 1)
    } catch (requestError) {
      setActionError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Unable to update the maintenance status.',
      )
    } finally {
      setUpdatingRecordId(null)
    }
  }

  const inProgressCount = records.filter(
    (record) =>
      normalizeValue(record.status) === 'in_progress',
  ).length

  const finishedCount = records.filter(
    (record) =>
      normalizeValue(record.status) === 'completed' ||
      normalizeValue(record.status) === 'verified',
  ).length

  const preventiveCount = records.filter(
    (record) =>
      normalizeValue(record.maintenance_type) ===
      'preventive',
  ).length

  const preventiveShare =
    records.length > 0
      ? Math.round(
          (preventiveCount / records.length) * 100,
        )
      : null

  return (
    <div className="maintenance-page">
      <section className="page-heading">
        <div>
          <p className="page-eyebrow">
            Maintenance Intelligence
          </p>

          <h1>Maintenance.</h1>

          <p>
            Track interventions, review machine history,
            and understand the current maintenance workload.
          </p>
        </div>

        <div className="maintenance-page-indicator">
          <Wrench size={15} />
          Maintenance register
        </div>
      </section>

      {error && (
        <div
          className="dashboard-data-error"
          role="alert"
        >
          <Wrench size={17} />

          <div>
            <strong>Maintenance data unavailable</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      <section className="maintenance-summary-grid">
        <motion.article
          className="maintenance-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="maintenance-summary-icon">
            <ClipboardCheck size={19} />
          </div>

          <span>Total maintenance records</span>

          <strong>
            {loading ? '—' : records.length}
          </strong>

          <small>
            Recorded interventions across all machines
          </small>
        </motion.article>

        <motion.article
          className="maintenance-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <div className="maintenance-summary-icon">
            <Clock3 size={19} />
          </div>

          <span>In progress</span>

          <strong>
            {loading ? '—' : inProgressCount}
          </strong>

          <small>
            Interventions currently underway
          </small>
        </motion.article>

        <motion.article
          className="maintenance-summary-card"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="maintenance-summary-icon">
            <Activity size={19} />
          </div>

          <span>Preventive maintenance</span>

          <strong>
            {loading
              ? '—'
              : preventiveShare === null
                ? '—'
                : `${preventiveShare}%`}
          </strong>

          <small>
            {loading
              ? 'Calculating from registered records'
              : `${preventiveCount} of ${records.length} records are preventive`}
          </small>
        </motion.article>
      </section>

      <section className="maintenance-workspace">
        <div className="maintenance-register-panel">
          <div className="maintenance-panel-header">
            <div>
              <span className="panel-eyebrow">
                Intervention management
              </span>

              <h2>Maintenance register</h2>
            </div>

            <span className="maintenance-result-count">
              {filteredRecords.length}
            </span>
          </div>

          <div className="maintenance-toolbar">
            <label className="maintenance-search">
              <Search size={17} />

              <input
                type="search"
                value={search}
                onChange={(event) => {
                    setSearch(event.target.value)
                    setSelectedRecordId(null)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                placeholder="Search descriptions, machines, IDs..."
                aria-label="Search maintenance records"
              />
            </label>

            <div className="maintenance-filter-row">
              <label>
                <span>Status</span>

                <select
                  value={statusFilter}
                  onChange={(event) => {
                    setStatusFilter(event.target.value)
                    setSelectedRecordId(null)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                >
                  <option value="all">
                    All statuses
                  </option>

                  {STATUS_OPTIONS.map((status) => (
                    <option
                      key={status}
                      value={status}
                    >
                      {formatLabel(status)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Type</span>

                <select
                  value={typeFilter}
                  onChange={(event) => {
                    setTypeFilter(event.target.value)
                    setSelectedRecordId(null)
                    setActionError(null)
                    setActionNotice(null)
                  }}
                >
                  <option value="all">
                    All types
                  </option>

                  <option value="preventive">
                    Preventive
                  </option>

                  <option value="corrective">
                    Corrective
                  </option>
                </select>
              </label>
            </div>
          </div>

          {loading && (
            <div className="dashboard-panel-state">
              Loading maintenance records...
            </div>
          )}

          {!loading &&
            !error &&
            records.length === 0 && (
              <div className="maintenance-empty">
                <Wrench size={23} />

                <strong>No maintenance records yet</strong>

                <span>
                  Maintenance interventions will appear
                  here once they have been recorded.
                </span>
              </div>
            )}

          {!loading &&
            !error &&
            records.length > 0 &&
            filteredRecords.length === 0 && (
              <div className="maintenance-empty">
                <Search size={23} />

                <strong>No matching records</strong>

                <span>
                  Try another search term or change the
                  filters.
                </span>
              </div>
            )}

          {!loading &&
            !error &&
            filteredRecords.length > 0 && (
              <div className="maintenance-record-list">
                {filteredRecords.map((record, index) => {
                  const machine = machinesById.get(
                    record.machine_id,
                  )

                  const isSelected =
                    selectedRecord?.id === record.id

                  return (
                    <motion.button
                      key={record.id}
                      type="button"
                      className={
                        isSelected
                          ? 'maintenance-record-item maintenance-record-item-selected'
                          : 'maintenance-record-item'
                      }
                      onClick={() => {
                        setSelectedRecordId((current) =>
                            current === record.id ? null : record.id,
                        )
                        setActionError(null)
                        setActionNotice(null)
                      }}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        delay: Math.min(index * 0.025, 0.2),
                      }}
                    >
                      <div className="maintenance-record-top">
                        <span
                          className={getTypeClass(
                            record.maintenance_type,
                          )}
                        >
                          {formatLabel(
                            record.maintenance_type,
                          )}
                        </span>

                        <span
                          className={getStatusClass(
                            record.status,
                          )}
                        >
                          {formatLabel(record.status)}
                        </span>
                      </div>

                      <strong className="maintenance-record-title">
                        {record.description}
                      </strong>

                      <div className="maintenance-record-context">
                        <span>
                          {machine?.name ??
                            `Machine #${record.machine_id}`}
                        </span>

                        <span>
                          {machine?.code ??
                            `Asset ID ${record.machine_id}`}
                        </span>
                      </div>

                      <div className="maintenance-record-footer">
                        <span>
                          <CalendarClock size={13} />
                          {formatMaintenanceDate(
                            record.performed_at ??
                              record.created_at,
                          )}
                        </span>

                        <span>
                          Record #{record.id}
                        </span>
                      </div>
                    </motion.button>
                  )
                })}
              </div>
            )}
        </div>

        <aside className="maintenance-detail-panel">
          {!selectedRecord ? (
            <div className="maintenance-empty maintenance-detail-empty">
              <Wrench size={23} />

              <strong>Select a maintenance record</strong>

              <span>
                Choose a record from the register to inspect
                its machine context and intervention details.
              </span>
            </div>
          ) : (
            <motion.div
              key={selectedRecord.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="maintenance-panel-header">
                <div>
                    <span className="panel-eyebrow">
                        Maintenance details
                    </span>

                    <h2>Record #{selectedRecord.id}</h2>
                </div>

                <button
                    type="button"
                    className="maintenance-clear-selection"
                    onClick={() => {
                        setSelectedRecordId(null)
                        setActionError(null)
                        setActionNotice(null)
                    }}
                    aria-label="Clear selected maintenance record"
                >
                    Clear selection
                </button>
              </div>

              <div className="maintenance-detail-badges">
                <span
                  className={getTypeClass(
                    selectedRecord.maintenance_type,
                  )}
                >
                  {formatLabel(
                    selectedRecord.maintenance_type,
                  )}
                </span>

                <span
                  className={getStatusClass(
                    selectedRecord.status,
                  )}
                >
                  {formatLabel(selectedRecord.status)}
                </span>
              </div>

              <h3 className="maintenance-detail-title">
                {selectedRecord.description}
              </h3>

              <div className="maintenance-detail-section">
                <span className="panel-eyebrow">
                  Machine context
                </span>

                <div className="maintenance-detail-row">
                  <span>Machine</span>

                  <strong>
                    {selectedMachine?.name ??
                      'Machine unavailable'}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Asset code</span>

                  <strong>
                    {selectedMachine?.code ?? '—'}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Machine status</span>

                  <strong>
                    {selectedMachine
                      ? formatLabel(selectedMachine.status)
                      : '—'}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Location</span>

                  <strong>
                    {selectedMachine?.location ??
                      'Not specified'}
                  </strong>
                </div>
              </div>

              <div className="maintenance-detail-section">
                <span className="panel-eyebrow">
                  Intervention record
                </span>

                <div className="maintenance-detail-row">
                  <span>Record ID</span>

                  <strong>
                    #{selectedRecord.id}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Performed at</span>

                  <strong>
                    {formatMaintenanceDate(
                      selectedRecord.performed_at,
                    )}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Created at</span>

                  <strong>
                    {formatMaintenanceDate(
                      selectedRecord.created_at,
                    )}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Linked alert</span>

                  <strong>
                    {selectedRecord.alert_id !== null
                      ? `Alert #${selectedRecord.alert_id}`
                      : 'Not linked'}
                  </strong>
                </div>

                <div className="maintenance-detail-row">
                  <span>Performed by</span>

                  <strong>
                    {selectedRecord.performed_by_user_id !== null
                      ? `User #${selectedRecord.performed_by_user_id}`
                      : 'Not assigned'}
                  </strong>
                </div>
              </div>
              <div className="maintenance-detail-section">
                <span className="panel-eyebrow">
                  Machine effectiveness
                </span>

                <p className="maintenance-effectiveness-context">
                  Performance across the selected machine's
                  recorded maintenance history.
                </p>

                {loadingEffectiveness && (
                  <div className="dashboard-panel-state">
                    Loading effectiveness metrics...
                  </div>
                )}

                {!loadingEffectiveness &&
                  effectivenessError && (
                    <div
                      className="dashboard-data-error"
                      role="alert"
                    >
                      <Activity size={16} />

                      <div>
                        <strong>
                          Analytics unavailable
                        </strong>

                        <span>
                          {effectivenessError}
                        </span>
                      </div>
                    </div>
                  )}

                {!loadingEffectiveness &&
                  !effectivenessError &&
                  maintenanceEffectiveness && (
                    <div className="maintenance-effectiveness-grid">
                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Preventive share
                        </span>

                        <strong>
                          {formatMaintenanceRate(
                            maintenanceEffectiveness.preventive_share,
                          )}
                        </strong>
                      </div>

                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Completion rate
                        </span>

                        <strong>
                          {formatMaintenanceRate(
                            maintenanceEffectiveness.completion_rate,
                          )}
                        </strong>
                      </div>

                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Verification rate
                        </span>

                        <strong>
                          {formatMaintenanceRate(
                            maintenanceEffectiveness.verification_rate,
                          )}
                        </strong>
                      </div>

                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Alert linkage
                        </span>

                        <strong>
                          {formatMaintenanceRate(
                            maintenanceEffectiveness.alert_link_rate,
                          )}
                        </strong>
                      </div>

                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Alert response rate
                        </span>

                        <strong>
                          {formatMaintenanceRate(
                            maintenanceEffectiveness.response_rate,
                          )}
                        </strong>
                      </div>

                      <div className="maintenance-effectiveness-metric">
                        <span>
                          Median response time
                        </span>

                        <strong>
                          {formatResponseDuration(
                            maintenanceEffectiveness.median_response_time_seconds,
                          )}
                        </strong>
                      </div>
                    </div>
                  )}
              </div>

              <div className="maintenance-action-panel">
                <span className="panel-eyebrow">
                  Maintenance actions
                </span>

                {!canUpdateMaintenance ? (
                  <p className="maintenance-action-description">
                    Your account has read-only access to maintenance
                    records.
                  </p>
                ) : statusActions.length === 0 ? (
                  <p className="maintenance-action-description">
                    This intervention has no further status actions.
                  </p>
                ) : (
                  <>
                    <p className="maintenance-action-description">
                      Update the intervention status as work progresses.
                    </p>

                    <div className="maintenance-action-row">
                      {statusActions.map((action) => (
                        <button
                          key={action.status}
                          type="button"
                          className={
                            action.status === 'cancelled'
                              ? 'maintenance-action-button maintenance-action-button-danger'
                              : 'maintenance-action-button'
                          }
                          disabled={updatingRecordId !== null}
                          onClick={() =>
                            void handleStatusChange(action.status)
                          }
                        >
                          {updatingRecordId === selectedRecord.id
                            ? 'Saving...'
                            : action.label}
                        </button>
                      ))}
                    </div>
                  </>
                )}

                {actionError && (
                  <p
                    className="maintenance-action-feedback maintenance-action-feedback-error"
                    role="alert"
                  >
                    {actionError}
                  </p>
                )}

                {actionNotice && (
                  <p
                    className="maintenance-action-feedback maintenance-action-feedback-success"
                    role="status"
                  >
                    {actionNotice}
                  </p>
                )}
              </div>

              <div className="maintenance-detail-footer">
                {selectedRecord.status === 'completed' ||
                selectedRecord.status === 'verified' ? (
                  <CheckCircle2 size={17} />
                ) : (
                  <UserRound size={17} />
                )}

                <span>
                  {selectedRecord.status === 'verified'
                    ? 'This intervention is marked as verified.'
                    : selectedRecord.status === 'completed'
                      ? 'This intervention is marked as completed.'
                      : selectedRecord.status === 'cancelled'
                        ? 'This intervention was cancelled.'
                        : 'This intervention is not yet finalized.'}
                </span>
              </div>
            </motion.div>
          )}
        </aside>
      </section>

      {!loading && !error && records.length > 0 && (
        <p className="maintenance-page-footnote">
          Completed and verified counts reflect the
          recorded status of each intervention. No
          unrecorded maintenance state is inferred.
          Finished records: {finishedCount}.
        </p>
      )}
    </div>
  )
}
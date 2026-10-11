const ALERTS_UPDATED_EVENT =
  'factorypulse:alerts-updated'

type AlertsUpdatedDetail = {
  openAlertCount?: number
}

export function notifyAlertsUpdated(
  openAlertCount?: number,
): void {
  window.dispatchEvent(
    new CustomEvent<AlertsUpdatedDetail>(
      ALERTS_UPDATED_EVENT,
      {
        detail: { openAlertCount },
      },
    ),
  )
}

export function subscribeToAlertsUpdated(
  listener: (openAlertCount?: number) => void,
): () => void {
  const handler = (event: Event) => {
    const detail = (
      event as CustomEvent<AlertsUpdatedDetail>
    ).detail

    listener(detail?.openAlertCount)
  }

  window.addEventListener(
    ALERTS_UPDATED_EVENT,
    handler,
  )

  return () => {
    window.removeEventListener(
      ALERTS_UPDATED_EVENT,
      handler,
    )
  }
}
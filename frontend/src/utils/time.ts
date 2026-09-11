export function formatRelativeTime(
  timestampValue: string,
): string {
  const timestamp =
    new Date(timestampValue).getTime()

  if (Number.isNaN(timestamp)) {
    return 'Unknown time'
  }

  const elapsedMilliseconds =
    Date.now() - timestamp

  const elapsedMinutes =
    Math.max(
      0,
      Math.floor(
        elapsedMilliseconds / 60000,
      ),
    )

  if (elapsedMinutes < 1) {
    return 'Just now'
  }

  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} min ago`
  }

  const elapsedHours =
    Math.floor(elapsedMinutes / 60)

  if (elapsedHours < 24) {
    return `${elapsedHours}h ago`
  }

  const elapsedDays =
    Math.floor(elapsedHours / 24)

  return `${elapsedDays}d ago`
}

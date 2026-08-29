type AuthSessionListener = () => void

const sessionInvalidatedListeners =
  new Set<AuthSessionListener>()

export function subscribeToSessionInvalidation(
  listener: AuthSessionListener,
): () => void {
  sessionInvalidatedListeners.add(listener)

  return () => {
    sessionInvalidatedListeners.delete(listener)
  }
}

export function notifySessionInvalidated(): void {
  for (const listener of sessionInvalidatedListeners) {
    listener()
  }
}
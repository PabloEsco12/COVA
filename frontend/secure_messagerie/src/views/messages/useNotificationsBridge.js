export function useNotificationsBridge({ notificationDedupSet, handleIncomingNotificationPayload }) {
  function makeNotificationFingerprint(payload) {
    if (!payload || typeof payload !== 'object') return `generic:${Date.now()}`
    const parts = [
      payload.type || 'generic',
      payload.message_id ||
        payload.id ||
        payload.notification_id ||
        payload.conversation_id ||
        payload.preview ||
        payload.title ||
        payload.sender ||
        payload.timestamp ||
        payload.created_at ||
        JSON.stringify(payload).slice(0, 60),
    ]
    return parts.join(':')
  }

  function processNotificationPayload(payload, origin = 'stream') {
    if (!payload || typeof payload !== 'object') return
    const key = makeNotificationFingerprint(payload)
    if (notificationDedupSet.has(key)) return
    if (notificationDedupSet.size > 512) {
      notificationDedupSet.clear()
    }
    notificationDedupSet.add(key)
    handleIncomingNotificationPayload?.(payload, origin)
  }

  return {
    makeNotificationFingerprint,
    processNotificationPayload,
  }
}

import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { buildWsUrl } from '@/utils/realtime'

export function useNotificationsStream(options = {}) {
  const socket = ref(null)
  const connected = ref(false)
  const reconnectTimer = ref(null)
  const backoffStep = ref(0)
  const baseDelay = 1500
  const maxDelay = 20000
  const token = ref(options.token || null)

  const handlers = {
    onNotification: options.onNotification || (() => {}),
    onStatus: options.onStatus || (() => {}),
  }

  function clearReconnect() {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
  }

  function scheduleReconnect() {
    clearReconnect()
    const delay = Math.min(maxDelay, baseDelay * Math.pow(2, backoffStep.value))
    reconnectTimer.value = setTimeout(connect, delay)
    backoffStep.value = Math.min(backoffStep.value + 1, 8)
  }

  function makeUrl() {
    if (!token.value) return null
    return buildWsUrl('notifications', { token: token.value })
  }

  function connect() {
    const url = makeUrl()
    if (!url) {
      disconnect()
      return
    }
    disconnect(false)
    const ws = new WebSocket(url)
    socket.value = ws
    ws.onopen = () => {
      connected.value = true
      backoffStep.value = 0
      handlers.onStatus(true)
    }
    ws.onclose = () => {
      connected.value = false
      handlers.onStatus(false)
      scheduleReconnect()
    }
    ws.onerror = () => {
      connected.value = false
    }
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.event === 'notification') {
          handlers.onNotification(data.payload || {})
        }
      } catch (err) {
        if (import.meta.env.DEV) {
          console.warn('[notifications] unable to parse event', err)
        }
      }
    }
  }

  function disconnect(clearTimer = true) {
    if (clearTimer) clearReconnect()
    if (socket.value) {
      try {
        socket.value.close()
      } catch {
        // ignore
      }
      socket.value = null
    }
    connected.value = false
    handlers.onStatus(false)
  }

  function updateToken(nextToken) {
    const trimmed = nextToken || null
    if (token.value === trimmed) return
    token.value = trimmed
  }

  watch(
    token,
    (value) => {
      if (value) connect()
      else disconnect()
    },
    { immediate: true },
  )

  onMounted(() => {
    if (token.value) connect()
  })

  onBeforeUnmount(() => {
    disconnect()
  })

  return {
    connected,
    connect,
    disconnect,
    updateToken,
  }
}

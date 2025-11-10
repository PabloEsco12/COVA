import { backendBase } from '@/utils/api'

function buildWsUrl(path) {
  const base = backendBase.replace(/\/+$/, '')
  const url = new URL(`${base}/api${path}`, base)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url
}

export function createConversationSocket(conversationId, { token, onEvent, onOpen, onError, onClose } = {}) {
  const url = buildWsUrl(`/ws/conversations/${conversationId}`)
  if (token) {
    url.searchParams.set('token', token)
  }

  const socket = new WebSocket(url.toString())

  if (onOpen) {
    socket.addEventListener('open', onOpen)
  }
  if (onClose) {
    socket.addEventListener('close', onClose)
  }
  if (onError) {
    socket.addEventListener('error', onError)
  }
  if (onEvent) {
    socket.addEventListener('message', (event) => {
      try {
        const payload = JSON.parse(event.data)
        onEvent(payload, event)
      } catch (err) {
        console.warn('Unable to parse realtime payload', err)
      }
    })
  }

  return socket
}

function normalizeBaseUrl(baseUrl) {
  return baseUrl.replace(/\/+$/, '')
}

function buildWebsocketUrl(baseUrl, conversationId, token) {
  const url = new URL(`/ws/conversations/${conversationId}`, normalizeBaseUrl(baseUrl))
  if (url.protocol === 'http:') url.protocol = 'ws:'
  if (url.protocol === 'https:') url.protocol = 'wss:'
  if (token) url.searchParams.set('token', token)
  return url.toString()
}

function ensureListenersMap(listeners, event) {
  if (!listeners.has(event)) {
    listeners.set(event, new Set())
  }
  return listeners.get(event)
}

export class ConversationSocket {
  constructor({ baseUrl, tokenProvider }) {
    this.baseUrl = normalizeBaseUrl(baseUrl)
    this.tokenProvider = tokenProvider
    this.websocket = null
    this.conversationId = null
    this.listeners = new Map()
    this._ackCleanup = null
    this._ackResolve = null
    this._ackReject = null
    this._wsListeners = null
  }

  async connect(conversationId) {
    await this.disconnect()
    this.conversationId = conversationId
    const token =
      typeof this.tokenProvider === 'function' ? await this.tokenProvider() : this.tokenProvider

    if (!token) {
      throw new Error('Missing access token for realtime connection')
    }

    const wsUrl = buildWebsocketUrl(this.baseUrl, conversationId, token)
    const ws = new WebSocket(wsUrl)
    this.websocket = ws
    this._setupWebsocket(ws)

    return new Promise((resolve, reject) => {
      this._ackResolve = resolve
      this._ackReject = reject
      const handleAck = payload => {
        cleanup()
        resolve(payload)
      }
      const handleError = error => {
        cleanup()
        reject(error instanceof Error ? error : new Error('WebSocket connection error'))
      }
      const handleClose = () => {
        cleanup()
        reject(new Error('WebSocket closed before acknowledgement'))
      }
      const cleanup = () => {
        this.off('ack', handleAck)
        this.off('error', handleError)
        this.off('close', handleClose)
        this._ackCleanup = null
        this._ackResolve = null
        this._ackReject = null
      }
      this._ackCleanup = cleanup
      this.on('ack', handleAck)
      this.on('error', handleError)
      this.on('close', handleClose)
    })
  }

  async disconnect() {
    if (this._ackReject) {
      try {
        this._ackReject(new Error('Realtime connection cancelled'))
      } catch {}
    }
    if (this._ackCleanup) {
      this._ackCleanup()
      this._ackCleanup = null
    }
    this._ackResolve = null
    this._ackReject = null

    if (this.websocket) {
      if (this._wsListeners) {
        const { handleOpen, handleMessage, handleError, handleClose } = this._wsListeners
        if (handleOpen) this.websocket.removeEventListener('open', handleOpen)
        if (handleMessage) this.websocket.removeEventListener('message', handleMessage)
        if (handleError) this.websocket.removeEventListener('error', handleError)
        if (handleClose) this.websocket.removeEventListener('close', handleClose)
        this._wsListeners = null
      }
      try {
        this.websocket.close(1000, 'Switching conversation')
      } catch {}
      this.websocket = null
    }
    this.conversationId = null
  }

  on(event, handler) {
    ensureListenersMap(this.listeners, event).add(handler)
  }

  off(event, handler) {
    const existing = this.listeners.get(event)
    if (!existing) return
    existing.delete(handler)
    if (existing.size === 0) {
      this.listeners.delete(event)
    }
  }

  _emit(event, payload) {
    const handlers = this.listeners.get(event)
    if (!handlers) return
    for (const handler of handlers) {
      try {
        handler(payload)
      } catch (error) {
        console.error('Realtime handler error', error)
      }
    }
  }

  _handleMessage(event) {
    let data = null
    try {
      data = typeof event.data === 'string' ? JSON.parse(event.data) : null
    } catch (error) {
      console.warn('Unable to parse realtime payload', error)
    }

    if (!data || typeof data !== 'object') {
      return null
    }

    this._emit('event', data)

    switch (data.type) {
      case 'connection.ack':
        this._emit('ack', data)
        break
      case 'message.created':
        this._emit('message', data)
        break
      case 'message.read':
        this._emit('read', data)
        break
      default:
        break
    }

    return data
  }

  _setupWebsocket(ws) {
    const handleOpen = () => {
      this._emit('open', { conversationId: this.conversationId })
    }
    const handleMessage = event => {
      this._handleMessage(event)
    }
    const handleError = error => {
      this._emit('error', error)
    }
    const handleClose = () => {
      this._emit('close')
    }

    this._wsListeners = { handleOpen, handleMessage, handleError, handleClose }
    ws.addEventListener('open', handleOpen)
    ws.addEventListener('message', handleMessage)
    ws.addEventListener('error', handleError)
    ws.addEventListener('close', handleClose)
  }
}

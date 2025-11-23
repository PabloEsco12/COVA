import { io } from 'socket.io-client'

export class CovaSocket {
  constructor({ baseUrl, tokenProvider }) {
    this.baseUrl = baseUrl
    this.tokenProvider = tokenProvider
    this.socket = null
  }

  async connect() {
    if (this.socket && this.socket.connected) return
    const token = typeof this.tokenProvider === 'function'
      ? await this.tokenProvider()
      : this.tokenProvider

    this.socket = io(this.baseUrl, {
      transports: ['websocket', 'polling'],
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      withCredentials: true,
      timeout: 10000,
      auth: { token },
    })

    return new Promise((resolve, reject) => {
      if (!this.socket) {
        reject(new Error('socket not created'))
        return
      }
      this.socket.once('connect', () => resolve())
      this.socket.once('connect_error', error => reject(error))
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  on(event, handler) {
    this.socket?.on(event, handler)
  }

  off(event, handler) {
    this.socket?.off(event, handler)
  }

  joinConversation(convId) {
    this.socket?.emit('join_conversation', { conv_id: convId })
  }

  leaveConversation(convId) {
    this.socket?.emit('leave_conversation', { conv_id: convId })
  }

  typing(convId, isTyping) {
    this.socket?.emit('typing', { conv_id: convId, is_typing: isTyping })
  }

  markRead(convId, messageIds = []) {
    this.socket?.emit('mark_read', { conv_id: convId, message_ids: messageIds })
  }
}

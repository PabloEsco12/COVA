// Wrapper socket.io pour les interactions temps reel (typing, read, join)
import { io } from 'socket.io-client'

export class CovaSocket {
  // Gere la creation/diffusion d'une socket authentifiee vers l'API temps reel
  constructor({ baseUrl, tokenProvider }) {
    this.baseUrl = baseUrl
    this.tokenProvider = tokenProvider
    this.socket = null
  }

  async connect() {
    // Ouvre une connexion socket.io en recuperant le token de maniere paresseuse
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
    // Ferme proprement la socket pour liberer les ressources
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  on(event, handler) {
    // Attache un listener d'evenement socket.io
    this.socket?.on(event, handler)
  }

  off(event, handler) {
    // Detache un listener
    this.socket?.off(event, handler)
  }

  joinConversation(convId) {
    // Rejoint une room de conversation pour recevoir les evenements associes
    this.socket?.emit('join_conversation', { conv_id: convId })
  }

  leaveConversation(convId) {
    // Quitte la room conversation associee
    this.socket?.emit('leave_conversation', { conv_id: convId })
  }

  typing(convId, isTyping) {
    // Informe les autres membres de l'etat de saisie
    this.socket?.emit('typing', { conv_id: convId, is_typing: isTyping })
  }

  markRead(convId, messageIds = []) {
    // Notifie le serveur des messages lus afin de synchroniser les badges/recepteurs
    this.socket?.emit('mark_read', { conv_id: convId, message_ids: messageIds })
  }
}

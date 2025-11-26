// src/services/messages.js
// Service messages : helpers pour normaliser payloads et appels REST conversationnels
import { api } from '@/utils/api'

// --- Helpers de normalisation ---
function asArray(data) {
  // S'assure que la reponse est un tableau exploitable
  return Array.isArray(data) ? data : []
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function coerceUuid(value) {
  // Valide et nettoie un identifiant transmis par l'UI
  if (!value) return null
  const candidate = String(value).trim()
  return UUID_PATTERN.test(candidate) ? candidate : null
}

function normalizeAttachmentRefs(raw) {
  // Convertit diverses representations (string/objet) en liste upload_token standard
  if (!raw) return []
  const list = Array.isArray(raw) ? raw : [raw]
  return list
    .map((entry) => {
      if (!entry) return null
      if (typeof entry === 'string') {
        return { upload_token: entry }
      }
      if (typeof entry === 'object' && entry.upload_token) {
        return { upload_token: entry.upload_token }
      }
      return null
    })
    .filter(Boolean)
}

function normalizeMessagePayload(input = {}) {
  // Construit le payload message en acceptant string, objet UI ou formes legacy
  const payload = typeof input === 'string' ? { content: input } : { ...input }
  const body = {
    content: typeof payload.content === 'string' ? payload.content : '',
    message_type: payload.message_type || payload.type || 'text',
  }
  const attachments = normalizeAttachmentRefs(payload.attachments || payload.attachment_tokens)
  if (attachments.length) {
    body.attachments = attachments
  }
  const replyId = coerceUuid(payload.reply_to_message_id || payload.reply_to)
  if (replyId) {
    body.reply_to_message_id = replyId
  }
  const forwardId = coerceUuid(payload.forward_message_id || payload.forward_from)
  if (forwardId) {
    body.forward_message_id = forwardId
  }
  return body
}

function normalizeContentPayload(value) {
  // Ramene les mises a jour de contenu a une forme minimale { content }
  if (typeof value === 'string') {
    return { content: value }
  }
  if (value && typeof value === 'object' && typeof value.content === 'string') {
    return { content: value.content }
  }
  return { content: '' }
}

// --- Appels API messages/conversations ---
export async function listConversations(params = {}) {
  // Liste les conversations avec les params utilises par l'UI (pagination/filtre)
  const { data } = await api.get('/conversations', { params })
  return asArray(data)
}

export async function createConversation(payload) {
  const { data } = await api.post('/conversations', payload)
  return data
}

export async function fetchConversations(params = {}) {
  return listConversations(params)
}

export async function getConversationMessages(conversationId, params = {}) {
  // Recupere les messages d'une conversation en encodant l'identifiant
  const cid = encodeURIComponent(conversationId)
  const { data } = await api.get(`/conversations/${cid}/messages`, { params })
  return asArray(data)
}

export async function fetchMessages(conversationId, params = {}) {
  return getConversationMessages(conversationId, params)
}

export async function sendMessage(conversationId, payload) {
  // Normalise et envoie un message (texte/fichier/reponse/forward)
  const cid = encodeURIComponent(conversationId)
  const body = normalizeMessagePayload(payload)
  const { data } = await api.post(`/conversations/${cid}/messages`, body)
  return data
}

export async function sendConversationMessage(conversationId, payload) {
  return sendMessage(conversationId, payload)
}

export async function updateMessage(conversationId, messageId, payload) {
  // Update idempotente du contenu d'un message existant
  const cid = encodeURIComponent(conversationId)
  const mid = encodeURIComponent(messageId)
  const body = normalizeContentPayload(payload)
  const { data } = await api.put(`/conversations/${cid}/messages/${mid}`, body)
  return data
}

export async function editConversationMessage(conversationId, messageId, payload) {
  return updateMessage(conversationId, messageId, payload)
}

export async function deleteMessage(conversationId, messageId) {
  // Supprime un message et renvoie true pour faciliter l'appelant
  const cid = encodeURIComponent(conversationId)
  const mid = encodeURIComponent(messageId)
  await api.delete(`/conversations/${cid}/messages/${mid}`)
  return true
}

export async function deleteConversationMessage(conversationId, messageId) {
  return deleteMessage(conversationId, messageId)
}

export async function markMessagesRead(conversationId, messageIds = []) {
  // Notifie le backend que certains messages sont lus, en dedoublonnant les IDs
  const cid = encodeURIComponent(conversationId)
  const uniqueIds = Array.isArray(messageIds)
    ? Array.from(new Set(messageIds.map((id) => coerceUuid(id)).filter(Boolean)))
    : []
  const payload = uniqueIds.length ? { message_ids: uniqueIds } : {}
  await api.post(`/conversations/${cid}/read`, payload)
  return true
}

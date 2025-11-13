// src/services/messages.js
import { api } from '@/utils/api'

/**
 * Normalise une réponse censée être un tableau.
 * @param {*} data
 * @returns {Array<any>}
 */
function asArray(data) {
  return Array.isArray(data) ? data : []
}

/** ****************************************************************************
 * CONVERSATIONS
 **************************************************************************** */

/**
 * Liste les conversations.
 * @param {Object} [params]
 * @returns {Promise<Array<any>>}
 */
export async function listConversations(params = {}) {
  const { data } = await api.get('/conversations/', { params })
  return asArray(data)
}

/**
 * Crée une conversation.
 * @param {Object} payload
 *  - selon ton backend: { titre } ou { title }, { participants|participant_ids }, { type|is_group }
 * @returns {Promise<any>}
 */
export async function createConversation(payload) {
  const { data } = await api.post('/conversations/', payload)
  return data
}

/** Aliases “fetch*” pour compat compat */
export async function fetchConversations(params = {}) {
  return listConversations(params)
}

/** ****************************************************************************
 * MESSAGES
 **************************************************************************** */

/**
 * Récupère les messages d’une conversation.
 * @param {string|number} conversationId
 * @param {Object} [params] - ex: { limit, before, after }
 * @returns {Promise<Array<any>>}
 */
export async function getConversationMessages(conversationId, params = {}) {
  const cid = encodeURIComponent(conversationId)
  const { data } = await api.get(`/conversations/${cid}/messages/`, { params })
  return asArray(data)
}

/** Alias “fetchMessages” */
export async function fetchMessages(conversationId, params = {}) {
  return getConversationMessages(conversationId, params)
}

/**
 * Envoie un message dans une conversation.
 * @param {string|number} conversationId
 * @param {string} content - attendu par ton API: `contenu_chiffre`
 * @returns {Promise<any>}
 */
export async function sendMessage(conversationId, content) {
  const cid = encodeURIComponent(conversationId)
  const { data } = await api.post(`/conversations/${cid}/messages/`, {
    contenu_chiffre: content,
  })
  return data
}

/** Alias “sendConversationMessage” */
export async function sendConversationMessage(conversationId, content) {
  return sendMessage(conversationId, content)
}

/**
 * Met à jour un message existant.
 * @param {string|number} conversationId
 * @param {string|number} messageId
 * @param {string} content
 * @returns {Promise<any>}
 */
export async function updateMessage(conversationId, messageId, content) {
  const cid = encodeURIComponent(conversationId)
  const mid = encodeURIComponent(messageId)
  const { data } = await api.put(`/conversations/${cid}/messages/${mid}`, {
    contenu_chiffre: content,
  })
  return data
}

/** Alias “editConversationMessage” */
export async function editConversationMessage(conversationId, messageId, content) {
  return updateMessage(conversationId, messageId, content)
}

/**
 * Supprime un message.
 * @param {string|number} conversationId
 * @param {string|number} messageId
 * @returns {Promise<boolean>}
 */
export async function deleteMessage(conversationId, messageId) {
  const cid = encodeURIComponent(conversationId)
  const mid = encodeURIComponent(messageId)
  await api.delete(`/conversations/${cid}/messages/${mid}`)
  return true
}

/** Alias “deleteConversationMessage” */
export async function deleteConversationMessage(conversationId, messageId) {
  return deleteMessage(conversationId, messageId)
}

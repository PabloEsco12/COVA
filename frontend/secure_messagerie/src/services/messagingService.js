import { api } from '@/utils/api'

export async function listContacts(status = 'accepted') {
  const res = await api.get(`/contacts?statut=${encodeURIComponent(status)}`)
  return res.data
}

export async function listConversations() {
  const res = await api.get(`/conversations/`)
  return res.data
}

export async function getConversation(convId) {
  const res = await api.get(`/conversations/${convId}`)
  return res.data
}

export async function getConversationMessages(convId) {
  const res = await api.get(`/conversations/${convId}/messages/`)
  return res.data
}

export async function createConversationRoom(payload) {
  const res = await api.post(`/conversations/`, payload)
  return res.data
}

export async function updateConversationTitle(convId, titre) {
  const res = await api.patch(`/conversations/${convId}/title`, { titre })
  return res.data
}

export async function leaveConversationRoom(convId) {
  const res = await api.post(`/conversations/${convId}/leave`, {})
  return res.data
}

export async function deleteConversationRoom(convId) {
  const res = await api.delete(`/conversations/${convId}`)
  return res.data
}

export async function getUnreadSummary() {
  const res = await api.get(`/messages/unread_summary`)
  return res.data
}

export async function sendConversationMessage(convId, formData) {
  const res = await api.post(`/conversations/${convId}/messages/`, formData)
  return res.data
}

export async function toggleMessageReaction(messageId, emoji) {
  const res = await api.post(`/messages/${messageId}/reactions`, { emoji })
  return res.data
}

export async function listConversationCalls(convId) {
  const res = await api.get(`/conversations/${convId}/calls`)
  return res.data
}

export async function createConversationCall(convId, payload) {
  const res = await api.post(`/conversations/${convId}/calls`, payload)
  return res.data
}

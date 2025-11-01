import { api } from '@/utils/api'

export async function listContacts() {
  const res = await api.get('/contacts/')
  return res.data
}

export async function createContact(payload) {
  const res = await api.post('/contacts/', payload)
  return res.data
}

export async function deleteContact(contactUserId) {
  await api.delete(`/contacts/${contactUserId}`)
}

export async function listConversations() {
  const res = await api.get('/conversations/')
  return res.data
}

export async function getConversation(convId) {
  const res = await api.get(`/conversations/${convId}`)
  return res.data
}

export async function listConversationMessages(convId, params = {}) {
  const res = await api.get(`/conversations/${convId}/messages`, { params })
  return res.data
}

export async function createConversation(payload) {
  const res = await api.post('/conversations/', payload)
  return res.data
}

export async function sendConversationMessage(convId, content) {
  const res = await api.post(`/conversations/${convId}/messages`, content)
  return res.data
}

export async function markConversationMessagesRead(convId, messageIds = []) {
  if (!Array.isArray(messageIds) || messageIds.length === 0) return
  await api.post(`/conversations/${convId}/read`, { message_ids: messageIds })
}

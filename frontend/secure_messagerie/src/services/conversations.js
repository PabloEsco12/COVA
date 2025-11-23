import { api } from '@/utils/api'

const CONVERSATIONS_BASE = '/conversations'

export async function fetchConversations() {
  const { data } = await api.get(CONVERSATIONS_BASE)
  return data
}

export async function createConversation({ title, participantIds = [], type = 'direct' }) {
  const { data } = await api.post(CONVERSATIONS_BASE, {
    title: title || null,
    participant_ids: participantIds,
    type,
  })
  return data
}

export async function fetchMessages(conversationId, { limit } = {}) {
  const params = limit ? { limit } : undefined
  const { data } = await api.get(`${CONVERSATIONS_BASE}/${conversationId}/messages`, { params })
  return data
}

export async function sendMessage(conversationId, { content, messageType = 'text', attachments = [] }) {
  const normalized = Array.isArray(attachments)
    ? attachments.map((item) => ({
        upload_token: item.upload_token || item.uploadToken || item,
      }))
    : []
  const { data } = await api.post(`${CONVERSATIONS_BASE}/${conversationId}/messages`, {
    content,
    message_type: messageType,
    attachments: normalized.filter((item) => typeof item.upload_token === 'string'),
  })
  return data
}

export async function updateConversation(conversationId, payload) {
  const { data } = await api.patch(`${CONVERSATIONS_BASE}/${conversationId}`, payload)
  return data
}

export async function leaveConversation(conversationId) {
  await api.post(`${CONVERSATIONS_BASE}/${conversationId}/leave`)
}

export async function deleteConversation(conversationId) {
  await api.delete(`${CONVERSATIONS_BASE}/${conversationId}`)
}

export async function pinMessage(conversationId, messageId) {
  const { data } = await api.post(`${CONVERSATIONS_BASE}/${conversationId}/messages/${messageId}/pin`)
  return data
}

export async function unpinMessage(conversationId, messageId) {
  const { data } = await api.delete(`${CONVERSATIONS_BASE}/${conversationId}/messages/${messageId}/pin`)
  return data
}

export async function updateMessageReaction(conversationId, messageId, { emoji, action = 'toggle' }) {
  const { data } = await api.post(`${CONVERSATIONS_BASE}/${conversationId}/messages/${messageId}/reactions`, {
    emoji,
    action,
  })
  return data
}

export async function updateConversationMember(conversationId, memberId, payload) {
  const { data } = await api.patch(`${CONVERSATIONS_BASE}/${conversationId}/members/${memberId}`, payload)
  return data
}

export async function listConversationInvites(conversationId) {
  const { data } = await api.get(`${CONVERSATIONS_BASE}/${conversationId}/invites`)
  return data
}

export async function createConversationInvite(conversationId, payload) {
  const { data } = await api.post(`${CONVERSATIONS_BASE}/${conversationId}/invites`, payload)
  return data
}

export async function revokeConversationInvite(conversationId, inviteId) {
  await api.delete(`${CONVERSATIONS_BASE}/${conversationId}/invites/${inviteId}`)
}

export async function acceptConversationInvite(token) {
  const { data } = await api.post(`${CONVERSATIONS_BASE}/invites/${token}/accept`)
  return data
}

export async function uploadAttachment(conversationId, file, { encryption, onUploadProgress } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (encryption) {
    formData.append('encryption', JSON.stringify(encryption))
  }
  const { data } = await api.post(`${CONVERSATIONS_BASE}/${conversationId}/attachments`, formData, {
    // Let Axios set the correct multipart boundary automatically.
    onUploadProgress,
  })
  return data
}

export async function editConversationMessage(conversationId, messageId, { content }) {
  const { data } = await api.patch(`${CONVERSATIONS_BASE}/${conversationId}/messages/${messageId}`, { content })
  return data
}

export async function deleteConversationMessage(conversationId, messageId) {
  const { data } = await api.delete(`${CONVERSATIONS_BASE}/${conversationId}/messages/${messageId}`)
  return data
}

export async function searchConversationMessages(conversationId, { query, limit = 50 } = {}) {
  const params = {
    q: query,
    limit,
  }
  const { data } = await api.get(`${CONVERSATIONS_BASE}/${conversationId}/messages/search`, { params })
  return data
}

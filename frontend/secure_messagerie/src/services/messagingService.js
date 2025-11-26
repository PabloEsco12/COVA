// Service historique de messagerie : wrappers simples des endpoints REST
import { api } from '@/utils/api'

// --- Contacts et conversations ---
export async function listContacts(status = 'accepted') {
  // Liste les contacts selon le statut relationnel attendu par l'UI
  const res = await api.get(`/contacts?statut=${encodeURIComponent(status)}`)
  return res.data
}

export async function listConversations() {
  // Recupere toutes les conversations visibles pour l'utilisateur courant
  const res = await api.get(`/conversations/`)
  return res.data
}

export async function getConversation(convId) {
  // Detail d'une conversation (metadonnees, participants)
  const res = await api.get(`/conversations/${convId}`)
  return res.data
}

export async function getConversationMessages(convId) {
  // Messages d'une conversation (utilise par la vue historique)
  const res = await api.get(`/conversations/${convId}/messages/`)
  return res.data
}

export async function createConversationRoom(payload) {
  // Cree une nouvelle conversation a partir du formulaire UI
  const res = await api.post(`/conversations/`, payload)
  return res.data
}

export async function updateConversationTitle(convId, titre) {
  // Modifie le titre d'une conversation existante
  const res = await api.patch(`/conversations/${convId}/title`, { titre })
  return res.data
}

export async function leaveConversationRoom(convId) {
  // Quitte une conversation; le serveur gere la suppression ou non de l'historique
  const res = await api.post(`/conversations/${convId}/leave`, {})
  return res.data
}

export async function deleteConversationRoom(convId) {
  // Supprime entierement la conversation cote serveur
  const res = await api.delete(`/conversations/${convId}`)
  return res.data
}

// --- Messages et reactions ---
export async function getUnreadSummary() {
  // Resume (compteur) des messages non lus pour les badges UI
  const res = await api.get(`/messages/unread_summary`)
  return res.data
}

export async function sendConversationMessage(convId, formData) {
  // Envoi d'un message avec pieces jointes (FormData)
  const res = await api.post(`/conversations/${convId}/messages/`, formData)
  return res.data
}

export async function toggleMessageReaction(messageId, emoji) {
  // Ajoute ou retire une reaction sur un message
  const res = await api.post(`/messages/${messageId}/reactions`, { emoji })
  return res.data
}

// --- Appels audio/visio ---
export async function listConversationCalls(convId) {
  // Liste les appels lies a une conversation (historique)
  const res = await api.get(`/conversations/${convId}/calls`)
  return res.data
}

export async function createConversationCall(convId, payload) {
  // Cree un nouvel appel (payload: medias, agenda, etc.)
  const res = await api.post(`/conversations/${convId}/calls`, payload)
  return res.data
}

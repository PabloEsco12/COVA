// Service REST contacts : creation, mise a jour, suppression et listing
import { api } from '@/utils/api'

const CONTACTS_BASE = '/contacts'

// --- Endpoints contacts ---
export async function fetchContacts({ status } = {}) {
  // Renvoyer les contacts eventuellement filtres par statut (pending/accepted)
  const params = status ? { status } : undefined
  const { data } = await api.get(CONTACTS_BASE, { params })
  return data
}

export async function createContact({ email, alias }) {
  // Cree un contact avec une adresse cible et un alias optionnel
  const { data } = await api.post(CONTACTS_BASE, {
    email,
    alias: alias || null,
  })
  return data
}

export async function updateContactStatus(contactId, status) {
  // Change l'etat de relation (ex: accepter ou bloquer)
  const { data } = await api.patch(`${CONTACTS_BASE}/${contactId}/status`, {
    status,
  })
  return data
}

export async function updateContactAlias(contactId, alias) {
  // Met a jour le nom affiche pour ce contact
  const { data } = await api.patch(`${CONTACTS_BASE}/${contactId}/alias`, {
    alias: alias || null,
  })
  return data
}

export async function deleteContact(contactId) {
  // Supprime definitivement un contact
  await api.delete(`${CONTACTS_BASE}/${contactId}`)
}

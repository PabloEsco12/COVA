import { api } from '@/utils/api'

const CONTACTS_BASE = '/contacts'

export async function fetchContacts({ status } = {}) {
  const params = status ? { status } : undefined
  const { data } = await api.get(CONTACTS_BASE, { params })
  return data
}

export async function createContact({ email, alias }) {
  const { data } = await api.post(CONTACTS_BASE, {
    email,
    alias: alias || null,
  })
  return data
}

export async function updateContactStatus(contactId, status) {
  const { data } = await api.patch(`${CONTACTS_BASE}/${contactId}/status`, {
    status,
  })
  return data
}

export async function updateContactAlias(contactId, alias) {
  const { data } = await api.patch(`${CONTACTS_BASE}/${contactId}/alias`, {
    alias: alias || null,
  })
  return data
}

export async function deleteContact(contactId) {
  await api.delete(`${CONTACTS_BASE}/${contactId}`)
}

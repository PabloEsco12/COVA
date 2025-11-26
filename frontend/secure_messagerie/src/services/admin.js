// Service d'administration : creation et suppression de comptes par un superadmin
import { api } from '@/utils/api'

export async function createUserAsAdmin(payload) {
  // payload: { email, password, display_name?, role?, confirm_now? }
  const { data } = await api.post('/admin/users', payload)
  return data
}

export async function deleteUserAsAdmin(userId) {
  const { data } = await api.delete(`/admin/users/${userId}`)
  return data
}

export default {
  createUserAsAdmin,
  deleteUserAsAdmin,
}

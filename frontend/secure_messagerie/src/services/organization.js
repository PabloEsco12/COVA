// Service organisation : membres, roles et suggestions
import { api } from '@/utils/api'

// --- Endpoints organisation ---
export async function getOrganizationSummary() {
  // Recupere les informations principales de l'organisation courante
  const { data } = await api.get('/organizations/current')
  return data
}

export async function listOrganizationMembers() {
  // Liste tous les membres de l'organisation (utilise pour la gestion d'equipe)
  const { data } = await api.get('/organizations/current/members')
  return data
}

export async function updateOrganizationMemberRole(membershipId, role) {
  // Met a jour le role d'un membre specifique (admin/user ...)
  const { data } = await api.put(`/organizations/current/members/${membershipId}`, { role })
  return data
}

export async function suggestOrganizationMembers(search = '', limit = 10) {
  // Suggestion auto-complete pour inviter/ajouter des membres
  const params = {}
  if (search) params.q = search
  params.limit = limit
  const { data } = await api.get('/organizations/current/members/suggest', { params })
  return data
}

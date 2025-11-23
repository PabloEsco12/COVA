import { api } from '@/utils/api'

export async function getOrganizationSummary() {
  const { data } = await api.get('/organizations/current')
  return data
}

export async function listOrganizationMembers() {
  const { data } = await api.get('/organizations/current/members')
  return data
}

export async function updateOrganizationMemberRole(membershipId, role) {
  const { data } = await api.put(`/organizations/current/members/${membershipId}`, { role })
  return data
}

export async function suggestOrganizationMembers(search = '', limit = 10) {
  const params = {}
  if (search) params.q = search
  params.limit = limit
  const { data } = await api.get('/organizations/current/members/suggest', { params })
  return data
}

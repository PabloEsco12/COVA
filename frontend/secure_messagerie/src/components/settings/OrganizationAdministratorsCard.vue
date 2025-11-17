<template>
  <div class="card organization-admin-card">
    <div class="card-header bg-white d-flex align-items-center gap-2 flex-wrap">
      <i class="bi bi-building-lock text-primary"></i>
      <strong>Administration de l'organisation</strong>
      <span v-if="organization" class="ms-2 badge bg-light text-dark">
        {{ organization.name }}
      </span>
      <button
        class="btn btn-link btn-sm ms-auto text-decoration-none"
        type="button"
        :disabled="loading || refreshing"
        @click="refresh"
      >
        <span v-if="refreshing" class="spinner-border spinner-border-sm me-1" />
        Actualiser
      </button>
    </div>
    <div class="card-body">
      <div v-if="loading && !organization" class="text-center py-5">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <p class="text-muted mb-0">Chargement des membres...</p>
      </div>

      <div v-else>
        <div v-if="error" class="alert alert-warning d-flex align-items-center gap-2">
          <i class="bi bi-exclamation-triangle"></i>
          <span class="flex-grow-1">{{ error }}</span>
          <button class="btn btn-sm btn-outline-primary" type="button" :disabled="refreshing" @click="refresh">
            Réessayer
          </button>
        </div>

        <template v-else>
          <div class="d-flex flex-wrap align-items-center gap-3 summary-line mb-4">
            <div>
              <div class="text-muted small">Rôle actuel</div>
              <span class="badge" :class="roleBadgeClass">
                {{ roleLabel(organization.membership.role) }}
              </span>
            </div>
            <div>
              <div class="text-muted small">Utilisateurs</div>
              <strong>{{ organization.member_count }}</strong>
            </div>
            <div>
              <div class="text-muted small">Administrateurs</div>
              <strong>{{ organization.admin_count }}</strong>
            </div>
          </div>

          <div v-if="!isAdmin" class="alert alert-info mb-0">
            Vous êtes membre de l'organisation <strong>{{ organization.name }}</strong> avec un rôle
            «&nbsp;{{ roleLabel(organization.membership.role) }}&nbsp;». Les paramètres d'administration ne sont
            visibles que par les administrateurs.
          </div>

          <div v-else>
            <div v-if="members.length === 0" class="text-muted small">Aucun membre trouvé.</div>

            <div v-else class="table-responsive">
              <table class="table table-sm align-middle">
                <thead>
                  <tr>
                    <th>Utilisateur</th>
                    <th>Rôle</th>
                    <th class="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="member in members" :key="member.membership_id">
                    <td>
                      <div class="fw-semibold">{{ member.display_name || member.email }}</div>
                      <div class="text-muted small">{{ member.email }}</div>
                    </td>
                    <td>
                      <span class="badge" :class="roleBadgeClassFor(member.role)">
                        {{ roleLabel(member.role) }}
                      </span>
                    </td>
                    <td class="text-end">
                      <div v-if="member.role === 'owner'" class="text-muted small">
                        Propriétaire (non modifiable)
                      </div>
                      <div v-else>
                        <div class="d-flex gap-2 align-items-center justify-content-end flex-wrap">
                          <select
                            v-model="member.pendingRole"
                            class="form-select form-select-sm w-auto"
                            :disabled="member.busy || !canManageAdmins"
                          >
                            <option
                              v-for="option in roleOptions"
                              :key="`${member.membership_id}-${option.value}`"
                              :value="option.value"
                            >
                              {{ option.label }}
                            </option>
                          </select>
                          <button
                            class="btn btn-primary btn-sm"
                            type="button"
                            :disabled="member.pendingRole === member.role || member.busy || !canManageAdmins"
                            @click="applyRole(member)"
                          >
                            <span v-if="member.busy" class="spinner-border spinner-border-sm me-1" />
                            Enregistrer
                          </button>
                        </div>
                        <div v-if="member.error" class="text-danger small mt-1">{{ member.error }}</div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { listOrganizationMembers, updateOrganizationMemberRole } from '@/services/organization'

const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const organization = ref(null)
const members = ref([])

const roleOptions = [
  { value: 'admin', label: 'Administrateur' },
  { value: 'auditor', label: 'Auditeur' },
  { value: 'member', label: 'Membre standard' },
]

const canManageAdmins = computed(() => Boolean(organization.value?.membership?.can_manage_admins))
const isAdmin = computed(() => Boolean(organization.value?.membership?.is_admin))
const roleBadgeClass = computed(() => roleBadgeClassFor(organization.value?.membership?.role || 'member'))

onMounted(() => {
  loadMembers()
})

async function loadMembers(options = {}) {
  const silent = options.silent ?? false
  if (silent) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  error.value = ''
  try {
    const payload = await listOrganizationMembers()
    organization.value = payload.organization
    members.value = (payload.members || []).map((member) => ({
      ...member,
      pendingRole: member.role,
      busy: false,
      error: '',
    }))
  } catch (err) {
    error.value = resolveError(err) || 'Impossible de charger les membres de votre organisation.'
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      loading.value = false
    }
  }
}

async function refresh() {
  await loadMembers({ silent: Boolean(organization.value) })
}

function roleLabel(role) {
  switch (role) {
    case 'owner':
      return 'Propriétaire'
    case 'admin':
      return 'Administrateur'
    case 'auditor':
      return 'Auditeur'
    default:
      return 'Membre'
  }
}

function roleBadgeClassFor(role) {
  if (role === 'owner') return 'bg-dark text-white'
  if (role === 'admin') return 'bg-primary-subtle text-primary'
  if (role === 'auditor') return 'bg-info-subtle text-info'
  return 'bg-light text-dark'
}

async function applyRole(member) {
  if (!canManageAdmins.value || member.role === member.pendingRole) return
  member.busy = true
  member.error = ''
  try {
    const updated = await updateOrganizationMemberRole(member.membership_id, member.pendingRole)
    const previousAdmin = Boolean(member.is_admin)
    member.role = updated.role
    member.pendingRole = updated.role
    member.is_admin = updated.is_admin
    if (organization.value) {
      const nowAdmin = Boolean(updated.is_admin)
      if (previousAdmin && !nowAdmin) {
        organization.value.admin_count = Math.max(0, (organization.value.admin_count || 1) - 1)
      } else if (!previousAdmin && nowAdmin) {
        organization.value.admin_count = (organization.value.admin_count || 0) + 1
      }
    }
  } catch (err) {
    member.error = resolveError(err) || 'Impossible de mettre à jour ce rôle.'
  } finally {
    member.busy = false
  }
}

function resolveError(err) {
  if (!err) return ''
  if (typeof err === 'string') return err
  const detail =
    err?.response?.data?.detail ||
    err?.response?.data?.error ||
    err?.message ||
    err?.response?.statusText
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail
  }
  return ''
}
</script>

<style scoped>
.organization-admin-card .summary-line > div {
  min-width: 120px;
}

.organization-admin-card table td {
  vertical-align: middle;
}

.organization-admin-card .badge {
  font-weight: 600;
}
</style>

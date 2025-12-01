<!--
  Vue: AdminUsersView
  Role: creation/suppression de comptes par un superadmin.
  Simplicite: formulaire de creation + tableau de membres avec action supprimer.
-->
<template>
  <div class="p-4 admin-users-view">
    <div class="d-flex align-items-center gap-3 mb-4">
      <h2 class="mb-0">
        <i class="bi bi-shield-lock-fill text-primary me-2"></i>
        Administration utilisateurs
      </h2>
      <span class="badge bg-dark text-white">Superadmin</span>
      <button class="btn btn-outline-secondary btn-sm ms-auto" type="button" :disabled="loading" @click="refresh">
        <span v-if="loading" class="spinner-border spinner-border-sm me-1" />
        Actualiser
      </button>
    </div>

    <div class="row g-4">
      <div class="col-lg-5">
        <div class="card shadow-sm border-0">
          <div class="card-body">
            <h5 class="card-title d-flex align-items-center gap-2 mb-3">
              <i class="bi bi-person-plus-fill text-primary"></i>
              Créer un compte
            </h5>

            <div v-if="formError" class="alert alert-warning py-2">{{ formError }}</div>
            <div v-if="formSuccess" class="alert alert-success py-2">{{ formSuccess }}</div>

            <div class="mb-3">
              <label class="form-label small text-muted">Email</label>
              <input v-model.trim="form.email" type="email" class="form-control" placeholder="user@example.com" />
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">Mot de passe</label>
              <input v-model="form.password" type="password" class="form-control" placeholder="Mot de passe temporaire" />
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">Nom / affichage</label>
              <input v-model.trim="form.displayName" type="text" class="form-control" placeholder="Nom visible" />
            </div>
            <div class="mb-3">
              <label class="form-label small text-muted">Role</label>
              <select v-model="form.role" class="form-select">
                <option value="member">Membre</option>
                <option value="support">Support</option>
                <option value="superadmin">Superadmin</option>
              </select>
            </div>
            <div class="form-check form-switch mb-3">
              <input v-model="form.confirmNow" class="form-check-input" type="checkbox" id="confirmNowToggle" />
              <label class="form-check-label" for="confirmNowToggle">Marquer l'email comme confirmé</label>
            </div>

            <button class="btn btn-primary w-100" type="button" :disabled="creating" @click="submit">
              <span v-if="creating" class="spinner-border spinner-border-sm me-2" />
              Creer
            </button>

            <div v-if="lastConfirmationLink" class="mt-3 alert alert-info small">
              Lien de confirmation : <code>{{ lastConfirmationLink }}</code>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-7">
        <div class="card shadow-sm border-0">
          <div class="card-body">
            <div class="d-flex align-items-center gap-2 mb-3">
              <i class="bi bi-people-fill text-primary"></i>
              <h5 class="mb-0">Membres</h5>
              <span class="badge bg-light text-dark">{{ members.length }} membres</span>
            </div>

            <div v-if="listError" class="alert alert-warning d-flex align-items-center gap-2">
              <i class="bi bi-exclamation-triangle"></i>
              <span class="flex-grow-1">{{ listError }}</span>
              <button class="btn btn-sm btn-outline-primary" type="button" :disabled="loading" @click="refresh">Réessayer</button>
            </div>

            <div v-else-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="text-muted mt-2 mb-0">Chargement...</p>
            </div>

            <div v-else>
              <div v-if="members.length === 0" class="text-muted">Aucun membre trouvé.</div>
              <div v-else class="table-responsive">
                <table class="table table-sm align-middle">
                  <thead>
                    <tr>
                      <th>Email</th>
                      <th>Nom</th>
                      <th>Rôle</th>
                      <th class="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="member in members" :key="member.user_id">
                      <td>{{ member.email }}</td>
                      <td>{{ member.display_name || '--' }}</td>
                      <td>
                        <span class="badge bg-secondary text-white text-uppercase">{{ member.role }}</span>
                      </td>
                      <td class="text-end">
                        <button
                          class="btn btn-outline-danger btn-sm"
                          type="button"
                          :disabled="member.busy"
                          @click="openConfirm(member)"
                        >
                          <span v-if="member.busy" class="spinner-border spinner-border-sm me-1" />
                          Supprimer
                        </button>
                        <div v-if="member.error" class="text-danger small mt-1">{{ member.error }}</div>
                        <div v-if="member.isDefaultAdmin" class="text-muted small">Admin principal protégé</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showConfirm" class="confirm-overlay">
        <div class="confirm-dialog">
          <h6 class="mb-3">Confirmer la suppression</h6>
          <p class="mb-4">
            Voulez-vous supprimer le compte
            <strong>{{ confirmTarget?.email }}</strong> ?
          </p>
          <div class="d-flex justify-content-end gap-2">
            <button class="btn btn-light" type="button" @click="closeConfirm">Annuler</button>
            <button class="btn btn-danger" type="button" :disabled="confirmTarget?.busy" @click="confirmRemoval">
              <span v-if="confirmTarget?.busy" class="spinner-border spinner-border-sm me-1" />
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listOrganizationMembers } from '@/services/organization'
import { createUserAsAdmin, deleteUserAsAdmin } from '@/services/admin'

const form = ref({
  email: '',
  password: '',
  displayName: '',
  role: 'member',
  confirmNow: true,
})

const members = ref([])
const loading = ref(false)
const creating = ref(false)
const listError = ref('')
const formError = ref('')
const formSuccess = ref('')
const lastConfirmationLink = ref('')
const showConfirm = ref(false)
const confirmTarget = ref(null)

const defaultAdminEmail = (import.meta.env.VITE_DEFAULT_ADMIN_EMAIL || '').trim().toLowerCase()

onMounted(() => {
  refresh()
})

function sanitizeForm() {
  return {
    email: form.value.email.trim(),
    password: form.value.password,
    display_name: form.value.displayName.trim() || null,
    role: form.value.role || 'member',
    confirm_now: Boolean(form.value.confirmNow),
  }
}

async function refresh() {
  loading.value = true
  listError.value = ''
  try {
    const payload = await listOrganizationMembers()
    members.value = (payload.members || []).map((member) => ({
      ...member,
      display_name: member.display_name || member.profile?.display_name || null,
      role: member.role || 'member',
      busy: false,
      error: '',
      isDefaultAdmin: isDefaultAdmin(member),
    }))
  } catch (err) {
    listError.value = resolveError(err) || 'Impossible de charger les membres.'
  } finally {
    loading.value = false
  }
}

async function submit() {
  formError.value = ''
  formSuccess.value = ''
  lastConfirmationLink.value = ''

  const payload = sanitizeForm()
  if (!payload.email || !payload.password) {
    formError.value = 'Email et mot de passe sont requis.'
    return
  }

  creating.value = true
  try {
    const data = await createUserAsAdmin(payload)
    formSuccess.value = 'Utilisateur créé.'
    if (data?.confirmation_url) {
      lastConfirmationLink.value = data.confirmation_url
    }
    form.value.password = ''
    await refresh()
  } catch (err) {
    formError.value = resolveError(err) || "Impossible de créer l'utilisateur."
  } finally {
    creating.value = false
  }
}

function isDefaultAdmin(member) {
  return defaultAdminEmail && member.email && member.email.toLowerCase() === defaultAdminEmail
}

async function removeMember(member) {
  member.error = ''
  if (member.isDefaultAdmin) {
    member.error = 'Admin principal protégé.'
    return
  }
  member.busy = true
  try {
    await deleteUserAsAdmin(member.user_id)
    await refresh()
  } catch (err) {
    member.error = resolveError(err) || 'Suppression impossible.'
  } finally {
    member.busy = false
  }
}

function openConfirm(member) {
  if (member.isDefaultAdmin) {
    member.error = 'Admin principal protégé.'
    return
  }
  confirmTarget.value = member
  showConfirm.value = true
}

function closeConfirm() {
  showConfirm.value = false
  confirmTarget.value = null
}

async function confirmRemoval() {
  if (!confirmTarget.value) return
  await removeMember(confirmTarget.value)
  closeConfirm()
}

function resolveError(err) {
  if (!err) return ''
  const detail = err.response?.data?.detail || err.message
  if (typeof detail === 'string') return detail
  return ''
}
</script>

<style scoped>
.admin-users-view .card {
  border-radius: 12px;
}

.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.confirm-dialog {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  width: min(420px, 90%);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
}
</style>

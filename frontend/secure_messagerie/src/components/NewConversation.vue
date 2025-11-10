<template>
  <div class="new-conv">
    <header class="new-conv__header">
      <div>
        <h1>Nouvelle conversation sécurisée</h1>
        <p class="new-conv__subtitle">
          Démarrez un espace chiffré de bout en bout avec vos contacts vérifiés. Configurez les règles de partage et invitez uniquement les personnes autorisées.
        </p>
      </div>
      <button type="button" class="btn btn-outline-secondary" @click="goBack">
        <i class="bi bi-arrow-left me-2" aria-hidden="true"></i>
        Retour aux messages
      </button>
    </header>

    <div v-if="error" class="alert alert-warning d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>

    <div class="new-conv__grid" :class="{ loading: loading }">
      <section class="card new-conv__card">
        <header class="card-header">
          <h2>Paramètres de conversation</h2>
        </header>
        <div class="card-body">
          <div class="form-group mb-4">
            <label class="form-label fw-semibold">Nom de la conversation <span class="text-muted fw-normal">(optionnel)</span></label>
            <input
              v-model.trim="title"
              type="text"
              class="form-control"
              maxlength="120"
              placeholder="Ex. Escalade projet Titan"
              :disabled="submitting"
            />
            <small class="text-muted">Utilisez un intitulé clair pour que vos collaborateurs identifient la conversation instantanément.</small>
          </div>

          <div class="form-group mb-4">
            <label class="form-label fw-semibold">Type de conversation</label>
            <div class="conv-type-list">
              <label v-for="option in typeOptions" :key="option.value" class="conv-type">
                <input
                  class="form-check-input"
                  type="radio"
                  :value="option.value"
                  v-model="conversationType"
                  :disabled="submitting"
                />
                <div class="conv-type__body">
                  <div class="d-flex align-items-center gap-2">
                    <i :class="option.icon" aria-hidden="true"></i>
                    <span class="fw-semibold">{{ option.label }}</span>
                  </div>
                  <p class="mb-0 text-muted small">{{ option.help }}</p>
                </div>
              </label>
            </div>
          </div>

          <div class="form-group mb-0">
            <label class="form-label fw-semibold">Message d'accueil <span class="text-muted fw-normal">(optionnel)</span></label>
            <textarea
              v-model="initialMessage"
              class="form-control"
              rows="4"
              maxlength="4000"
              placeholder="Partager le contexte, les objectifs ou les règles de sécurité dès le premier message."
              :disabled="submitting"
            ></textarea>
            <div class="d-flex justify-content-between small text-muted mt-1">
              <span>Le message d'accueil est envoyé automatiquement après la création.</span>
              <span>{{ initialMessage.length }}/4000</span>
            </div>
          </div>
        </div>
      </section>

      <section class="card new-conv__card">
        <header class="card-header d-flex align-items-center justify-content-between">
          <h2>Participants autorisés</h2>
          <span class="badge text-bg-primary">{{ selectedContacts.length }} sélectionné{{ selectedContacts.length > 1 ? 's' : '' }}</span>
        </header>
        <div class="card-body">
          <div class="form-group mb-3">
            <label class="form-label fw-semibold">Rechercher un contact</label>
            <div class="position-relative">
              <i class="bi bi-search search-icon" aria-hidden="true"></i>
              <input
                v-model.trim="search"
                type="search"
                class="form-control"
                placeholder="Nom, adresse e-mail…"
                :disabled="loading || submitting"
              />
            </div>
          </div>

          <div v-if="selectedContacts.length" class="selected-chips mb-3">
            <span v-for="contact in selectedContacts" :key="contact.id" class="chip">
              <span class="chip__label">{{ contact.displayName }}</span>
              <button type="button" class="chip__close" @click="removeParticipant(contact.id)" :disabled="submitting">
                <i class="bi bi-x"></i>
              </button>
            </span>
          </div>

          <p v-if="!contacts.length && !loading" class="text-muted small mb-0">
            Vous n'avez pas encore de contacts validés. Ajoutez des contacts depuis l'onglet dédié avant de créer une conversation.
          </p>

          <div v-else class="contact-list">
            <label
              v-for="contact in filteredContacts"
              :key="contact.id"
              class="contact-row form-check"
              :class="{ active: selection.includes(contact.id) }"
            >
              <input
                class="form-check-input"
                type="checkbox"
                :value="contact.id"
                :checked="selection.includes(contact.id)"
                @change="toggleParticipant(contact.id)"
                :disabled="submitting"
              />
              <div class="contact-row__body">
                <span class="fw-semibold">{{ contact.displayName }}</span>
                <span class="text-muted small">{{ contact.email }}</span>
              </div>
              <span class="contact-row__badge">
                {{ contact.trustLabel }}
              </span>
            </label>
            <div v-if="!filteredContacts.length && contacts.length" class="text-muted small text-center py-2">
              Aucun contact correspondant à "{{ search }}"…
            </div>
          </div>
          <p v-if="excludedContacts" class="text-muted small mt-2">
            {{ excludedContacts }} contact{{ excludedContacts > 1 ? 's' : '' }} non encore inscrit{{ excludedContacts > 1 ? 's' : '' }} ne peuvent pas être ajoutés à une conversation sécurisée.
          </p>

          <div v-if="selectionWarning" class="alert alert-info py-2 px-3 mt-3">
            <i class="bi bi-info-circle me-2" aria-hidden="true"></i>
            <span>{{ selectionWarning }}</span>
          </div>
        </div>
      </section>

      <aside class="new-conv__aside">
        <section class="card info-card">
          <header class="card-header">
            <h2>Protection & conformité</h2>
          </header>
          <div class="card-body">
            <ul class="list-unstyled mb-0">
              <li v-for="tip in securityTips" :key="tip.title" class="info-card__item">
                <i :class="tip.icon" aria-hidden="true"></i>
                <div>
                  <strong>{{ tip.title }}</strong>
                  <p class="mb-0 text-muted small">{{ tip.description }}</p>
                </div>
              </li>
            </ul>
          </div>
        </section>
        <section class="card summary-card">
          <header class="card-header">
            <h2>Résumé</h2>
          </header>
          <div class="card-body">
            <dl class="summary-list">
              <div>
                <dt>Type</dt>
                <dd>{{ selectedType.label }}</dd>
              </div>
              <div>
                <dt>Participants</dt>
                <dd>{{ selection.length }} contact{{ selection.length > 1 ? 's' : '' }}</dd>
              </div>
              <div>
                <dt>Message d'accueil</dt>
                <dd>{{ initialMessage ? 'Programmé' : 'Non défini' }}</dd>
              </div>
            </dl>
            <button
              type="button"
              class="btn btn-primary w-100"
              @click="submit"
              :disabled="submitDisabled"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
              Créer la conversation sécurisée
            </button>
            <p class="text-muted small mb-0 mt-2">
              Les conversations sont automatiquement journalisées dans l'audit interne. Aucun participant non sélectionné ne pourra rejoindre sans autorisation.
            </p>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="loading" class="loading-overlay" aria-hidden="true">
      <div class="spinner-border text-primary" role="status"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/utils/api'

const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const error = ref('')

const contacts = ref([])
const excludedContacts = ref(0)
const search = ref('')
const selection = ref([])

const title = ref('')
const conversationType = ref('group')
const initialMessage = ref('')

const typeOptions = [
  {
    value: 'direct',
    label: 'Conversation directe',
    icon: 'bi bi-person-lock',
    help: 'Canal privé entre deux personnes. Parfait pour des échanges confidentiels ou des suivis individuels.',
  },
  {
    value: 'group',
    label: 'Groupe collaboratif',
    icon: 'bi bi-people',
    help: 'Espace partagé pour coordonner une équipe ou un projet avec rétroaction en temps réel.',
  },
  {
    value: 'broadcast',
    label: 'Diffusion informelle',
    icon: 'bi bi-megaphone',
    help: 'Annonce ou diffusion descendante. Seuls les administrateurs publient, les autres reçoivent les notifications.',
  },
]

const securityTips = [
  {
    icon: 'bi bi-shield-lock-fill',
    title: 'Chiffrement de bout en bout',
    description: 'Chaque message est scellé avec vos clés. Aucun tiers, pas même la plateforme, n’y a accès.',
  },
  {
    icon: 'bi bi-clock-history',
    title: 'Traçabilité maîtrisée',
    description: 'Les événements critiques sont consignés dans le journal d’audit pour répondre aux exigences de conformité.',
  },
  {
    icon: 'bi bi-person-check-fill',
    title: 'Participants contrôlés',
    description: 'Seuls les contacts approuvés peuvent intégrer le canal. Les invitations externes nécessitent validation.',
  },
]

const filteredContacts = computed(() => {
  const term = search.value.toLowerCase()
  if (!term) return contacts.value
  return contacts.value.filter((contact) =>
    [contact.displayName, contact.email].some((value) => value.toLowerCase().includes(term)),
  )
})

const selectedContacts = computed(() => {
  const map = new Map(contacts.value.map((contact) => [contact.id, contact]))
  return selection.value
    .map((id) => map.get(id))
    .filter(Boolean)
})

const selectedType = computed(() => typeOptions.find((option) => option.value === conversationType.value) || typeOptions[0])

const selectionWarning = computed(() => {
  if (!selection.value.length) {
    return 'Sélectionnez au moins un contact pour activer la création.'
  }
  if (conversationType.value === 'direct' && selection.value.length !== 1) {
    return 'La conversation directe ne peut impliquer qu’un seul contact à la fois.'
  }
  if (conversationType.value === 'group' && selection.value.length < 2) {
    return 'Un groupe collaboratif nécessite au moins deux participants en plus de vous.'
  }
  return ''
})

const canSubmit = computed(() => {
  if (!selection.value.length || submitting.value) return false
  if (conversationType.value === 'direct') return selection.value.length === 1
  if (conversationType.value === 'group') return selection.value.length >= 2
  return true
})

const submitDisabled = computed(() => submitting.value || loading.value || !canSubmit.value)

watch(conversationType, (type) => {
  if (type === 'direct' && selection.value.length > 1) {
    selection.value = selection.value.slice(0, 1)
  }
})

async function fetchContacts() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/contacts', { params: { status: 'accepted' } })
    const items = Array.isArray(data) ? data : []
    const usable = []
    let excluded = 0
    for (const contact of items) {
      if (!contact?.contact_user_id) {
        excluded += 1
        continue
      }
      usable.push({
        id: String(contact.contact_user_id),
        email: contact.email,
        displayName: contact.display_name || contact.email,
        trustLabel: contact.status === 'accepted' ? 'Vérifié' : contact.status,
      })
    }
    contacts.value = usable
    excludedContacts.value = excluded
  } catch (err) {
    error.value = extractError(err, 'Impossible de récupérer vos contacts vérifiés.')
    contacts.value = []
  } finally {
    loading.value = false
  }
}

function toggleParticipant(id) {
  const exists = selection.value.includes(id)
  if (exists) {
    selection.value = selection.value.filter((value) => value !== id)
    return
  }
  if (conversationType.value === 'direct') {
    selection.value = [id]
  } else {
    selection.value = [...selection.value, id]
  }
}

function removeParticipant(id) {
  selection.value = selection.value.filter((value) => value !== id)
}

async function submit() {
  if (!canSubmit.value || submitDisabled.value) return
  submitting.value = true
  error.value = ''
  try {
    const payload = {
      title: title.value.trim() || null,
      participant_ids:
        conversationType.value === 'direct' ? selection.value.slice(0, 1) : selection.value.slice(),
      type: conversationType.value,
    }
    const { data } = await api.post('/conversations/', payload)
    const conversationId = data?.id
    if (!conversationId) throw new Error('Conversation non créée.')
    if (initialMessage.value.trim()) {
      await api.post(`/conversations/${conversationId}/messages`, {
        content: initialMessage.value.trim(),
      })
    }
    await router.push({ path: '/dashboard/messages', query: { conversation: conversationId } })
  } catch (err) {
    error.value = extractError(err, 'Impossible de créer la conversation sécurisée.')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.push({ path: '/dashboard/messages' }).catch(() => {})
}

function extractError(err, fallback) {
  if (!err) return fallback
  if (typeof err === 'string') return err
  const data = err.response?.data
  const detail =
    (typeof data?.detail === 'string' && data.detail) ||
    (Array.isArray(data?.detail) && data.detail.length && data.detail[0]) ||
    data?.message ||
    data?.error ||
    err.message
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  return fallback
}

onMounted(async () => {
  await fetchContacts()
})
</script>

<style scoped>
.new-conv {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-height: calc(100vh - 110px);
}

.new-conv__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
}

.new-conv__header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
}

.new-conv__subtitle {
  margin: 0;
  color: #6d7894;
  font-size: 0.95rem;
  max-width: 720px;
}

.new-conv__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1.6fr) minmax(280px, 0.8fr);
  gap: 1.5rem;
  position: relative;
}

.new-conv__grid.loading {
  pointer-events: none;
  opacity: 0.6;
}

.new-conv__card {
  border: none;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(15, 26, 48, 0.08);
  overflow: hidden;
}

.card-header {
  background: #fff;
  border-bottom: 1px solid rgba(13, 110, 253, 0.08);
}

.card-header h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.card-body {
  padding: 1.4rem;
}

.conv-type-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.conv-type {
  display: flex;
  gap: 0.75rem;
  border: 1px solid #d6deef;
  border-radius: 14px;
  padding: 0.75rem 0.9rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.conv-type:hover {
  border-color: #0d6efd;
  box-shadow: 0 8px 22px rgba(13, 110, 253, 0.11);
}

.conv-type__body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.conv-type__body i {
  color: #0d6efd;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #99a3c4;
}

.position-relative input {
  padding-left: 2.2rem;
  border-radius: 12px;
}

.selected-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(13, 110, 253, 0.12);
  color: #0d4ad4;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
}

.chip__close {
  border: none;
  background: transparent;
  color: inherit;
  padding: 0;
  display: inline-flex;
  align-items: center;
}

.contact-list {
  border: 1px solid #d6deef;
  border-radius: 16px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.contact-row {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.75rem 0.95rem;
  border-bottom: 1px solid rgba(215, 223, 238, 0.6);
  cursor: pointer;
  transition: background 0.1s ease;
}

.contact-row:last-child {
  border-bottom: none;
}

.contact-row.active {
  background: rgba(13, 110, 253, 0.1);
}

.contact-row__body {
  flex: 1;
  min-width: 0;
}

.contact-row__body span {
  display: block;
}

.contact-row__badge {
  font-size: 0.75rem;
  color: #0d4ad4;
  background: rgba(13, 110, 253, 0.1);
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-weight: 600;
}

.info-card {
  border-radius: 18px;
}

.info-card__item {
  display: flex;
  gap: 0.6rem;
  padding: 0.65rem 0;
}

.info-card__item i {
  color: #0d6efd;
  font-size: 1.1rem;
}

.summary-card {
  border-radius: 18px;
  margin-top: 1.5rem;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.9rem;
  margin-bottom: 1.5rem;
}

.summary-list dt {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6d7894;
  margin-bottom: 0.15rem;
}

.summary-list dd {
  margin: 0;
  font-weight: 600;
  font-size: 0.95rem;
  color: #13224b;
}

.new-conv__aside {
  display: flex;
  flex-direction: column;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(247, 249, 255, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

@media (max-width: 1200px) {
  .new-conv__grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    grid-template-areas:
      "main main"
      "aside aside";
  }

  .new-conv__aside {
    flex-direction: row;
    gap: 1.2rem;
  }

  .summary-card {
    margin-top: 0;
    flex: 1;
  }
}

@media (max-width: 992px) {
  .new-conv__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .new-conv__aside {
    flex-direction: column;
  }
}

@media (max-width: 576px) {
  .new-conv__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .new-conv__grid {
    gap: 1rem;
  }
}
</style>

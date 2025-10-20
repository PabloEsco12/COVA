<template>
  <div class="container py-4">
    <div class="row g-4">
      <!-- Hero / Welcome -->
      <div class="col-12">
        <div class="hero card border-0 overflow-hidden animate__animated animate__fadeIn">
          <div class="hero-bg"></div>
          <div class="hero-content d-flex align-items-center">
            <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="avatar-hero me-3" @error="onAvatarError" />
            <img v-else src="@/assets/logo_COVA.png" alt="COVA" class="avatar-hero me-3 placeholder" />
            <div class="flex-grow-1">
              <div class="text-white-50 small mb-1">{{ greeting }}</div>
              <h2 class="m-0 fw-bold text-white">Bienvenue, {{ pseudo }} !</h2>
              <div class="text-white-75 mt-1">Messagerie sécurisée, simple et rapide.</div>
            </div>
            <div class="d-flex gap-2">
              <router-link to="/dashboard/messages" class="btn btn-light btn-sm">
                <i class="bi bi-chat-dots me-1"></i> Ouvrir les messages
              </router-link>
              <router-link to="/dashboard/contacts" class="btn btn-outline-light btn-sm">
                <i class="bi bi-person-plus me-1"></i> Inviter un contact
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick stats -->
      <div class="col-12">
        <div class="row g-3">
          <div class="col-6 col-lg-3">
            <router-link to="/dashboard/messages" class="tile card h-100 text-decoration-none">
              <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-wrap bg-primary-subtle text-primary"><i class="bi bi-envelope-open"></i></div>
                <div>
                  <div class="tile-label">Non lus</div>
                  <div class="tile-value">{{ stats.unread }}</div>
                </div>
              </div>
            </router-link>
          </div>
          <div class="col-6 col-lg-3">
            <router-link to="/dashboard/contacts" class="tile card h-100 text-decoration-none">
              <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-wrap bg-success-subtle text-success"><i class="bi bi-people"></i></div>
                <div>
                  <div class="tile-label">Contacts</div>
                  <div class="tile-value">{{ stats.contacts }}</div>
                </div>
              </div>
            </router-link>
          </div>
          <div class="col-6 col-lg-3">
            <router-link to="/dashboard/invitations" class="tile card h-100 text-decoration-none">
              <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-wrap bg-warning-subtle text-warning"><i class="bi bi-person-plus"></i></div>
                <div>
                  <div class="tile-label">Invitations</div>
                  <div class="tile-value">{{ stats.invitations }}</div>
                </div>
              </div>
            </router-link>
          </div>
          <div class="col-6 col-lg-3">
            <router-link to="/dashboard/messages" class="tile card h-100 text-decoration-none">
              <div class="card-body d-flex align-items-center gap-3">
                <div class="icon-wrap bg-info-subtle text-info"><i class="bi bi-chat"></i></div>
                <div>
                  <div class="tile-label">Conversations</div>
                  <div class="tile-value">{{ stats.conversations }}</div>
                </div>
              </div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Recent items + System status -->
      <div class="col-12 col-lg-8">
        <div class="card h-100">
          <div class="card-header bg-white d-flex align-items-center">
            <i class="bi bi-clock-history me-2 text-primary"></i>
            <strong>Dernières conversations</strong>
            <router-link to="/dashboard/messages" class="ms-auto small">Tout voir</router-link>
          </div>
          <div class="list-group list-group-flush">
            <div v-if="recent.length === 0" class="p-3 text-muted small">Aucune conversation pour le moment.</div>
            <button
              v-for="c in recent"
              :key="c.id"
              type="button"
              class="list-group-item list-group-item-action d-flex align-items-center"
              @click="goToConversation(c.id)"
            >
              <i class="bi bi-chat-dots me-2 text-primary"></i>
              <div class="flex-grow-1">
                <div class="fw-semibold">{{ c.titre }}</div>
                <div class="text-muted small">Créée le {{ formatDate(c.date_crea) }}</div>
              </div>
              <i class="bi bi-chevron-right text-muted"></i>
            </button>
          </div>
        </div>
      </div>
      <div class="col-12 col-lg-4">
        <div class="card h-100">
          <div class="card-header bg-white d-flex align-items-center">
            <i class="bi bi-activity me-2 text-success"></i>
            <strong>État du système</strong>
          </div>
          <div class="card-body">
            <div class="d-flex align-items-center mb-2">
              <span class="status-dot me-2" :class="apiOk ? 'ok' : 'ko'"></span>
              <div>
                <div class="fw-semibold">API</div>
                <div class="text-muted small">{{ apiOk ? 'Connecté' : 'Hors ligne' }}</div>
              </div>
            </div>
            <div class="text-muted small">Conseil: gardez votre profil à jour et activez la 2FA pour plus de sécurité.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { api, backendBase } from '@/utils/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const apiOk = ref(false)
const pseudo = ref('Utilisateur')
const avatarUrl = ref(null)
const greeting = ref('Bonjour')

const stats = ref({ unread: 0, contacts: 0, invitations: 0, conversations: 0 })
const recent = ref([])

onMounted(async () => {
  // Local state
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null
  greeting.value = computeGreeting()

  // Ping API
  try {
    await api.get(`/ping`)
    apiOk.value = true
  } catch {
    apiOk.value = false
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const [me, unread, contacts, invitations, convs] = await Promise.all([
        api.get(`/me`),
        api.get(`/messages/unread_count`),
        api.get(`/contacts?statut=accepted`),
        api.get(`/contacts/invitations`),
        api.get(`/conversations/`),
      ])
      if (me.data?.pseudo) {
        pseudo.value = me.data.pseudo
        localStorage.setItem('pseudo', me.data.pseudo)
      }
      const apiAvatar = me.data?.avatar_url || (me.data?.avatar ? `${backendBase}/static/avatars/${me.data.avatar}` : null)
      if (apiAvatar) {
        avatarUrl.value = apiAvatar
        localStorage.setItem('avatar_url', apiAvatar)
      }
      stats.value.unread = Number(unread.data?.count || 0)
      stats.value.contacts = (contacts.data?.contacts || []).length
      stats.value.invitations = Array.isArray(invitations.data) ? invitations.data.length : 0
      const convList = Array.isArray(convs.data) ? convs.data : []
      stats.value.conversations = convList.length
      recent.value = convList
        .slice()
        .sort((a, b) => new Date(b.date_crea) - new Date(a.date_crea))
        .slice(0, 5)
    } catch (e) {
      // Best effort; keep defaults
    }
  }
})

function computeGreeting() {
  const h = new Date().getHours()
  if (h < 5) return 'Bonsoir'
  if (h < 12) return 'Bonjour'
  if (h < 18) return 'Bon après-midi'
  return 'Bonsoir'
}

function onAvatarError() { try { localStorage.removeItem('avatar_url') } catch {}; avatarUrl.value = null }

function formatDate(ts) {
  try { return new Date(ts).toLocaleString('fr-BE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) } catch { return '' }
}

function goToConversation(id) {
  router.push('/dashboard/messages')
}
</script>

<style scoped src="../styles/components/DashboardHomeEnhanced.css"></style>

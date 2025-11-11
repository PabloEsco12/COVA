<template>
  <transition name="fade">
    <div v-if="detailContact" class="modal-overlay" @click.self="$emit('close-details-modal')">
      <div class="modal-card detail-card">
        <div class="modal-header">
          <div>
            <h5 class="mb-0">
              <i class="bi bi-person-vcard me-2"></i>Fiche contact
            </h5>
            <small class="text-muted">Informations partagées depuis le profil sécurisé.</small>
          </div>
          <button class="btn btn-sm btn-outline-secondary" @click="$emit('close-details-modal')">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="modal-body detail-body" v-if="detailContact">
          <div class="detail-hero mb-3">
            <div class="contact-avatar detail-avatar">
              <img v-if="detailContact.avatar_url" :src="detailContact.avatar_url" alt="avatar" />
              <span v-else>{{ initials }}</span>
            </div>
            <div>
              <h4 class="mb-1">{{ displayName }}</h4>
              <p class="text-muted mb-2">{{ detailContact.email }}</p>
              <p v-if="detailContact.status_message" class="detail-status">
                <i class="bi bi-chat-quote-fill me-2 text-primary"></i>{{ detailContact.status_message }}
              </p>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-field">
              <span class="label">Fonction</span>
              <span class="value">{{ detailContact.job_title || 'Non renseigné' }}</span>
            </div>
            <div class="detail-field">
              <span class="label">Département / équipe</span>
              <span class="value">{{ detailContact.department || 'Non renseigné' }}</span>
            </div>
            <div class="detail-field">
              <span class="label">Téléphone sécurisé</span>
              <span class="value">{{ detailContact.phone_number || 'Non communiqué' }}</span>
            </div>
            <div class="detail-field">
              <span class="label">Statut</span>
              <span class="value">{{ statusLabel }}</span>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline-secondary" @click="$emit('close-details-modal')">
            Fermer
          </button>
          <button class="btn btn-primary" @click="$emit('open-conversation', detailContact)">
            <i class="bi bi-chat-dots me-1"></i>Ouvrir une conversation
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  detailContact: {
    type: Object,
    default: null,
  },
})

defineEmits(['close-details-modal', 'open-conversation'])

const displayName = computed(() => {
  if (!props.detailContact) return ''
  return (
    (props.detailContact.alias && props.detailContact.alias.trim()) ||
    (props.detailContact.display_name && props.detailContact.display_name.trim()) ||
    props.detailContact.email.split('@')[0]
  )
})

const initials = computed(() => {
  if (!props.detailContact) return ''
  const label = displayName.value
  const parts = label.split(/\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((w) => w[0])
  return letters.join('').toUpperCase() || label.slice(0, 2).toUpperCase()
})

const statusLabel = computed(() => {
  if (!props.detailContact) return ''
  switch (props.detailContact.status) {
    case 'accepted':
      return 'Contact actif'
    case 'pending':
      return 'En attente'
    case 'blocked':
      return 'Bloqué'
    default:
      return props.detailContact.status
  }
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

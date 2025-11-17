<!-- src/components/messages/ChatHeader.vue -->
<template>
  <header class="msg-main__header" role="banner" aria-label="En-tête de conversation">
    <div class="msg-main__identity">
      <button
        v-if="showBack"
        class="msg-main__icon"
        type="button"
        @click="handleBack"
        :aria-label="ariaBackLabel"
      >
        <i class="bi bi-arrow-left"></i>
      </button>
      <button
        v-if="showAvatar"
        type="button"
        class="msg-main__avatar msg-main__avatar-btn"
        @click="$emit('info')"
        aria-label="Afficher les informations du participant"
      >
        <img v-if="avatarUrl" :src="avatarUrl" alt="" />
        <span v-else>{{ avatarInitialsComputed }}</span>
        <span
          v-if="participantStatus"
          class="presence-indicator"
          :class="`presence-${participantStatus}`"
          :title="participantStatusLabel || 'Statut du participant'"
        ></span>
      </button>
      <div>
        <h3>{{ title || 'Messagerie' }}</h3>
        <p class="msg-main__meta">
          <slot name="subtitle">{{ subtitleComputed }}</slot>
        </p>
      </div>
    </div>

    <div class="msg-main__actions">
      <slot name="actions-left"></slot>

      <span
        v-if="showStatus"
        class="msg-status__pill"
        :class="statusClass"
        :title="statusTitle"
        role="status"
        :aria-live="status === 'connecting' ? 'polite' : 'off'"
      >
        {{ statusLabel }}
      </span>

      <button
        v-if="showCall"
        type="button"
        class="msg-main__icon"
        aria-label="Appel audio"
        @click="$emit('call')"
      >
        <i class="bi bi-telephone"></i>
      </button>
      <button
        v-if="showVideo"
        type="button"
        class="msg-main__icon"
        aria-label="Appel vidéo"
        @click="$emit('video')"
      >
        <i class="bi bi-camera-video"></i>
      </button>

      <button
        v-if="showRefresh"
        type="button"
        class="msg-main__icon"
        :disabled="loading"
        :aria-label="ariaRefreshLabel"
        @click="$emit('refresh')"
      >
        <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        <i v-else class="bi bi-arrow-clockwise"></i>
      </button>

      <button
        v-if="showInfo"
        type="button"
        class="msg-main__icon"
        aria-label="Informations de la conversation"
        @click="$emit('info')"
      >
        <i class="bi bi-info-circle"></i>
      </button>

      <slot name="actions"></slot>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  title: { type: String, default: 'Messagerie' },
  subtitle: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
  avatarInitials: { type: String, default: '' },
  showAvatar: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
  showBack: { type: Boolean, default: false },
  backTo: { type: [String, Object], default: null },
  showRefresh: { type: Boolean, default: true },
  showInfo: { type: Boolean, default: true },
  showStatus: { type: Boolean, default: true },
  showCall: { type: Boolean, default: true },
  showVideo: { type: Boolean, default: true },
  status: { type: String, default: 'idle' },
  participantStatus: { type: String, default: '' },
  participantStatusLabel: { type: String, default: '' },
})

const emit = defineEmits(['refresh', 'back', 'info', 'call', 'video'])
const router = useRouter()

const subtitleComputed = computed(() => props.subtitle || 'Discussions sécurisées sur COVA')
const ariaBackLabel = computed(() => 'Revenir à la page précédente')
const ariaRefreshLabel = computed(() => (props.loading ? 'Actualisation en cours' : 'Actualiser les messages'))

const statusLabel = computed(() => {
  switch (props.status) {
    case 'connected':
      return 'Canal actif'
    case 'connecting':
      return 'Connexion…'
    case 'error':
      return 'Canal indisponible'
    default:
      return 'En veille'
  }
})

const statusClass = computed(() => {
  switch (props.status) {
    case 'connected':
      return 'ok'
    case 'connecting':
      return 'pending'
    case 'error':
      return 'error'
    default:
      return 'idle'
  }
})

const statusTitle = computed(() => `Statut : ${statusLabel.value}`)
const avatarInitialsComputed = computed(() => props.avatarInitials || (props.title || 'MG').slice(0, 2).toUpperCase())

function handleBack() {
  if (props.backTo) {
    router.push(props.backTo).catch(() => {})
  } else {
    emit('back')
  }
}
</script>

<style src="@/assets/styles/messages.css"></style>


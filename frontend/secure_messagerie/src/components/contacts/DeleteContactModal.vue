<!--
  ===== Component Header =====
  Component: DeleteContactModal
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Confirmation de suppression d'un contact.
-->
<template>
  <!-- Fenetre modale de confirmation de suppression -->
  <transition name="fade">
    <div
      v-if="showDeleteModal"
      class="modal-overlay"
      @click.self="$emit('close-delete-modal')"
    >
      <div class="modal-card danger-card">
        <div class="modal-header">
          <div>
            <h5 class="mb-0 text-danger">
              <i class="bi bi-exclamation-triangle me-2"></i> Supprimer ce contact ?
            </h5>
            <small class="text-muted">
              Cette action retire la relation pour vous deux. Les conversations existantes ne sont pas supprimées.
            </small>
          </div>
          <button
            class="btn btn-sm btn-outline-secondary"
            @click="$emit('close-delete-modal')"
            :disabled="deleteBusy"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="deleteTarget" class="delete-preview">
            <div class="contact-avatar preview-avatar">
              <img v-if="deleteTarget.avatar_url" :src="deleteTarget.avatar_url" alt="avatar" />
              <span v-else>{{ initials }}</span>
            </div>
            <div class="flex-grow-1">
              <h6 class="mb-1">{{ displayName }}</h6>
              <p class="text-muted small mb-0">{{ deleteTarget.email }}</p>
            </div>
          </div>
          <p class="text-muted small mt-3 mb-0">
            Vous pourrez envoyer une nouvelle invitation si nécessaire. Le contact sera notifié de la suppression.
          </p>
          <div v-if="deleteError" class="alert alert-danger py-2 mt-3">
            {{ deleteError }}
          </div>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-outline-secondary"
            @click="$emit('close-delete-modal')"
            :disabled="deleteBusy"
          >
            Annuler
          </button>
          <button
            class="btn btn-danger"
            @click="$emit('confirm-delete')"
            :disabled="deleteBusy"
          >
            <span v-if="deleteBusy" class="spinner-border spinner-border-sm me-1"></span>
            Supprimer définitivement
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

// ===== Props de la modale de suppression =====
const props = defineProps({
  showDeleteModal: {
    type: Boolean,
    default: false,
  },
  deleteTarget: {
    type: Object,
    default: null,
  },
  deleteBusy: {
    type: Boolean,
    default: false,
  },
  deleteError: {
    type: String,
    default: '',
  },
})

// ===== Evenements emis vers le parent =====
defineEmits(['close-delete-modal', 'confirm-delete'])

// ===== Formatage des affichages =====
const displayName = computed(() => {
  if (!props.deleteTarget) return ''
  return (
    (props.deleteTarget.alias && props.deleteTarget.alias.trim()) ||
    (props.deleteTarget.display_name && props.deleteTarget.display_name.trim()) ||
    props.deleteTarget.email.split('@')[0]
  )
})

const initials = computed(() => {
  const label = displayName.value
  if (!label) return ''
  const parts = label.split(/\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((w) => w[0])
  return letters.join('').toUpperCase()
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

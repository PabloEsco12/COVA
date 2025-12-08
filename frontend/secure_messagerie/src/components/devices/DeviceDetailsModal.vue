<!--
  ===== Component Header =====
  Component: DeviceDetailsModal
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Modale d'inspection detaillee d'un appareil.
-->
<template>
  <transition name="fade">
    <div v-if="show" class="modal-backdrop"></div>
  </transition>
  <transition name="scale">
    <div v-if="show" class="modal-wrapper" @click.self="$emit('close')">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h5 class="mb-0">Details de l'appareil</h5>
            <small class="text-muted">Verifiez que cet appareil vous appartient.</small>
          </div>
          <button class="btn btn-sm btn-outline-secondary" type="button" @click="$emit('close')">
            <i class="bi bi-x-lg"></i>
          </button>
        </header>
        <!-- Corps detaille affiche uniquement si device fournit -->
        <div class="modal-body" v-if="device">
          <div class="modal-device-heading">
            <div :class="['device-avatar', device.iconClass]">
              <i :class="device.icon"></i>
            </div>
            <div>
              <h6 class="mb-1">{{ device.label }}</h6>
              <p v-if="device.subtitle" class="text-muted small mb-0">{{ device.subtitle }}</p>
              <p v-if="device.isCurrent" class="badge text-bg-primary mt-2 mb-0">Cet appareil</p>
            </div>
          </div>

          <div class="modal-two-cols">
            <div>
              <h6>Identification</h6>
              <p class="small text-muted mb-1">ID client :</p>
              <code class="payload-block">{{ device.id }}</code>

              <p class="small text-muted mb-1 mt-3">Inscrit le :</p>
              <p class="mb-0">{{ device.createdAt }}</p>

              <p class="small text-muted mb-1 mt-3">Dernier acces :</p>
              <p class="mb-0">
                {{ device.lastSeenAt ? device.lastSeenAt : 'Jamais' }}
                <span v-if="device.lastSeenRelative" class="text-muted">({{ device.lastSeenRelative }})</span>
              </p>
            </div>
            <div>
              <h6>Contexte navigateur</h6>
              <p class="small text-muted mb-1">User agent transmis :</p>
              <code class="payload-block">{{ device.metadata.userAgent || 'Non communique' }}</code>
              <p v-if="device.metadata.raw" class="small text-muted mt-2">
                Payload brut : <code>{{ device.metadata.raw }}</code>
              </p>
            </div>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-outline-secondary" type="button" @click="$emit('close')">Fermer</button>
          <button
            v-if="device && !device.isCurrent"
            class="btn btn-outline-danger"
            type="button"
            :disabled="revoking === device.id"
            @click="$emit('revoke', device)"
          >
            <span v-if="revoking === device.id" class="spinner-border spinner-border-sm me-1"></span>
            Déconnecter
          </button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script setup>
// ===== Props et emissions =====
defineProps({
  show: Boolean,
  device: Object,
  revoking: {
    type: String,
    default: '',
  },
})
defineEmits(['close', 'revoke'])
</script>

<!-- ===== Styles de la modale ===== -->
<style scoped src="@/assets/styles/devices.css"></style>

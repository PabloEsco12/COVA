<!--
  ===== Component Header =====
  Component: DeviceCard
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Carte d'appareil avec metadonnees et actions.
-->
<template>
  <article
    class="device-card card"
    :class="[{ 'device-card--current': device.isCurrent }, 'device-card--' + device.trustVariant]"
  >
    <div class="card-body">
      <div class="device-top">
        <div :class="['device-avatar', device.iconClass]">
          <i :class="device.icon"></i>
        </div>
        <div class="device-heading">
          <div>
            <h5 class="mb-1">{{ device.label }}</h5>
            <p v-if="device.subtitle" class="text-muted small mb-2">{{ device.subtitle }}</p>
          </div>
          <div class="badge-stack">
            <span v-if="device.isCurrent" class="badge text-bg-primary">Cet appareil</span>
            <span class="trust-chip" :class="'trust-chip--' + device.trustVariant">
              <i :class="device.trustIcon" class="me-1"></i>
              {{ device.trustLabel }}
            </span>
          </div>
        </div>
      </div>

      <ul class="device-meta list-unstyled small mb-0">
        <li>
          <i class="bi bi-clock me-2"></i>
          Inscrit le {{ device.createdAt }}
        </li>
        <li v-if="device.lastSeenAt">
          <i class="bi bi-activity me-2"></i>
          Vu {{ device.lastSeenRelative }}
          <span class="text-muted">({{ device.lastSeenAt }})</span>
        </li>
        <li v-if="device.timezone">
          <i class="bi bi-globe me-2"></i>
          Fuseau {{ device.timezone }}
        </li>
        <li v-if="device.language">
          <i class="bi bi-translate me-2"></i>
          Langue {{ device.language }}
        </li>
        <li v-if="device.screen">
          <i class="bi bi-aspect-ratio me-2"></i>
          Ecran {{ device.screen }}
        </li>
        <li v-if="device.lastSync">
          <i class="bi bi-arrow-repeat me-2"></i>
          Derniere synchro {{ device.lastSync }}
        </li>
      </ul>

      <!-- Actions: details ou revocation -->
      <div class="device-actions d-flex flex-wrap gap-2 mt-3">
        <button class="btn btn-outline-secondary btn-sm" type="button" @click="$emit('details', device)">
          <i class="bi bi-info-circle me-1"></i>
          Details
        </button>
        <button
          class="btn btn-outline-danger btn-sm"
          type="button"
          :disabled="device.isCurrent || revoking === device.id"
          @click="$emit('revoke', device)"
        >
          <span v-if="revoking === device.id" class="spinner-border spinner-border-sm me-1"></span>
          Déconnecter
        </button>
      </div>

      <div class="device-id text-muted small mt-3">
        ID client : <span>{{ device.id }}</span>
      </div>
    </div>
  </article>
</template>

<script setup>
// ===== Props et emissions =====
defineProps({
  device: {
    type: Object,
    required: true,
  },
  revoking: {
    type: String,
    default: '',
  },
})
defineEmits(['details', 'revoke'])
</script>

<!-- ===== Styles de la carte device ===== -->
<style scoped src="@/assets/styles/devices.css"></style>

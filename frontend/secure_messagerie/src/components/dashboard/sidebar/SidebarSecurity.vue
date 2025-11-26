<!--
  ===== Component Header =====
  Component: SidebarSecurity
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Resume securite et dernier audit dans la sidebar.
-->
<template>
  <section class="sidebar-section mt-4">
    <p class="sidebar-section-title">Sécurité & confidentialit\u00e9</p>
    <ul class="list-unstyled sidebar-security">
      <li class="security-item">
        <div class="security-icon info">
          <i class="bi bi-shield-check"></i>
        </div>
        <div>
          <span class="label">Chiffrement de bout en bout</span>
          <small class="text-muted">AES-256/GCM actif</small>
        </div>
      </li>
      <li class="security-item">
        <div :class="['security-icon', securitySettings.totpEnabled ? 'success' : 'warning']">
          <i :class="securitySettings.totpEnabled ? 'bi bi-shield-lock' : 'bi bi-exclamation-triangle'"></i>
        </div>
        <div>
          <span class="label">Double authentification</span>
          <small :class="securitySettings.totpEnabled ? 'text-success' : 'text-warning'">
            {{ securitySettings.totpEnabled ? 'Activée' : 'Désactivée' }}
          </small>
        </div>
      </li>
      <li class="security-item">
        <div :class="['security-icon', securitySettings.notificationLogin ? 'info' : 'muted']">
          <i class="bi bi-bell"></i>
        </div>
        <div>
          <span class="label">Alertes de connexion</span>
          <small :class="securitySettings.notificationLogin ? 'text-primary' : 'text-muted'">
            {{ securitySettings.notificationLogin ? 'Activées' : 'Aucune alerte' }}
          </small>
        </div>
      </li>
    </ul>

    <div v-if="lastAuditText" class="audit-card mt-3">
      <div class="audit-icon">
        <i class="bi bi-activity"></i>
      </div>
      <div>
        <span class="fw-semibold d-block">Dernière activité</span>
        <small class="text-muted">{{ lastAuditText }}</small>
      </div>
    </div>

    <button type="button" class="manage-security" @click="$emit('go-security')">
      <i class="bi bi-shield-lock me-2"></i>
      Gérer mes paramètres de sécurité
    </button>
  </section>
</template>

<script setup>
// ===== Props =====
defineProps({
  securitySettings: {
    type: Object,
    default: () => ({
      totpEnabled: false,
      notificationLogin: false,
    }),
  },
  lastAuditText: {
    type: String,
    default: '',
  },
})

defineEmits(['go-security'])
</script>

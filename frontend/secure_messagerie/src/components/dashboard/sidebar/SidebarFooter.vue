<!--
  ===== Component Header =====
  Component: SidebarFooter
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Zone basse de la sidebar (statut reseau et toggle theme).
-->
<template>
  <div class="sidebar-footer mt-auto pt-4">
    <div class="connection-status mb-3">
      <span class="status-indicator" :class="isOnline ? 'bg-success' : 'bg-warning'"></span>
      <span class="ms-2">{{ isOnline ? 'Réseau protégé' : 'Connexion instable' }}</span>
    </div>
    <button
      type="button"
      class="btn btn-sm theme-toggle"
      :class="isDark ? 'btn-outline-light' : 'btn-outline-secondary'"
      @click="$emit('toggle-dark')"
    >
      <i :class="isDark ? 'bi bi-sun' : 'bi bi-moon'"></i>
      {{ isDark ? 'Clair' : 'Sombre' }}
    </button>
    <div v-if="unreadCount > 0" class="mt-3 small text-muted text-center">
      {{ unreadCount }} message{{ unreadCount > 1 ? 's' : '' }} non lus
    </div>
  </div>
</template>

<script setup>
// ===== Props et evenements =====
defineProps({
  isOnline: {
    type: Boolean,
    default: true,
  },
  isDark: {
    type: Boolean,
    default: false,
  },
  unreadCount: {
    type: Number,
    default: 0,
  },
})

defineEmits(['toggle-dark'])
</script>

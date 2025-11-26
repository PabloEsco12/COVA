<!--
  ===== Component Header =====
  Component: SidebarInsights
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Carte d'informations securite/activite dans la sidebar.
-->
<template>
  <section class="sidebar-insights mb-4">
    <div class="insights-header">
      <div>
        <p class="insights-eyebrow">Vue sécurité</p>
        <h5 class="mb-0">{{ formattedToday }}</h5>
        <small class="text-muted">{{ formattedTime }}</small>
      </div>
      <button
        class="btn btn-outline-light btn-sm"
        :disabled="insightsRefreshing"
        @click="$emit('refresh-insights')"
      >
        <span v-if="insightsRefreshing" class="spinner-border spinner-border-sm me-1"></span>
        Rafraîchir
      </button>
    </div>
    <div class="insights-summary mt-3">
      <div v-for="highlight in highlights" :key="highlight.id" class="insight-highlight">
        <p class="highlight-label">{{ highlight.label }}</p>
        <p class="highlight-value">{{ highlight.value }}</p>
        <small>{{ highlight.hint }}</small>
      </div>
    </div>
    <div class="insight-actions mt-3">
      <article v-for="action in recommendations" :key="action.id" class="insight-action">
        <div class="insight-action__icon" :class="`variant-${action.variant || 'info'}`">
          <i :class="action.icon"></i>
        </div>
        <div class="insight-action__body">
          <p class="insight-action__title mb-1">
            {{ action.title }}
            <span v-if="action.badge" class="insight-action__badge">{{ action.badge }}</span>
          </p>
          <small class="insight-action__description">{{ action.description }}</small>
        </div>
      </article>
    </div>
    <div v-if="lastAuditText" class="insight-activity mt-3">
      <i class="bi bi-activity me-2"></i>
      <span>{{ lastAuditText }}</span>
    </div>
  </section>
</template>

<script setup>
// ===== Props et emissions =====
defineProps({
  formattedToday: {
    type: String,
    default: '',
  },
  formattedTime: {
    type: String,
    default: '',
  },
  highlights: {
    type: Array,
    default: () => [],
  },
  recommendations: {
    type: Array,
    default: () => [],
  },
  lastAuditText: {
    type: String,
    default: '',
  },
  insightsRefreshing: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['refresh-insights'])
</script>

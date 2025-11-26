<!--
  ===== Component Header =====
  Component: SidebarQuickLinks
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Raccourcis rapides dans la sidebar.
-->
<template>
  <section class="sidebar-section quick-links">
    <p class="sidebar-section-title">Raccourcis sécurisés</p>
    <div class="quick-links-grid">
      <router-link v-for="link in links" :key="link.to" class="quick-link" :to="link.to">
        <div class="quick-link__icon">
          <i :class="link.icon"></i>
        </div>
        <div class="quick-link__body">
          <span class="quick-link__label">
            {{ link.label }}
            <span
              v-if="link.badge"
              :class="[
                'quick-link__badge',
                link.badgeVariant ? `quick-link__badge--${link.badgeVariant}` : null,
              ]"
            >
              {{ link.badge }}
            </span>
          </span>
          <small class="quick-link__hint">{{ link.hint }}</small>
        </div>
        <i class="bi bi-arrow-right-short quick-link__chevron"></i>
      </router-link>
    </div>
  </section>
</template>

<script setup>
// ===== Props =====
defineProps({
  links: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <section class="security-summary card">
    <div class="summary-grid">
      <div class="summary-item">
        <h6 class="label">Appareils enregistres</h6>
        <p class="value">{{ summary.total }}</p>
        <span class="hint">{{ summary.currentLabel }}</span>
      </div>
      <div class="summary-item">
        <h6 class="label">Activite recente</h6>
        <p class="value">{{ summary.lastSeenRelative || 'Jamais' }}</p>
        <span class="hint" v-if="summary.lastSeenAt">Dernier acces {{ summary.lastSeenAt }}</span>
      </div>
      <div class="summary-item">
        <h6 class="label">Surveillance</h6>
        <p class="value" :class="{ 'text-warning': summary.risky > 0 }">{{ summary.risky }}</p>
        <span class="hint">
          {{ summary.risky > 0 ? 'Appareil(s) a verifier' : 'Aucun signal faible' }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  summary: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped src="@/assets/styles/devices.css"></style>

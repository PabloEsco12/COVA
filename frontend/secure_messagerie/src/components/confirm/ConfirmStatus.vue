<script setup>
defineProps({
  success: String,
  successSubtitle: String,
  error: String,
  errorHelp: String,
})
</script>

<template>
  <div v-if="success" class="status-block status-block--success">
    <div class="status-block__icon">
      <i class="bi bi-shield-check"></i>
    </div>
    <div class="status-block__body">
      <p class="status-block__title">{{ success }}</p>
      <p class="status-block__text">{{ successSubtitle }}</p>
    </div>
  </div>

  <div v-else class="status-block status-block--error">
    <div class="status-block__icon">
      <i class="bi bi-exclamation-octagon"></i>
    </div>
    <div class="status-block__body">
      <p class="status-block__title">Impossible de confirmer ce lien</p>
      <p class="status-block__text">{{ error }}</p>
      <p class="status-block__hint">{{ errorHelp }}</p>
    </div>
  </div>
</template>

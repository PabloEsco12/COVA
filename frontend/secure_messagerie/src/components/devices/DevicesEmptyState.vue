<!--
  ===== Component Header =====
  Component: DevicesEmptyState
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Bloc d'absence d'appareils avec action d'enregistrement.
-->
<template>
  <section class="empty-state card">
    <div class="card-body text-center">
      <div class="icon-circle mb-3">
        <i class="bi bi-broadcast"></i>
      </div>
      <h5>Aucun appareil enregistre</h5>
      <p class="text-muted mb-3">
        Nous n’avons pas encore detecte votre appareil actuel. Cliquez sur le bouton ci-dessous
        pour l’ajouter.
      </p>
      <button class="btn btn-primary" type="button" @click="$emit('manual-sync')" :disabled="registering">
        <span v-if="registering" class="spinner-border spinner-border-sm me-2"></span>
        <span v-else>Enregistrer cet appareil</span>
      </button>
    </div>
  </section>
</template>

<script setup>
// ===== Props et emissions =====
defineProps({
  registering: Boolean,
})
defineEmits(['manual-sync'])
</script>

<!-- ===== Styles de l'etat vide ===== -->
<style scoped src="@/assets/styles/devices.css"></style>

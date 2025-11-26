<!--
  ===== Component Header =====
  Component: DevicesGrid
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Grille listant les cartes appareils.
-->
<template>
  <section class="device-grid">
    <DeviceCard
      v-for="device in devices"
      :key="device.id"
      :device="device"
      :revoking="revoking"
      @details="$emit('open-details', device)"
      @revoke="$emit('open-delete', device)"
    />
  </section>
</template>

<script setup>
import DeviceCard from './DeviceCard.vue'

// ===== Props et emissions =====
defineProps({
  devices: {
    type: Array,
    required: true,
  },
  revoking: {
    type: String,
    default: '',
  },
})
defineEmits(['open-details', 'open-delete'])
</script>

<!-- ===== Styles de la grille devices ===== -->
<style scoped src="@/assets/styles/devices.css"></style>

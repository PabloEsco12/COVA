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

<style scoped src="@/assets/styles/devices.css"></style>

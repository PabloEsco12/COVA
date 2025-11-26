<!--
  ===== Component Header =====
  Component: MessageToastStack
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Pile de toasts informatifs liés aux messages.
-->
<template>
  <transition-group name="msg-toast" tag="div" class="msg-toast-stack">
    <article
      v-for="toast in toasts"
      :key="toast.id"
      class="msg-toast"
      @click="$emit('open', toast)"
    >
      <div class="msg-toast__content">
        <p class="msg-toast__title">{{ toast.title }}</p>
        <p class="msg-toast__body">{{ toast.body }}</p>
        <small>{{ formatter(toast.createdAt) }}</small>
      </div>
      <button
        type="button"
        class="msg-toast__close"
        @click.stop="$emit('dismiss', toast.id)"
        aria-label="Fermer la notification"
      >
        <i class="bi bi-x-lg"></i>
      </button>
    </article>
  </transition-group>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

// ===== Props =====
defineProps({
  toasts: {
    type: Array,
    default: () => [],
  },
  formatter: {
    type: Function,
    required: true,
  },
})

// ===== Emissions =====
defineEmits(['dismiss', 'open'])
</script>

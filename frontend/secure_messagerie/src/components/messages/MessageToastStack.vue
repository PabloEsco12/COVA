<template>
  <transition-group name="msg-toast" tag="div" class="msg-toast-stack">
    <article
      v-for="toast in toasts"
      :key="toast.id"
      class="msg-toast"
      @click="handleOpen(toast)"
    >
      <div class="msg-toast__content">
        <p class="msg-toast__title">{{ toast.title }}</p>
        <p class="msg-toast__body">{{ toast.body }}</p>
        <small>{{ formatTime(toast.createdAt) }}</small>
      </div>
      <button
        type="button"
        class="msg-toast__close"
        @click.stop="handleDismiss(toast.id)"
        aria-label="Fermer la notification"
      >
        <i class="bi bi-x-lg"></i>
      </button>
    </article>
  </transition-group>
</template>

<script setup>
const props = defineProps({
  toasts: {
    type: Array,
    default: () => [],
  },
  formatTime: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['open', 'dismiss'])

function handleOpen(toast) {
  emit('open', toast)
}

function handleDismiss(id) {
  emit('dismiss', id)
}
</script>

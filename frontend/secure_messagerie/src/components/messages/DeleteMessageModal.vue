<template>
  <CustomModal
    :model-value="visible"
    @update:modelValue="(val) => $emit('update:visible', val)"
  >
    <template #title>
      <i class="bi bi-trash me-2"></i>Supprimer le message
    </template>
    <p class="mb-2">
      Cette action retirera définitivement ce message pour tous les participants de la conversation.
    </p>
    <div v-if="preview" class="alert alert-warning py-2 px-3 mb-3">
      <strong>Aperçu&nbsp;:</strong>
      <span class="ms-1">{{ preview }}</span>
    </div>
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <template #footer>
      <button class="btn btn-outline-secondary" type="button" :disabled="loading" @click="$emit('close')">
        Annuler
      </button>
      <button class="btn btn-danger" type="button" :disabled="loading" @click="$emit('confirm')">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        Supprimer pour tous
      </button>
    </template>
  </CustomModal>
</template>

<script setup>
import CustomModal from '@/components/ui/CustomModal.vue'

defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  preview: {
    type: String,
    default: '',
  },
  error: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close', 'confirm', 'update:visible'])
</script>

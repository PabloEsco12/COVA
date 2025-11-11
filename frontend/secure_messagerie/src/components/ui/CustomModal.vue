<template>
  <div v-if="modelValue">
    <!-- backdrop comme avant -->
    <div class="modal-backdrop fade show"></div>

    <!-- même structure que ton ancien fichier -->
    <div class="custom-modal d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div class="custom-modal-dialog">
        <div class="custom-modal-content">
          <div class="custom-modal-header">
            <h5 class="custom-modal-title">
              <slot name="title">{{ title }}</slot>
            </h5>
            <button
              type="button"
              class="btn-close"
              aria-label="Fermer"
              @click="close"
            ></button>
          </div>
          <div class="custom-modal-body">
            <slot />
          </div>
          <div class="custom-modal-footer" v-if="$slots.footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}
</script>

<!-- tu peux le laisser scoped ou pas, vu que tu importes déjà ton CSS global -->
<style scoped src="@/assets/styles/settings.css"></style>

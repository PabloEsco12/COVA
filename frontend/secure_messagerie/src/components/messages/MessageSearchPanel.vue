<template>
  <div v-if="show" class="msg-search-panel">
    <form class="msg-search-panel__form" @submit.prevent="emit('submit')">
      <input
        :value="query"
        type="search"
        class="form-control"
        placeholder="Rechercher dans cette conversation"
        @input="emit('update:query', $event.target.value)"
      />
      <button class="btn btn-secondary btn-sm" type="submit" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        Rechercher
      </button>
      <button type="button" class="btn btn-link btn-sm" @click="emit('close')">Fermer</button>
    </form>
    <p v-if="error" class="msg-alert">{{ error }}</p>
    <ul class="msg-search-results">
      <li
        v-for="result in results"
        :key="result.id"
        class="msg-search-results__item"
      >
        <div>
          <p class="msg-search__author">{{ result.displayName }}</p>
          <p class="msg-search__excerpt">{{ messagePreviewText(result) }}</p>
          <small class="text-muted">{{ formatAbsolute(result.createdAt) }}</small>
        </div>
        <button type="button" class="btn btn-link p-0" @click="emit('jump', result)">Afficher</button>
      </li>
      <li
        v-if="executed && !loading && !results.length"
        class="text-muted small"
      >
        Aucun message trouvé.
      </li>
    </ul>
  </div>
</template>

<script setup>
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  query: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  results: {
    type: Array,
    default: () => [],
  },
  executed: {
    type: Boolean,
    default: false,
  },
  formatAbsolute: {
    type: Function,
    required: true,
  },
  messagePreviewText: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:query', 'submit', 'close', 'jump'])
</script>

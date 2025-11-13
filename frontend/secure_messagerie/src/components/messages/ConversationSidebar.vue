<template>
  <aside class="msg-nav">
    <header class="msg-nav__header">
      <div>
        <p class="msg-nav__eyebrow">Chats</p>
        <h2>{{ summaryText }}</h2>
      </div>
      <button
        class="msg-nav__action"
        type="button"
        @click="$emit('new-conversation')"
        :disabled="loading"
        aria-label="Nouvelle conversation"
      >
        <i class="bi bi-pencil-square" aria-hidden="true"></i>
      </button>
    </header>

    <label class="msg-search">
      <i class="bi bi-search"></i>
      <input
        :value="search"
        type="search"
        class="form-control form-control-sm"
        placeholder="Rechercher"
        :disabled="loading"
        @input="onSearchInput"
      />
    </label>

    <div class="msg-filters compact">
      <button
        v-for="f in filtersList"
        :key="f.value"
        type="button"
        class="msg-filter"
        :class="{ active: currentFilter === f.value }"
        @click="$emit('update:filter', f.value)"
      >
        {{ f.label }}
      </button>
    </div>

    <p v-if="error" class="msg-alert">{{ error }}</p>

    <ul class="msg-nav__list">
      <li v-for="c in conversations" :key="c.id">
        <button
          type="button"
          class="msg-nav__item"
          :class="{ active: c.id === selectedId }"
          @click="$emit('select', c.id)"
        >
          <span class="msg-avatar">
            <img
              v-if="c.avatarUrl"
              :src="c.avatarUrl"
              alt=""
              @error="$emit('avatar-error', c.id)"
            />
            <span v-else>{{ c.initials }}</span>
          </span>

          <span class="msg-item__body">
            <span class="msg-item__title">{{ c.displayName }}</span>
            <span class="msg-item__preview">{{ c.lastPreview || 'Aucun message' }}</span>
          </span>

          <span class="msg-item__meta">
            <time>{{ formatListTime(c.lastActivity) }}</time>
            <span v-if="c.unreadCount" class="msg-badge">{{ c.unreadCount }}</span>
          </span>
        </button>
      </li>

      <li v-if="!loading && !conversations.length" class="msg-empty-row">
        <span>Aucune conversation</span>
      </li>
      <li v-if="loading" class="msg-empty-row">
        <span>Chargement…</span>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  selectedId: { type: [String, Number, null], default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  summary: { type: String, default: '' },
  search: { type: String, default: '' },
  filter: { type: String, default: 'all' },
  filters: {
    type: Array,
    default: () => [
      { value: 'all', label: 'Toutes' },
      { value: 'unread', label: 'Non lues' },
      { value: 'direct', label: 'Direct' },
      { value: 'group', label: 'Groupes' },
    ],
  },
})

const emit = defineEmits(['select', 'new-conversation', 'avatar-error', 'update:search', 'update:filter'])

const filtersList = computed(() => props.filters)
const currentFilter = computed(() => props.filter)

const summaryText = computed(() => {
  if (props.summary) return props.summary
  if (props.loading) return 'Chargement…'
  const count = props.conversations.length
  return count ? `${count} conversation${count > 1 ? 's' : ''}` : 'Aucune conversation'
})

function onSearchInput(event) {
  emit('update:search', event.target.value)
}

function formatListTime(date) {
  const d = date instanceof Date ? date : new Date(date || Date.now())
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
</script>


<template>
  <div class="conv-list-wrap">
    <!-- En-tête -->
    <div class="d-flex align-items-center mb-3">
      <strong class="flex-grow-1">Conversations</strong>
      <div class="d-flex gap-2">
        <button
          class="btn btn-sm btn-outline-secondary"
          @click="$emit('refresh')"
          :disabled="loading"
          aria-label="Rafraîchir les conversations"
          title="Rafraîchir"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
        </button>
        <button
          class="btn btn-sm btn-primary"
          @click="$emit('create')"
          aria-label="Créer une conversation"
          title="Nouvelle conversation"
        >
          <i class="bi bi-plus" aria-hidden="true"></i>
        </button>
      </div>
    </div>

    <!-- Recherche -->
    <div class="mb-2 position-relative">
      <i class="bi bi-search position-absolute" style="left:10px; top: 9px; color:#8aa;" aria-hidden="true" />
      <input
        v-model="query"
        type="search"
        class="form-control"
        :placeholder="'Rechercher…'"
        :disabled="loading"
        style="padding-left:32px;border-radius:12px;"
        aria-label="Rechercher dans les conversations"
      />
    </div>

    <!-- État chargement -->
    <div v-if="loading" class="text-center py-4" role="status" aria-live="polite">
      <span class="spinner-border text-primary" aria-hidden="true"></span>
      <span class="visually-hidden">Chargement…</span>
    </div>

    <!-- Liste -->
    <ul
      v-else
      class="list-group list-group-flush"
      role="listbox"
      :aria-busy="false"
    >
      <li
        v-for="conv in filtered"
        :key="conv.id"
        class="list-group-item conv-item d-flex align-items-start gap-2"
        :class="{ active: conv.id === selectedId }"
        @click="$emit('select', conv.id)"
        @keydown.enter.prevent="$emit('select', conv.id)"
        @keydown.space.prevent="$emit('select', conv.id)"
        role="option"
        :aria-selected="conv.id === selectedId"
        :aria-current="conv.id === selectedId ? 'true' : undefined"
        tabindex="0"
        style="cursor:pointer;"
      >
        <!-- Avatar/icone simple (placeholder) -->
        <div class="rounded-circle d-inline-flex justify-content-center align-items-center"
             style="width:36px;height:36px;background:#eaf0ff;color:#1b57d0;flex:0 0 36px;">
          <i class="bi bi-chat-dots" aria-hidden="true"></i>
        </div>

        <!-- Corps -->
        <div class="flex-grow-1 min-w-0">
          <div class="d-flex align-items-center">
            <span class="fw-semibold text-truncate">
              {{ conv.titre || conv.title || ('Conversation ' + conv.id) }}
            </span>
            <small v-if="conv.updated_at" class="ms-auto text-muted ps-2 flex-shrink-0">
              {{ formatShortDate(conv.updated_at) }}
            </small>
          </div>

          <small class="text-muted d-block text-truncate">
            <template v-if="conv.last_message && (conv.last_message.content || conv.last_message.contenu_chiffre)">
              {{ (conv.last_message.content || conv.last_message.contenu_chiffre) }}
            </template>
            <template v-else>
              Aucun message pour le moment
            </template>
          </small>
        </div>

        <!-- Badge non lus -->
        <span
          v-if="conv.unread_count && conv.unread_count > 0"
          class="badge rounded-pill text-bg-primary align-self-center ms-2"
          aria-label="Messages non lus"
          title="Messages non lus"
        >
          {{ conv.unread_count }}
        </span>
      </li>

      <li v-if="!filtered.length" class="list-group-item text-muted small">
        Aucune conversation…
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  selectedId: { type: [Number, String, null], default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['refresh', 'create', 'select'])

const query = ref('')

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.conversations
  return props.conversations.filter((c) => {
    const title = (c.titre || c.title || '').toLowerCase()
    const last = (c.last_message?.content || c.last_message?.contenu_chiffre || '').toLowerCase()
    return title.includes(q) || last.includes(q) || String(c.id).includes(q)
  })
})

function formatShortDate(input) {
  try {
    const d = new Date(input)
    // Affiche HH:mm si aujourd’hui, sinon JJ/MM
    const now = new Date()
    const sameDay =
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate()
    return sameDay
      ? d.toLocaleTimeString('fr-BE', { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleDateString('fr-BE', { day: '2-digit', month: '2-digit' })
  } catch {
    return ''
  }
}
</script>

<style scoped src="@/assets/styles/messages.css"></style>

<template>
  <article
    class="contact-card card"
    :class="[
      `contact-card--${contact.status}`,
      { 'contact-card--highlight': highlight },
    ]"
  >
    <div class="card-body">
      <!-- zone cliquable -->
      <div
        class="contact-main contact-main--interactive"
        role="button"
        tabindex="0"
        @click="$emit('open-details', contact)"
        @keydown.enter.prevent="$emit('open-details', contact)"
        @keydown.space.prevent="$emit('open-details', contact)"
      >
        <div class="contact-avatar">
          <img v-if="contact.avatar_url" :src="contact.avatar_url" alt="avatar" />
          <span v-else>{{ initials }}</span>
        </div>
        <div class="contact-info">
          <div class="contact-name">
            <strong>{{ displayName }}</strong>
            <button
              v-if="contact.status === 'accepted'"
              class="btn btn-link btn-sm"
              @click.stop="$emit('start-alias-edit', contact)"
              title="Modifier l'alias"
            >
              <i class="bi bi-pencil-square"></i>
            </button>
          </div>
          <div class="contact-meta text-muted small">
            <span>{{ secondaryLabel }}</span>
            <span class="dot-separator"></span>
            <span>{{ statusLabel }}</span>
            <span v-if="contact.created_at" class="d-none d-md-inline">
              <span class="dot-separator"></span>
              Ajouté le {{ formatDate(contact.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <!-- éditeur d'alias -->
      <div
        v-if="editingAlias"
        class="alias-editor input-group input-group-sm mt-2"
        @click.stop
      >
        <input
          :ref="(el) => $emit('set-alias-input-ref', el)"
          v-model.trim="localAliasDraft"
          type="text"
          class="form-control"
          maxlength="160"
          placeholder="Alias personnalisé"
          @keyup.enter="$emit('save-alias', { contact, value: localAliasDraft })"
          @keyup.esc="$emit('cancel-alias-edit')"
        />
        <button class="btn btn-outline-secondary" @click="$emit('cancel-alias-edit')">
          Annuler
        </button>
        <button class="btn btn-primary" @click="$emit('save-alias', { contact, value: localAliasDraft })">
          <span v-if="aliasSaving" class="spinner-border spinner-border-sm"></span>
          <span v-else>Enregistrer</span>
        </button>
      </div>

      <!-- actions -->
      <div class="contact-actions">
        <!-- pending -->
        <template v-if="contact.status === 'pending'">
          <button
            class="btn btn-success btn-sm"
            :disabled="busy"
            @click="$emit('set-status', { contact, status: 'accepted' })"
          >
            <span v-if="busy" class="spinner-border spinner-border-sm me-1"></span>
            Accepter
          </button>
          <button
            class="btn btn-outline-secondary btn-sm"
            :disabled="busy"
            @click="$emit('set-status', { contact, status: 'blocked' })"
          >
            Bloquer
          </button>
          <button
            class="btn btn-outline-danger btn-sm"
            :disabled="busy"
            @click="$emit('prompt-delete', contact)"
          >
            Refuser
          </button>
        </template>

        <!-- accepted -->
        <template v-else-if="contact.status === 'accepted'">
          <button
            class="btn btn-outline-primary btn-sm"
            @click="$emit('open-conversation', contact)"
          >
            <i class="bi bi-chat-dots me-1"></i> Converser
          </button>
          <button
            class="btn btn-outline-secondary btn-sm"
            :disabled="busy"
            @click="$emit('set-status', { contact, status: 'blocked' })"
          >
            Bloquer
          </button>
          <button
            class="btn btn-outline-danger btn-sm"
            :disabled="busy"
            @click="$emit('prompt-delete', contact)"
          >
            Supprimer
          </button>
        </template>

        <!-- blocked -->
        <template v-else>
          <button
            class="btn btn-outline-success btn-sm"
            :disabled="busy"
            @click="$emit('set-status', { contact, status: 'accepted' })"
          >
            Débloquer
          </button>
          <button
            class="btn btn-outline-danger btn-sm"
            :disabled="busy"
            @click="$emit('prompt-delete', contact)"
          >
            Supprimer
          </button>
        </template>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
  highlight: {
    type: Boolean,
    default: false,
  },
  // true si le parent est en train d'éditer CETTE carte
  editingAlias: {
    type: Boolean,
    default: false,
  },
  // valeur actuelle de l'alias dans le parent
  aliasDraft: {
    type: String,
    default: '',
  },
  aliasSaving: {
    type: Boolean,
    default: false,
  },
  busy: {
    type: Boolean,
    default: false,
  },
})

defineEmits([
  'open-details',
  'start-alias-edit',
  'cancel-alias-edit',
  'save-alias',
  'set-status',
  'prompt-delete',
  'open-conversation',
  'set-alias-input-ref',
])

// on garde une copie locale pour pouvoir taper et renvoyer la valeur au parent
const localAliasDraft = ref(props.aliasDraft)

watch(
  () => props.aliasDraft,
  (val) => {
    localAliasDraft.value = val
  },
)

const displayName = computed(() => {
  return (
    (props.contact.alias && props.contact.alias.trim()) ||
    (props.contact.display_name && props.contact.display_name.trim()) ||
    props.contact.email.split('@')[0]
  )
})

const secondaryLabel = computed(() => {
  if (props.contact.job_title) {
    return props.contact.job_title
  }
  if (props.contact.department) {
    return props.contact.department
  }
  if (
    props.contact.alias &&
    props.contact.display_name &&
    props.contact.alias !== props.contact.display_name
  ) {
    return props.contact.display_name
  }
  return props.contact.email
})

const initials = computed(() => {
  const label = displayName.value
  const parts = label.split(/\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((w) => w[0])
  return letters.join('').toUpperCase() || label.slice(0, 2).toUpperCase()
})

const statusLabel = computed(() => {
  switch (props.contact.status) {
    case 'accepted':
      return 'Contact actif'
    case 'pending':
      return 'En attente'
    case 'blocked':
      return 'Bloqué'
    default:
      return props.contact.status
  }
})

function formatDate(value) {
  try {
    return new Date(value).toLocaleDateString()
  } catch {
    return ''
  }
}
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

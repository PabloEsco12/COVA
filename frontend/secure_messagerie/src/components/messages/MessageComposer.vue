<!--
  ===== Component Header =====
  Component: MessageComposer
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Zone de composition de message (texte, pièces jointes, actions).
-->
<template>
  <div
    v-if="blockedInfo"
    class="msg-composer msg-composer--disabled"
  >
    <div class="msg-blocked-banner__icon">
      <i :class="blockedInfo.state === 'blocked_by_other' ? 'bi bi-shield-lock-fill' : 'bi bi-shield-check'" aria-hidden="true"></i>
    </div>
    <div class="msg-blocked-banner__body">
      <p class="mb-1 fw-semibold">{{ blockedInfo.title }}</p>
      <p class="mb-0 text-muted">{{ blockedInfo.message }}</p>
    </div>
    <router-link to="/dashboard/contacts" class="btn btn-outline-primary btn-sm">
      GÃ©rer les contacts
    </router-link>
  </div>

  <form v-else class="msg-composer" @submit.prevent="sendMessage">
    <div class="msg-composer__pickers">
      <div v-if="showPicker" class="msg-picker" role="menu" aria-label="Choisir un contenu">
        <div class="msg-picker__header">
          <div class="msg-picker__tabs">
            <button type="button" :class="{ active: pickerMode === 'emoji' }" @click="setPickerMode('emoji')">Emoji</button>
            <button type="button" :class="{ active: pickerMode === 'gif' }" @click="setPickerMode('gif')">GIF</button>
          </div>
          <input
            v-if="pickerMode === 'emoji'"
            :value="emojiSearch"
            type="search"
            class="msg-picker__search"
            placeholder="Rechercher un emoji"
            @input="onEmojiSearch($event.target.value)"
          />
          <input
            v-else-if="gifSearchAvailable"
            :value="gifSearch"
            type="search"
            class="msg-picker__search"
            placeholder="Rechercher un GIF"
            @input="onGifSearch($event.target.value)"
          />
          <p v-else class="msg-picker__hint">Bibliothèque locale de GIFs prête à l'emploi.</p>
        </div>
        <div class="msg-picker__body" v-if="pickerMode === 'emoji'">
          <div
            v-for="section in filteredEmojiSections"
            :key="section.id"
            class="msg-picker__section"
          >
            <p class="msg-picker__section-title">{{ section.label }}</p>
            <div class="msg-picker__grid">
              <button
                type="button"
                v-for="emoji in section.items"
                :key="`${section.id}-${emoji}`"
                @click="addEmoji(emoji)"
              >
                {{ emoji }}
              </button>
            </div>
          </div>
        </div>
        <div class="msg-picker__body msg-picker__body--gifs" v-else>
          <button type="button" v-for="gif in displayedGifs" :key="gif.url" @click="insertGif(gif)">
            <img :src="gif.preview || gif.url" :alt="gif.label" />
            <span>{{ gif.label }}</span>
          </button>
          <p v-if="gifError && gifSearchAvailable && !loadingGifs" class="msg-picker__error">{{ gifError }}</p>
          <div v-if="loadingGifs" class="msg-picker__loading">
            <span class="spinner-border spinner-border-sm me-2"></span>
            Chargement…
          </div>
        </div>
      </div>
    </div>

    <input :ref="attachmentInput" class="visually-hidden" type="file" multiple @change="onAttachmentChange" />
    <textarea
      :value="messageInput"
      class="form-control"
      rows="2"
      placeholder="Ecrire un message sécurisé."
      :disabled="sending"
      @keydown.enter.exact.prevent="sendMessage"
      @input="handleComposerInput"
      @blur="handleComposerBlur"
    ></textarea>

    <div v-if="pendingAttachments.length && !isEditingMessage" class="msg-composer__attachments">
      <article v-for="attachment in pendingAttachments" :key="attachment.id" class="msg-composer__attachment">
        <div>
          <strong>{{ attachment.name }}</strong>
          <p class="small mb-0 text-muted">
            {{ formatFileSize(attachment.size) }}
            <span v-if="attachment.status === 'uploading'"> Â· {{ attachment.progress || 0 }}%</span>
            <span v-if="attachment.status === 'error'" class="text-danger"> Â· {{ attachment.error }}</span>
          </p>
        </div>
        <div class="msg-composer__attachment-actions">
          <span v-if="attachment.status === 'uploading'" class="msg-panel__pill">Envoi</span>
          <span v-else-if="attachment.status === 'ready'" class="msg-panel__pill ok">Prêt</span>
          <button type="button" class="btn btn-link p-0" @click="removeAttachment(attachment.id)">Retirer</button>
        </div>
      </article>
    </div>
    <p v-if="attachmentError" class="msg-alert mb-2">{{ attachmentError }}</p>

    <div v-if="hasComposerContext" class="msg-composer__context">
      <div>
        <template v-if="isEditingMessage">
          <strong>Modification du message</strong>
        </template>
        <template v-else-if="composerState.replyTo">
          <strong>Réponse à  {{ composerState.replyTo.displayName || composerState.replyTo.authorDisplayName || 'Participant' }}</strong>
          <p class="small mb-0 text-muted">
            {{ messagePreviewText(composerState.replyTo) }}
          </p>
        </template>
        <template v-else-if="composerState.forwardFrom">
          <strong>Transfert</strong>
          <p class="small mb-0 text-muted">
            {{ messagePreviewText(composerState.forwardFrom) }}
          </p>
        </template>
      </div>
      <button type="button" class="btn btn-link p-0" @click="cancelComposerContext">Annuler</button>
    </div>

    <p v-if="typingIndicatorText" class="msg-typing-indicator">
      <i class="bi bi-pencil" aria-hidden="true"></i>
      <span>{{ typingIndicatorText }}</span>
    </p>

    <div class="msg-composer__footer">
      <div class="msg-composer__left">
        <div class="msg-composer__actions">
          <button
            type="button"
            class="msg-icon-btn"
            @click="triggerAttachmentPicker"
            :disabled="hasAttachmentInProgress || isEditingMessage"
            aria-label="Ajouter une piÃ¨ce jointe"
          >
            <i class="bi bi-paperclip"></i>
          </button>
          <button type="button" class="msg-icon-btn primary" @click="togglePicker" aria-label="Emoji et GIF">
            <i class="bi bi-emoji-smile"></i>
          </button>
        </div>
        <small>{{ messageInput.length }}/2000</small>
      </div>
      <button class="btn btn-primary" type="submit" :disabled="!canSend || sending">
        <span v-if="sending" class="spinner-border spinner-border-sm me-2"></span>
        Envoyer
      </button>
    </div>
  </form>
</template>

<script setup>
// ===== Props d'etat et de configuration =====
const props = defineProps({
  blockedInfo: Object,
  showPicker: Boolean,
  pickerMode: String,
  emojiSearch: String,
  gifSearch: String,
  gifSearchAvailable: Boolean,
  filteredEmojiSections: {
    type: Array,
    default: () => [],
  },
  displayedGifs: {
    type: Array,
    default: () => [],
  },
  gifError: String,
  loadingGifs: Boolean,
  addEmoji: {
    type: Function,
    required: true,
  },
  insertGif: {
    type: Function,
    required: true,
  },
  onEmojiSearch: {
    type: Function,
    default: () => {},
  },
  onGifSearch: {
    type: Function,
    default: () => {},
  },
  attachmentInput: Object,
  onAttachmentChange: {
    type: Function,
    required: true,
  },
  messageInput: {
    type: String,
    default: '',
  },
  sending: Boolean,
  onComposerInput: {
    type: Function,
    required: true,
  },
  handleComposerBlur: {
    type: Function,
    required: true,
  },
  pendingAttachments: {
    type: Array,
    default: () => [],
  },
  isEditingMessage: Boolean,
  formatFileSize: {
    type: Function,
    required: true,
  },
  removeAttachment: {
    type: Function,
    required: true,
  },
  attachmentError: String,
  hasComposerContext: Boolean,
  composerState: {
    type: Object,
    default: () => ({}),
  },
  messagePreviewText: {
    type: Function,
    required: true,
  },
  cancelComposerContext: {
    type: Function,
    required: true,
  },
  typingIndicatorText: String,
  triggerAttachmentPicker: {
    type: Function,
    required: true,
  },
  hasAttachmentInProgress: Boolean,
  togglePicker: {
    type: Function,
    required: true,
  },
  setPickerMode: {
    type: Function,
    required: true,
  },
  canSend: Boolean,
  sendMessage: {
    type: Function,
    required: true,
  },
})

// ===== Emissions =====
const emit = defineEmits(['update:messageInput'])

function handleComposerInput(event) {
  props.onComposerInput(event)
  const value = event?.target?.value ?? ''
  emit('update:messageInput', value)
}
</script>


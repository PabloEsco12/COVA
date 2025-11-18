<template>
  <div class="msg-body">
    <section v-if="pinnedMessages.length" class="msg-pinned card">
      <header class="msg-pinned__header">
        <i class="bi bi-bookmark-star-fill" aria-hidden="true"></i>
        <div>
          <strong>{{ pinnedMessages.length }} message{{ pinnedMessages.length > 1 ? 's' : '' }} épinglé{{ pinnedMessages.length > 1 ? 's' : '' }}</strong>
          <p class="mb-0 small text-muted">Gardez les consignes critiques à portée de main.</p>
        </div>
      </header>
      <ul class="msg-pinned__list">
        <li v-for="pin in pinnedMessages" :key="`pin-${pin.id}`">
          <button type="button" @click="$emit('select-pin', pin.id)">
            <span class="msg-pinned__time">{{ callFormatter('formatTime', pin.createdAt) }}</span>
            <span class="msg-pinned__preview">{{ pin.preview }}</span>
          </button>
        </li>
      </ul>
    </section>

    <div ref="threadEl" class="msg-thread" @scroll="onScroll">
      <div v-if="loadingOlder" class="msg-thread__loader">
        <span class="spinner-border spinner-border-sm me-2"></span>
        Chargement des messages précédents.
      </div>

      <article
        v-for="message in messages"
        :key="message.id"
        :id="`message-${message.id}`"
        class="msg-bubble"
        :class="bubbleClass(message)"
      >
        <header class="msg-bubble__meta">
          <div class="msg-bubble__identity">
            <span>{{ message.displayName }}</span>
            <span v-if="message.pinned" class="msg-pill">
              <i class="bi bi-bookmark-fill" aria-hidden="true"></i>
              Épinglé
            </span>
            <span
              v-if="callFormatter('messageSecurityLabel', message)"
              class="msg-security-icon"
              :title="callFormatter('messageSecurityTooltip', message)"
            >
              <i class="bi bi-shield-lock-fill" aria-hidden="true"></i>
            </span>
            <span v-if="message.editedAt && !message.deleted" class="msg-bubble__badge">Modifié</span>
          </div>
          <div class="msg-bubble__meta-aside">
            <div class="msg-bubble__timestamps">
              <span
                v-if="callFormatter('messageStatusLabel', message)"
                class="msg-state"
                :class="callFormatter('messageStatusClass', message)"
              >
                {{ callFormatter('messageStatusLabel', message) }}
              </span>
              <time :title="callFormatter('formatAbsolute', message.createdAt)">
                {{ callFormatter('formatTime', message.createdAt) }}
              </time>
            </div>
            <div
              v-if="!message.deleted && !message.isSystem"
              :class="['msg-bubble__toolbar', message.sentByMe ? 'msg-bubble__toolbar--right' : 'msg-bubble__toolbar--left']"
              @click.stop
            >
              <button
                type="button"
                class="icon-btn subtle"
                :aria-expanded="reactionPickerFor === message.id"
                :aria-label="`Réagir au message de ${message.displayName}`"
                @click.stop="$emit('toggle-reaction-picker', message.id)"
              >
                <i class="bi bi-emoji-smile"></i>
              </button>
              <button
                type="button"
                class="icon-btn subtle"
                :aria-expanded="messageMenuOpen === message.id"
                :aria-label="`Afficher les actions pour le message de ${message.displayName}`"
                @click.stop="$emit('toggle-message-menu', message.id)"
              >
                <i class="bi bi-three-dots"></i>
              </button>
              <div
                v-if="reactionPickerFor === message.id"
                :class="[
                  'msg-popover',
                  'msg-popover--reactions',
                  message.sentByMe ? 'msg-popover--left' : 'msg-popover--right',
                ]"
                role="menu"
                aria-label="Choisir une réaction"
              >
                <button
                  v-for="emoji in reactionPalette"
                  :key="`${message.id}-picker-${emoji}`"
                  type="button"
                  class="msg-popover__item"
                  @click="$emit('reaction-select', { message, emoji })"
                  :disabled="isReactionPending(message.id, emoji)"
                >
                  {{ emoji }}
                </button>
              </div>
              <div
                v-if="messageMenuOpen === message.id"
                :class="[
                  'msg-popover',
                  'msg-popover--menu',
                  message.sentByMe ? 'msg-popover--left' : 'msg-popover--right',
                ]"
                role="menu"
                aria-label="Actions du message"
              >
                <button type="button" class="msg-menu__item" @click="$emit('copy', message)">
                  <i class="bi bi-clipboard"></i>
                  Copier
                </button>
                <button type="button" class="msg-menu__item" @click="$emit('reply', message)">
                  <i class="bi bi-reply"></i>
                  Répondre
                </button>
                <button type="button" class="msg-menu__item" @click="$emit('forward', message)">
                  <i class="bi bi-share"></i>
                  Transférer
                </button>
                <button
                  type="button"
                  class="msg-menu__item"
                  :disabled="isPinning(message.id)"
                  @click="$emit('pin', message)"
                >
                  <i :class="message.pinned ? 'bi bi-bookmark-fill' : 'bi bi-bookmark'"></i>
                  {{ message.pinned ? 'Retirer des favoris' : 'Épingler' }}
                </button>
                <button
                  v-if="message.sentByMe"
                  type="button"
                  class="msg-menu__item"
                  @click="$emit('edit', message)"
                >
                  <i class="bi bi-pencil-square"></i>
                  Modifier
                </button>
                <button
                  v-if="message.sentByMe || canModerate"
                  type="button"
                  class="msg-menu__item text-danger"
                  @click="$emit('delete', message)"
                >
                  <i class="bi bi-trash"></i>
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </header>

        <div v-if="message.replyTo" class="msg-reference msg-reference--reply">
          <p class="msg-reference__author">{{ message.replyTo.authorDisplayName || 'Participant' }}</p>
          <p class="msg-reference__excerpt">
            <span v-if="message.replyTo.deleted" class="text-muted">Message supprimé</span>
            <span v-else>{{ message.replyTo.excerpt }}</span>
          </p>
        </div>

        <div v-if="message.forwardFrom" class="msg-reference msg-reference--forward">
          <p class="msg-reference__author">Transfert de {{ message.forwardFrom.authorDisplayName || 'Participant' }}</p>
          <p class="msg-reference__excerpt">
            <span v-if="message.forwardFrom.deleted" class="text-muted">Message supprimé</span>
            <span v-else>{{ message.forwardFrom.excerpt }}</span>
          </p>
        </div>

        <div v-if="message.deleted" class="msg-bubble__deleted">Message supprimé</div>
        <template v-else>
          <pre class="msg-bubble__body">{{ message.content }}</pre>

          <div v-if="message.attachments?.length" class="msg-attachments">
            <article v-for="attachment in message.attachments" :key="attachment.id" class="msg-attachment">
              <div class="msg-attachment__icon" aria-hidden="true">
                <i :class="attachmentIconClass(attachment)"></i>
              </div>
              <div class="msg-attachment__body">
                <strong>{{ attachment.fileName || 'Pièce jointe' }}</strong>
                <p class="small mb-0 text-muted">
                  {{ attachmentDescription(attachment) }}
                </p>
              </div>
              <button
                type="button"
                class="btn btn-link p-0"
                :disabled="!attachment.downloadUrl"
                @click="$emit('download-attachment', attachment)"
              >
                Télécharger
              </button>
            </article>
          </div>

          <div v-if="message.reactions && message.reactions.length" class="msg-reactions">
            <button
              v-for="reaction in message.reactions"
              :key="`${message.id}-${reaction.emoji}`"
              type="button"
              class="msg-reaction"
              :class="{ active: reaction.reacted }"
              @click="$emit('reaction-toggle', { message, emoji: reaction.emoji })"
              :disabled="isReactionPending(message.id, reaction.emoji)"
            >
              <span>{{ reaction.emoji }}</span>
              <span>{{ reaction.count }}</span>
            </button>
          </div>
          <p v-if="callFormatter('messageStatusDetail', message)" class="msg-bubble__note">
            <i class="bi bi-clock-history" aria-hidden="true"></i>
            <span>{{ callFormatter('messageStatusDetail', message) }}</span>
          </p>
        </template>
        <span v-if="copiedId === message.id" class="msg-bubble__copied">Copié</span>
      </article>

      <div v-if="loading" class="msg-thread__loading">Chargement…</div>
      <div v-else-if="!messages.length" class="msg-thread__empty text-muted">Aucun message</div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  loadingOlder: { type: Boolean, default: false },
  reactionPalette: { type: Array, default: () => [] },
  reactionPickerFor: { type: [String, Number, null], default: null },
  messageMenuOpen: { type: [String, Number, null], default: null },
  copiedId: { type: [String, Number, null], default: null },
  pinnedMessages: { type: Array, default: () => [] },
  formatters: { type: Object, default: () => ({}) },
  isReactionPending: { type: Function, default: () => false },
  isPinning: { type: Function, default: () => false },
})

const emit = defineEmits([
  'load-older',
  'select-pin',
  'toggle-reaction-picker',
  'toggle-message-menu',
  'reaction-select',
  'reaction-toggle',
  'pin',
  'reply',
  'forward',
  'edit',
  'delete',
  'copy',
  'download-attachment',
])

const threadEl = ref(null)
const NEAR_BOTTOM_PX = 120
const LOAD_MORE_THRESHOLD = 80

function bubbleClass(message) {
  return {
    me: message.sentByMe,
    system: message.isSystem,
    pinned: message.pinned,
    pending: message.localOnly,
  }
}

function isNearBottom() {
  const el = threadEl.value
  if (!el) return true
  const distance = el.scrollHeight - (el.scrollTop + el.clientHeight)
  return distance <= NEAR_BOTTOM_PX
}

async function scrollToBottom() {
  await nextTick()
  const el = threadEl.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

async function autoScrollIfNeeded() {
  if (isNearBottom()) {
    await scrollToBottom()
  }
}

function onScroll() {
  const el = threadEl.value
  if (!el) return
  if (el.scrollTop <= LOAD_MORE_THRESHOLD) {
    emit('load-older')
  }
}

function scrollToMessage(messageId) {
  const el = threadEl.value?.querySelector(`#message-${messageId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('msg-bubble--focus')
    setTimeout(() => el.classList.remove('msg-bubble--focus'), 1200)
  }
}

const defaultFormatters = {
  formatTime: (value) => new Date(value || Date.now()).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
  formatAbsolute: (value) => new Date(value || Date.now()).toLocaleString('fr-FR'),
  formatFileSize: (bytes) => {
    if (!bytes && bytes !== 0) return '—'
    const units = ['o', 'Ko', 'Mo', 'Go']
    let size = bytes
    let unit = 0
    while (size >= 1024 && unit < units.length - 1) {
      size /= 1024
      unit += 1
    }
    return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[unit]}`
  },
  messageStatusLabel: () => '',
  messageStatusClass: () => '',
  messageStatusDetail: () => '',
  messageSecurityLabel: () => '',
  messageSecurityTooltip: () => '',
}

function callFormatter(name, ...args) {
  const fn = props.formatters?.[name]
  if (typeof fn === 'function') {
    return fn(...args)
  }
  const fallback = defaultFormatters[name]
  return typeof fallback === 'function' ? fallback(...args) : ''
}

const ATTACHMENT_TYPE_META = [
  {
    label: 'Document PDF',
    icon: 'bi bi-filetype-pdf',
    match: (type, name) => type.includes('pdf') || name.endsWith('.pdf'),
  },
  {
    label: 'Document Word',
    icon: 'bi bi-filetype-docx',
    match: (type, name) => type.includes('word') || name.endsWith('.doc') || name.endsWith('.docx'),
  },
  {
    label: 'Classeur Excel',
    icon: 'bi bi-filetype-xlsx',
    match: (type, name) => type.includes('sheet') || name.endsWith('.xls') || name.endsWith('.xlsx'),
  },
  {
    label: 'Présentation',
    icon: 'bi bi-filetype-ppt',
    match: (type, name) => type.includes('presentation') || name.endsWith('.ppt') || name.endsWith('.pptx'),
  },
  {
    label: 'Image',
    icon: 'bi bi-file-image',
    match: (type, name) => type.startsWith('image/') || /\.(png|jpe?g|gif|webp)$/i.test(name),
  },
  {
    label: 'Archive',
    icon: 'bi bi-file-zip',
    match: (type, name) => type.includes('zip') || /\.(zip|rar|7z|tar|gz)$/i.test(name),
  },
  {
    label: 'Texte',
    icon: 'bi bi-file-text',
    match: (type, name) => type.includes('text') || name.endsWith('.txt'),
  },
  {
    label: 'Vidéo',
    icon: 'bi bi-file-earmark-play',
    match: (type, name) => type.startsWith('video/') || /\.(mp4|mov|avi|mkv)$/i.test(name),
  },
]

function attachmentMeta(attachment) {
  const type = String(attachment?.mimeType || '').toLowerCase()
  const name = String(attachment?.fileName || '').toLowerCase()
  const meta = ATTACHMENT_TYPE_META.find((entry) => entry.match(type, name))
  return meta || { label: attachment?.mimeType || 'Fichier', icon: 'bi bi-paperclip' }
}

function attachmentIconClass(attachment) {
  return attachmentMeta(attachment).icon
}

function attachmentDescription(attachment) {
  const meta = attachmentMeta(attachment)
  const size = callFormatter('formatFileSize', attachment.sizeBytes)
  return size ? `${meta.label} · ${size}` : meta.label
}

onMounted(scrollToBottom)

watch(
  () => props.messages,
  async () => {
    await autoScrollIfNeeded()
  },
  { deep: true },
)

watch(
  () => props.loading,
  async () => {
    if (!props.loading) {
      await autoScrollIfNeeded()
    }
  },
)

defineExpose({ scrollToBottom, scrollToMessage })
</script>

<style src="@/assets/styles/messages.css"></style>



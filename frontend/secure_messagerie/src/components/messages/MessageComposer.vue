<template>
  <form @submit.prevent="handleSubmit" class="chat-input px-3 py-2">
    <div class="input-group">
      <!-- Mono-ligne -->
      <input
        v-if="!multiline"
        ref="inputEl"
        v-model="text"
        type="text"
        class="form-control"
        :placeholder="placeholder"
        :disabled="disabled || sending"
        :maxlength="maxLength || null"
        :aria-label="ariaLabel"
        autocomplete="off"
        @keydown.enter.exact.prevent="handleSubmit"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @compositionstart="onCompositionStart"
        @compositionend="onCompositionEnd"
      />

      <!-- Multiligne -->
      <textarea
        v-else
        ref="inputEl"
        v-model="text"
        class="form-control"
        :rows="rows"
        :placeholder="placeholder"
        :disabled="disabled || sending"
        :maxlength="maxLength || null"
        :aria-label="ariaLabel"
        autocomplete="off"
        @keydown.enter.exact="onEnterInTextarea"
        @keydown.enter.ctrl.exact.prevent="handleSubmit"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @compositionstart="onCompositionStart"
        @compositionend="onCompositionEnd"
      ></textarea>

      <button
        class="btn btn-primary"
        type="submit"
        :disabled="disabled || sending || !textTrimmed"
        :title="sendTitle"
        :aria-label="sendTitle"
      >
        <i class="bi bi-send" aria-hidden="true"></i>
      </button>
    </div>
  </form>
</template>

<script setup>
import { onMounted, ref, watch, computed, nextTick, defineExpose } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: 'Ã‰crire un messageâ€¦' },
  autofocus: { type: Boolean, default: false },
  maxLength: { type: Number, default: 0 }, // 0 = illimitÃ©
  multiline: { type: Boolean, default: false },
  rows: { type: Number, default: 2 },
  ariaLabel: { type: String, default: 'Zone de saisie du message' },
})

/**
 * Ã‰vÃ©nements Ã©mis :
 * - send: string
 * - typing-start
 * - typing-stop
 */
const emit = defineEmits(['send', 'typing-start', 'typing-stop', 'update:modelValue'])

const text = ref(props.modelValue)
const sending = ref(false)
const composing = ref(false)
const inputEl = ref(null)
let lastSubmitTs = 0

/* ----- Utils & labels ----- */
const textTrimmed = computed(() => text.value.trim())
const sendTitle = computed(() => (props.multiline ? 'Envoyer (Ctrl+EntrÃ©e)' : 'Envoyer (EntrÃ©e)'))

/* ----- Autofocus ----- */
onMounted(async () => {
  if (props.autofocus) {
    await nextTick()
    inputEl.value?.focus()
  }
})

/* ----- IME (composition) ----- */
function onCompositionStart() {
  composing.value = true
}
function onCompositionEnd() {
  composing.value = false
}

/* ----- Typing indicators (debounce) ----- */
let typingTimer = null
let hasSentTypingStart = false
const TYPING_IDLE_MS = 3000

function onInput() {
  emit('update:modelValue', text.value)
  // DÃ©lenche typing-start une seule fois tant quâ€™on tape
  if (!hasSentTypingStart && text.value) {
    emit('typing-start')
    hasSentTypingStart = true
  }
  // Reset du timer -> typing-stop aprÃ¨s inactivitÃ©
  clearTimeout(typingTimer)
  typingTimer = setTimeout(() => {
    if (hasSentTypingStart) {
      emit('typing-stop')
      hasSentTypingStart = false
    }
  }, TYPING_IDLE_MS)
}

function onFocus() {
  // rien de spÃ©cial ici, mais prÃªt si tu veux brancher autre chose
}

function onBlur() {
  // Stop typing si on sort du champ
  clearTimeout(typingTimer)
  if (hasSentTypingStart) {
    emit('typing-stop')
    hasSentTypingStart = false
  }
}

/* ----- Envoi ----- */
async function handleSubmit() {
  if (props.disabled || sending.value) return
  const payload = textTrimmed.value
  if (!payload) return
  // Ã©vite double envoi ultra-rapide
  const now = Date.now()
  if (now - lastSubmitTs < 300) return
  lastSubmitTs = now

  try {
    sending.value = true
    emit('send', payload)
    text.value = ''
    emit('update:modelValue', '')
  } finally {
    sending.value = false
    // Forcer typing-stop aprÃ¨s envoi
    clearTimeout(typingTimer)
    if (hasSentTypingStart) {
      emit('typing-stop')
      hasSentTypingStart = false
    }
  }
}

/* ----- Gestion Enter en multiligne ----- */
function onEnterInTextarea(e) {
  if (composing.value) return // ne pas casser lâ€™IME
  // En multiligne, Enter normal = nouvelle ligne (comportement natif)
  // donc on ne preventDefault pas ici.
  // Lâ€™envoi se fait via Ctrl+Enter (gÃ©rÃ© plus haut).
}

/* ----- Expose mÃ©thodes utiles ----- */
function focus() {
  inputEl.value?.focus()
}
function blur() {
  inputEl.value?.blur()
}
defineExpose({ focus, blur })

/* ----- SÃ©curitÃ© : si on disable, on sâ€™assure dâ€™envoyer typing-stop ----- */
watch(
  () => props.disabled,
  (v) => {
    if (v) {
      clearTimeout(typingTimer)
      if (hasSentTypingStart) {
        emit('typing-stop')
        hasSentTypingStart = false
      }
    }
  },
)

watch(
  () => props.modelValue,
  (value) => {
    if (value !== text.value) {
      text.value = value || ''
    }
  },
)
</script>

<style src="@/assets/styles/messages.css"></style>


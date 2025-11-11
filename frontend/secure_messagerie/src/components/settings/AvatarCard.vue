<template>
  <div class="card p-3 h-100">
    <h4 class="mb-3">Avatar</h4>

    <div class="avatar-settings d-flex align-items-center gap-3 mb-3">
      <div class="avatar-preview-wrapper">
        <img
          v-if="localAvatarUrl"
          :src="localAvatarUrl"
          alt="Avatar"
          class="avatar-preview"
        />
        <div v-else class="avatar-placeholder">
          {{ avatarInitials }}
        </div>
      </div>
      <div class="flex-grow-1">
        <div class="d-flex flex-wrap gap-2">
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            class="form-control form-control-sm avatar-input"
            @change="uploadAvatar"
            :disabled="loadingAvatar"
          />
          <button
            class="btn btn-sm btn-outline-danger"
            @click="deleteAvatar"
            :disabled="loadingAvatar || !localAvatarUrl"
          >
            <span v-if="loadingAvatar" class="spinner-border spinner-border-sm me-1"></span>
            Supprimer
          </button>
        </div>
        <p class="text-muted small mt-2 mb-0">
          PNG, JPG, WebP ou GIF • 512 px max • 2 MB max.
        </p>
      </div>
    </div>

    <div v-if="avatarMsg" :class="['alert mt-3', avatarOk ? 'alert-success' : 'alert-danger']">
      {{ avatarMsg }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '@/utils/api'

const props = defineProps({
  email: {
    type: String,
    default: '',
  },
  displayName: {
    type: String,
    default: '',
  },
  avatarUrl: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['avatar-updated'])

const loadingAvatar = ref(false)
const avatarMsg = ref('')
const avatarOk = ref(false)
const localAvatarUrl = ref(props.avatarUrl)

watch(
  () => props.avatarUrl,
  (val) => {
    localAvatarUrl.value = val
  },
)

const avatarInitials = computed(() => {
  const base = (props.displayName || '').trim() || (props.email || '').trim()
  if (!base) return 'SC'
  const parts = base
    .replace(/[_\-@.]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
  const initials = (parts[0]?.[0] || '') + (parts[1]?.[0] || '')
  const candidate = initials || parts[0]?.slice(0, 2) || base[0]
  return candidate.toUpperCase()
})

async function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  avatarMsg.value = ''
  avatarOk.value = false
  if (file.size > 2_000_000) {
    avatarMsg.value = 'Image trop volumineuse (max 2 MB).'
    return
  }
  loadingAvatar.value = true
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    const res = await api.post('/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const url = res.data.avatar_url ? `${res.data.avatar_url}?v=${Date.now()}` : null
    localAvatarUrl.value = url
    if (url) {
      localStorage.setItem('avatar_url', url)
    } else {
      localStorage.removeItem('avatar_url')
    }
    avatarOk.value = true
    avatarMsg.value = 'Avatar mis a jour.'
    emit('avatar-updated', url)
  } catch (e) {
    avatarOk.value = false
    avatarMsg.value =
      e.response?.data?.detail ||
      e.response?.data?.error ||
      "Impossible de televerser l'image."
  } finally {
    loadingAvatar.value = false
    event.target.value = ''
  }
}

async function deleteAvatar() {
  avatarMsg.value = ''
  avatarOk.value = false
  loadingAvatar.value = true
  try {
    await api.delete('/me/avatar')
    localAvatarUrl.value = null
    localStorage.removeItem('avatar_url')
    avatarOk.value = true
    avatarMsg.value = 'Avatar supprime.'
    emit('avatar-updated', null)
  } catch (e) {
    avatarOk.value = false
    avatarMsg.value =
      e.response?.data?.detail ||
      e.response?.data?.error ||
      'Suppression impossible pour le moment.'
  } finally {
    loadingAvatar.value = false
  }
}
</script>

<style scoped src="@/assets/styles/settings.css"></style>
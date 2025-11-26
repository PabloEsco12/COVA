<!--
  ===== Component Header =====
  Component: DangerZone
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Actions sensibles du compte (revoquer sessions, supprimer compte).
-->
<template>
  <div class="danger-zone p-3 border rounded-3">
    <h4 class="text-danger mb-2">
      <i class="bi bi-exclamation-triangle-fill me-1"></i> Zone dangereuse
    </h4>
    <p class="mb-3">
      Supprimer votre compte effacera définitivement vos données associées (conversations, messages liés, appareils, etc.).
      Cette action est irréversible.
    </p>
    <button class="btn btn-outline-danger" @click="openDeleteModal" :disabled="loadingDelete">
      <span v-if="loadingDelete" class="spinner-border spinner-border-sm me-2"></span>
      Supprimer mon compte
    </button>
    <div v-if="deleteError" class="alert alert-danger mt-3">{{ deleteError }}</div>

    <!-- modale -->
    <CustomModal v-model="showDeleteModal">
      <template #title>
        <span class="text-danger">
          <i class="bi bi-trash3-fill me-2"></i>Confirmer la suppression
        </span>
      </template>

      <p class="mb-3">
        Cette action est irréversible. Veuillez saisir votre mot de passe pour confirmer la suppression définitive de votre compte.
      </p>
      <input
        v-model="deletePassword"
        type="password"
        class="form-control"
        placeholder="Mot de passe"
        autocomplete="current-password"
      />
      <div v-if="deleteError" class="alert alert-danger mt-3">{{ deleteError }}</div>

      <template #footer>
        <button class="btn btn-secondary" @click="closeDeleteModal" :disabled="loadingDelete">
          Annuler
        </button>
        <button class="btn btn-danger" @click="confirmDelete" :disabled="!deletePassword || loadingDelete">
          <span v-if="loadingDelete" class="spinner-border spinner-border-sm me-2"></span>
          Supprimer définitivement
        </button>
      </template>
    </CustomModal>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/utils/api'
import { clearSession } from '@/services/auth'
import CustomModal from '@/components/ui/CustomModal.vue'

// ===== Etats locaux =====
const loadingDelete = ref(false)
const deleteError = ref('')
const showDeleteModal = ref(false)
const deletePassword = ref('')

const router = useRouter()

function openDeleteModal() {
  deleteError.value = ''
  deletePassword.value = ''
  showDeleteModal.value = true
}
function closeDeleteModal() {
  if (!loadingDelete.value) showDeleteModal.value = false
}

async function confirmDelete() {
  deleteError.value = ''
  loadingDelete.value = true
  try {
    await api.delete('/me', { data: { password: deletePassword.value } })
    clearSession()
    router.push('/login')
  } catch (e) {
    deleteError.value =
      e.response?.data?.detail || e.response?.data?.error || 'Suppression impossible pour le moment.'
  } finally {
    loadingDelete.value = false
  }
}
</script>

<style scoped src="@/assets/styles/settings.css"></style>

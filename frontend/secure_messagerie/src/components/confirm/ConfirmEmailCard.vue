<!-- src/components/confirm/ConfirmEmailCard.vue -->
<!-- ===== Carte de confirmation d'email ===== -->
<template>
  <div class="confirm-card animate__animated animate__fadeInDown">
    <!-- En-tete branding + accroche securite -->
    <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="confirm-logo" />
    <p class="confirm-eyebrow">Messagerie COVA</p>
    <h2 class="confirm-title">Validation de votre accès</h2>
    <p class="confirm-lead">
      Nous vérifions chaque lien pour garantir que vos conversations restent protégées.
    </p>

    <!-- Indicateur de chargement pendant l'appel API -->
    <Spinner v-if="loading" />

    <!-- Bloc principal success/erreur -->
    <div v-else>
      <div v-if="success" class="status-block status-block--success">
        <div class="status-block__icon">
          <i class="bi bi-shield-check"></i>
        </div>
        <div class="status-block__body">
          <p class="status-block__title">{{ success }}</p>
          <p class="status-block__text">{{ successSubtitle }}</p>
        </div>
      </div>

      <div v-else class="status-block status-block--error">
        <div class="status-block__icon">
          <i class="bi bi-exclamation-octagon"></i>
        </div>
        <div class="status-block__body">
          <p class="status-block__title">Impossible de confirmer ce lien</p>
          <p class="status-block__text">{{ error }}</p>
          <p class="status-block__hint">{{ errorHelp }}</p>
        </div>
      </div>

      <!-- Liens d'action post confirmation -->
      <div class="confirm-actions">
        <router-link
          v-if="success"
          to="/login"
          class="confirm-btn confirm-btn--primary"
        >
          Accéder à ma messagerie
        </router-link>
        <router-link
          v-else
          to="/register"
          class="confirm-btn confirm-btn--ghost"
        >
          Refaire une demande d'activation
        </router-link>
        <router-link to="/" class="confirm-secondary-link">
          Retourner à l'accueil COVA
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== Logique de validation du token de confirmation =====
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'
import { useRoute } from 'vue-router'
import Spinner from '@/components/confirm/Spinner.vue'

// ===== Etats reactivs =====
const route = useRoute()
const loading = ref(true)
const success = ref('')
const successSubtitle = ref('')
const error = ref('')
const errorHelp = ref('')

// ===== Verification du token a l'initialisation =====
onMounted(async () => {
  try {
    const res = await api.get(`/auth/confirm/${route.params.token}`)
    const apiMessage = (res.data?.message || '').trim()
    success.value = apiMessage || 'Votre adresse e-mail est confirmée.'
    successSubtitle.value =
      "Votre accès sécurisé est désormais actif. Vous pouvez vous connecter et échanger en toute confidentialité."
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error
    error.value = detail || err.message || 'Une erreur inconnue est survenue.'
    errorHelp.value =
      "Le lien peut avoir expiré ou avoir déjà été utilisé. Demandez un nouvel e-mail de confirmation depuis la page de connexion."
  } finally {
    loading.value = false
  }
})
</script>

<!-- ===== Styles du module de confirmation ===== -->
<style scoped src="@/assets/styles/confirm.css"></style>

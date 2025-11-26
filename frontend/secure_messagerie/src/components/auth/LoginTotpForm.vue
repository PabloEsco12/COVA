<!-- src/components/auth/LoginTotpForm.vue -->
<template>
  <!-- ===== Etape de verification TOTP apres saisie du mot de passe ===== -->
  <section class="auth-card">
    <!-- Bandeau rappel du contexte de verification -->
    <div class="auth-card__brand">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
      <div>
        <p class="auth-card__subtitle">Vérification requise</p>
        <h2 class="auth-card__title">Entrez votre code TOTP</h2>
      </div>
    </div>

    <!-- Rappel de l'adresse concernee pour eviter les erreurs de compte -->
    <div class="auth-context" v-if="userEmail">
      <i class="bi bi-envelope"></i>
      <span>{{ userEmail }}</span>
    </div>

    <!-- Formulaire de saisie et validation du code TOTP -->
    <form @submit.prevent="handleTotp" class="auth-form">
      <div class="input-field">
        <span class="input-field__icon"><i class="bi bi-shield-lock-fill"></i></span>
        <input
          v-model="code"
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="6"
          class="input-field__control"
          placeholder=" "
          autocomplete="one-time-code"
          required
        >
        <label class="input-field__label">Code TOTP</label>
        <small class="input-field__hint">
          Saisissez le code à 6 chiffres affiché par votre application.
        </small>
      </div>

      <button type="submit" class="btn-auth" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm"></span>
        <span v-else>Valider et continuer</span>
      </button>

      <button
        type="button"
        class="btn-auth-secondary"
        :disabled="loading"
        @click="cancelTotp"
      >
        Retour à la connexion
      </button>
    </form>

    <!-- Affichage des erreurs de code ou de serveur -->
    <div
      v-if="error"
      class="alert alert-danger text-center animate__animated animate__shakeX mt-3"
    >
      {{ error }}
    </div>
  </section>
</template>

<script setup>
// Formulaire TOTP appelé après un login/password réussi quand le compte exige 2FA.
import { onMounted, ref } from 'vue'
import { loginWithPassword, setPresenceStatus } from '@/services/auth'
import { useRouter } from 'vue-router'
import { backendBase } from '@/utils/api'
import { normalizeAvatarUrl } from '@/utils/profile'

// ===== Etats reactivs =====
const code = ref('')
const error = ref('')
const loading = ref(false)
const userEmail = ref('')
const router = useRouter()

// ===== Donnees temporaires issues du step password =====
const pendingKey = 'pending_totp'
let pendingAuth = null

// ===== Lifecycle: initialisation du contexte TOTP =====
onMounted(() => {
  // Récupère les credentials stockés lors du step password, sinon retour login.
  const raw = sessionStorage.getItem(pendingKey)
  if (!raw) {
    router.replace('/login')
    return
  }
  try {
    const parsed = JSON.parse(raw)
    if (!parsed?.email || !parsed?.password) {
      throw new Error('pending login missing data')
    }
    pendingAuth = parsed
    userEmail.value = parsed.email
  } catch {
    sessionStorage.removeItem(pendingKey)
    router.replace('/login')
  }
})

// ===== Flux de validation TOTP =====
async function handleTotp() {
  error.value = ''
  if (!pendingAuth) {
    router.replace('/login')
    return
  }

  const trimmed = code.value.trim()
  if (!trimmed || trimmed.length !== 6) {
    error.value = 'Veuillez indiquer un code TOTP valide.'
    return
  }

  loading.value = true
  try {
    const session = await loginWithPassword({
      email: pendingAuth.email,
      password: pendingAuth.password,
      totpCode: trimmed,
    })

    const user = session?.user || null
    const profile = user?.profile || null
    const displayName = profile?.display_name || user?.email || 'Utilisateur'

    if (displayName) {
      localStorage.setItem('pseudo', displayName)
    } else {
      localStorage.removeItem('pseudo')
    }
    const normalizedAvatar = normalizeAvatarUrl(profile?.avatar_url, {
      baseUrl: backendBase,
      cacheBust: true,
    })
    if (normalizedAvatar) {
      localStorage.setItem('avatar_url', normalizedAvatar)
    } else {
      localStorage.removeItem('avatar_url')
    }

    try {
      await setPresenceStatus('Disponible', 'available')
    } catch {}

    sessionStorage.removeItem(pendingKey)
    router.replace('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error
    if (typeof detail === 'string' && detail.trim()) {
      error.value = detail
    } else if (err.response?.data?.require_totp) {
      error.value = 'Code TOTP invalide. Réessayez avec le code le plus récent.'
      code.value = ''
    } else {
      error.value = 'Erreur inconnue, réessayez.'
    }
  } finally {
    loading.value = false
  }
}

// ===== Annulation de la verification =====
function cancelTotp() {
  sessionStorage.removeItem(pendingKey)
  router.push('/login')
}
</script>

<!-- ===== Styles du step TOTP ===== -->
<style scoped src="@/assets/styles/login-totp.css"></style>

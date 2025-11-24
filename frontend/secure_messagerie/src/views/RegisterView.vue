<!--
############################################################
# Vue : RegisterView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Page d'inscription affichant l'illustration + formulaire d'inscription.
############################################################
-->
<script setup>
import AuthIllustration from '@/components/auth/AuthIllustration.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
</script>

<template>
  <div class="auth-page signup-page">
    <!-- bulles décoratives -->
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <div class="auth-grid">
      <AuthIllustration />
      <RegisterForm />
    </div>
  </div>
</template>

<style scoped>
/* ici on laisse juste le minimal propre à la page */
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef3fc 0%, #dfe7f8 40%, #eaf6ff 100%);
  padding: 3.5rem 1.5rem;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

.signup-page::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(25, 89, 194, 0.14), transparent 45%),
    radial-gradient(circle at 70% 0%, rgba(90, 211, 245, 0.15), transparent 50%),
    radial-gradient(circle at 50% 100%, rgba(19, 72, 160, 0.12), transparent 55%);
  opacity: 0.8;
  z-index: 1;
}

.auth-orb {
  position: absolute;
  border-radius: 50%;
  opacity: 0.8;
  z-index: 0;
}

.orb-primary {
  width: 360px;
  height: 360px;
  top: -140px;
  right: -140px;
  background: radial-gradient(circle, rgba(25, 89, 194, 0.3) 0%, rgba(24, 60, 135, 0) 70%);
}

.orb-secondary {
  width: 300px;
  height: 300px;
  bottom: -160px;
  left: -120px;
  background: radial-gradient(circle, rgba(90, 211, 245, 0.32) 0%, rgba(90, 211, 245, 0) 70%);
}

.auth-grid {
  position: relative;
  z-index: 2;
  width: min(1120px, 100%);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2.5rem;
  align-items: stretch;
}

@media (max-width: 992px) {
  .auth-grid {
    grid-template-columns: 1fr;
  }
}
</style>


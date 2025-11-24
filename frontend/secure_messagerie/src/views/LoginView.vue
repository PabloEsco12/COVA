<!--
############################################################
# Vue : LoginView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Page de connexion principale avec illustration marketing + formulaire LoginForm.
# - La partie hero (gauche) est statique; la partie droite est le composant LoginForm.
############################################################
-->

<!-- Section principale -->
<template>
  <div class="auth-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <div class="auth-grid">
      <!-- partie gauche -->
      <section class="auth-illustration">
        <div class="auth-illustration__overlay"></div>
        <div class="auth-illustration__content">
          <div class="auth-badge">
            <i class="bi bi-shield-check me-2"></i>
            Messagerie souveraine
          </div>
          <h1>
            Collaborez en toute confiance avec
            <span class="brand-text">COVA</span>
          </h1>
          <p>
            Centralisez les échanges sensibles de votre organisation dans une interface
            moderne, sûre et pensée pour les équipes exigeantes.
          </p>
          <ul class="auth-feature-list">
            <li>
              <span class="feature-icon"><i class="bi bi-lock-fill"></i></span>
              Chiffrement de bout en bout et conformité RGPD.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-lightning-charge-fill"></i></span>
              Notifications en temps réel et canaux dédiés.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-people-fill"></i></span>
              Collaboration fluide entre équipes internes et partenaires.
            </li>
          </ul>
          <div class="auth-metrics">
            <div>
              <strong>+250</strong>
              <span>équipes actives</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>support dédié</span>
            </div>
          </div>
        </div>
      </section>

      <!-- partie droite = formulaire -->
      <LoginForm />
    </div>
  </div>
</template>

<script setup>
import LoginForm from '@/components/auth/LoginForm.vue'
</script>

<style scoped src="@/assets/styles/login.css"></style>

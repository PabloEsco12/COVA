<!--
############################################################
# Vue : LoginTotpView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Page pour le challenge TOTP apres login/password.
# - Monte LoginTotpForm et reprend l'identité depuis sessionStorage.
############################################################
-->
<template>
  <!-- Layout: fond d'authentification + colonne gauche marketing + formulaire TOTP -->
  <div class="auth-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <div class="auth-grid">
      <!-- colonne gauche : texte / features -->
      <section class="auth-illustration">
        <div class="auth-illustration__overlay"></div>
        <div class="auth-illustration__content">
          <div class="auth-badge">
            <i class="bi bi-shield-lock-fill me-2"></i>
            Vérification en deux étapes
          </div>
          <h1>
            Confirmez votre identité avec
            <span class="brand-text">COVA</span>
          </h1>
          <p>
            Saisissez le code généré par votre application d’authentification afin de finaliser la connexion.
          </p>
          <ul class="auth-feature-list">
            <li>
              <span class="feature-icon"><i class="bi bi-shield-check"></i></span>
              Protection additionnelle pour votre messagerie sécurisée.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-phone"></i></span>
              Codes disponibles sur votre application mobile ou desktop préférée.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-clock-history"></i></span>
              Chaque code expire rapidement, utilisez le plus récent.
            </li>
          </ul>
        </div>
      </section>

      <!-- colonne droite : formulaire totp -->
      <LoginTotpForm />
    </div>
  </div>
</template>

<script setup>
import LoginTotpForm from '@/components/auth/LoginTotpForm.vue'
</script>

<style scoped src="@/assets/styles/login-totp.css"></style>

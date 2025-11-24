<!-- src/views/NewPasswordView.vue -->
<template>
  <div class="reset-page">
    <div class="reset-decor">
      <span class="orb orb--one"></span>
      <span class="orb orb--two"></span>
      <span class="orb orb--three"></span>
    </div>

    <NewPasswordForm />
  </div>
</template>

<script setup>
import NewPasswordForm from '@/components/auth/NewPasswordForm.vue'
</script>

<style scoped src="@/assets/styles/new-password.css"></style>
<!--
############################################################
# Vue : NewPasswordView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Page de définition de nouveau mot de passe (token de reset).
############################################################
-->

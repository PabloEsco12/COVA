<!-- src/views/ConfirmEmailView.vue -->
<template>
  <!-- on laisse le fond ici -->
  <div class="confirm-bg">
    <ConfirmEmailCard />
  </div>
</template>

<script setup>
import ConfirmEmailCard from '@/components/confirm/ConfirmEmailCard.vue'
</script>

<!-- on importe ton css spécifique -->
<style scoped src="@/assets/styles/confirm.css"></style>
<!--
############################################################
# Vue : ConfirmEmailView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Affiche la confirmation d'email avec message de succès.
############################################################
-->

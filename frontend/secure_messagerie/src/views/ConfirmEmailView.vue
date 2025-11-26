<!-- src/views/ConfirmEmailView.vue -->
<!--
===== Vue Overview : ConfirmEmailView =====
- Role: affiche la carte de confirmation d'email apres inscription ou demande utilisateur.
- Layout: conteneur simple avec fond dedie pour aligner ConfirmEmailCard au centre de la page.
- Styles: importe confirm.css pour isoler la charte graphique de cette page specifique.
- Navigation: aucune logique ici; la carte gere seule les appels reseau et les messages a l'utilisateur.
-->
<template>
  <!-- Section principale: garde uniquement le fond et delegue l'affichage a la carte -->
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

<!--
===== Vue Overview : DevicesView =====
- Role: point d'entree de la vue appareils pour afficher la liste des sessions et actions de revocation.
- Composition: instancie uniquement DevicesPage qui gere appels API, etats de chargement et interactions.
- Routing: cible les utilisateurs depuis la section securite/parametres du dashboard.
- Styles: herites de DevicesPage; aucune feuille specifique ici pour limiter le bruit.
-->
<template>
  <DevicesPage />
</template>

<script setup>
import DevicesPage from '../components/devices/DevicesPage.vue'
</script>
<!--
############################################################
# Vue : DevicesView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Affiche la liste des appareils liés au compte.
############################################################
-->

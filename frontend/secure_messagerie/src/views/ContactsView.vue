<!--
===== Vue Overview : ContactsView =====
- Role: vue racine pour la gestion des contacts (listing, recherche, actions).
- Composition: se contente de monter ContactsPage qui encapsule toute la logique metier.
- Navigation: utilise le routeur pour acceder a cette page depuis le tableau de bord.
- Styles: relies via contacts.css pour conserver l'identite visuelle commune des contacts.
-->
<template>
  <ContactsPage />
</template>

<script setup>
import ContactsPage from '@/components/contacts/ContactsPage.vue'
</script>

<style src="@/assets/styles/contacts.css"></style>
<!--
############################################################
# Vue : ContactsView
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
# Description:
# - Page principale pour la gestion des contacts.
############################################################
-->

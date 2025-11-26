<!--
  ===== Component Header =====
  Component: SidebarPrimaryActions
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Actions principales (nouvelle conversation, invitation) dans la sidebar.
-->
<template>
  <section class="sidebar-actions mb-4">
    <button type="button" class="btn btn-primary w-100 mb-2" @click="$emit('start-conversation')">
      <i class="bi bi-pencil-square me-2"></i>
      Nouvelle conversation
    </button>
    <button type="button" class="btn btn-outline-primary w-100" @click="$emit('invite-contact')">
      <i class="bi bi-person-plus me-2"></i>
      Inviter un contact
    </button>
  </section>
</template>

<script setup>
// ===== Evenements emis =====
defineEmits(['start-conversation', 'invite-contact'])
</script>

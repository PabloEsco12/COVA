<template>
  <div class="msg-empty">
    <h3>Messagerie sécurisée</h3>
    <p>Choisissez une conversation ou créez-en une nouvelle avec vos contacts vérifiés.</p>
    <button class="btn btn-primary" type="button" @click="$emit('new')">
      Nouvelle conversation
    </button>
  </div>
</template>

<script setup>
defineEmits(['new'])
</script>

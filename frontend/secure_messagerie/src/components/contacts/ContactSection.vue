<!--
  ===== Component Header =====
  Component: ContactSection
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Regroupe et affiche une categorie de contacts.
-->
<template>
  <!-- Section listant une categorie de contacts -->
  <section
    v-show="section.contacts && section.contacts.length"
    class="contact-section"
  >
    <div class="section-heading">
      <div>
        <h5 class="mb-1">{{ section.title }}</h5>
        <p v-if="section.description" class="text-muted small mb-0">
          {{ section.description }}
        </p>
      </div>
      <span class="badge bg-secondary-subtle text-secondary-emphasis">
        {{ section.contacts.length }}
      </span>
    </div>

    <div class="contact-grid">
      <!-- on laisse le parent décider comment rendre chaque contact -->
      <slot
        v-for="contact in section.contacts"
        :key="contact.id"
        :contact="contact"
      />
    </div>
  </section>
</template>

<script setup>
// ===== Props du groupe de contacts =====
defineProps({
  section: {
    type: Object,
    required: true,
    // attendu : { key, title, description?, contacts: [...] }
  },
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

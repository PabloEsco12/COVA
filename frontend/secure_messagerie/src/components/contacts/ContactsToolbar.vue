<template>
  <div class="toolbar card mb-3">
    <div class="search-group">
      <i class="bi bi-search text-muted"></i>
      <input
        :value="searchTerm"
        type="search"
        class="form-control border-0"
        placeholder="Rechercher par nom, alias ou adresse e-mail"
        @input="$emit('update:search-term', $event.target.value.trim())"
      />
    </div>
    <div class="filter-group">
      <button
        v-for="chip in filterChips"
        :key="chip.value"
        class="filter-chip"
        :class="{ active: statusFilter === chip.value }"
        @click="$emit('update:status-filter', chip.value)"
      >
        <span>{{ chip.label }}</span>
        <span class="badge bg-light text-secondary">{{ chip.count }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  searchTerm: {
    type: String,
    required: true,
  },
  statusFilter: {
    type: String,
    required: true,
  },
  filterChips: {
    type: Array,
    required: true,
  },
})

defineEmits(['update:search-term', 'update:status-filter'])
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

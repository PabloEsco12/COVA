<template>
  <div class="availability-menu" ref="menuRef">
    <button
      type="button"
      class="availability-menu__trigger"
      :class="`status-${modelValue}`"
      @click="toggle"
      aria-haspopup="true"
      :aria-expanded="open"
    >
      <span class="status-dot"></span>
      <span class="label">{{ currentOption.label }}</span>
      <i class="bi bi-chevron-down ms-1"></i>
    </button>
    <ul v-if="open" class="availability-menu__list" role="listbox">
      <li
        v-for="option in options"
        :key="option.value"
      >
        <button type="button" @click="select(option.value)">
          <span class="status-dot" :class="`status-${option.value}`"></span>
          <span>{{ option.label }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: 'available' },
  options: {
    type: Array,
    default: () => [
      { value: 'available', label: 'Disponible' },
      { value: 'away', label: 'Absent' },
      { value: 'meeting', label: 'En réunion' },
      { value: 'busy', label: 'Occupé' },
      { value: 'dnd', label: 'Ne pas déranger' },
      { value: 'offline', label: 'Hors ligne' },
    ],
  },
})

const emit = defineEmits(['update:modelValue'])
const menuRef = ref(null)
const open = ref(false)

const currentOption = computed(() => {
  return props.options.find((opt) => opt.value === props.modelValue) || props.options[0]
})

function toggle() {
  open.value = !open.value
}

function select(value) {
  emit('update:modelValue', value)
  open.value = false
}

function onClickOutside(event) {
  if (!open.value) return
  if (menuRef.value && !menuRef.value.contains(event.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.availability-menu {
  position: relative;
}

.availability-menu__trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: 1px solid rgba(148, 163, 184, 0.5);
  border-radius: 999px;
  background: #fff;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  color: #0f172a;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.12);
}

.availability-menu__list {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 30;
  margin-top: 0.35rem;
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.2);
  padding: 0.35rem;
  list-style: none;
  min-width: 220px;
}

.availability-menu__list li + li {
  margin-top: 0.25rem;
}

.availability-menu__list button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: none;
  background: transparent;
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
}

.availability-menu__list button:hover,
.availability-menu__list button:focus-visible {
  background: rgba(59, 130, 246, 0.1);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-available .status-dot,
.status-dot.status-available {
  background: #22c55e;
}

.status-away .status-dot,
.status-dot.status-away {
  background: #facc15;
}

.status-meeting .status-dot,
.status-dot.status-meeting {
  background: #fb923c;
}

.status-busy .status-dot,
.status-dot.status-busy,
.status-dnd .status-dot,
.status-dot.status-dnd {
  background: #f87171;
}

.status-offline .status-dot,
.status-dot.status-offline {
  background: #94a3b8;
}
</style>


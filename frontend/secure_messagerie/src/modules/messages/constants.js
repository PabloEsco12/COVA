// ===== Module Header =====
// Module: messages/constants
// Author: Valentin Masurelle
// Date: 2025-11-26
// Role: Constantes (statuts, presets, options) réutilisées dans les composables/messages pour éviter les chaînes en dur.

export const PRESENCE_STALE_MS = 60000

export const STATUS_LABELS = {
  online: 'En ligne',
  available: 'Disponible',
  meeting: 'En réunion',
  busy: 'Occupé',
  dnd: 'Ne pas déranger',
  away: 'Absent',
  offline: 'Hors ligne',
}

export const STATUS_PRESETS = {
  available: { label: 'Disponible', message: 'Disponible' },
  away: { label: 'Absent', message: 'Absent' },
  meeting: { label: 'En réunion', message: 'En réunion' },
  busy: { label: 'Occupé', message: 'Occupé' },
  dnd: { label: 'Ne pas déranger', message: 'Ne pas déranger' },
  offline: { label: 'Hors ligne', message: '' },
}

export const availabilityOptions = [
  { value: 'available', label: 'Disponible' },
  { value: 'away', label: 'Absent' },
  { value: 'meeting', label: 'En réunion' },
  { value: 'busy', label: 'Occupé' },
  { value: 'dnd', label: 'Ne pas déranger' },
  { value: 'offline', label: 'Hors ligne' },
]

// ===== Module Header =====
// Module: messages/constants
// Author: Valentin Masurelle
// Date: 2025-11-26
// Role: Constantes (statuts, presets, options) réutilisées dans les composables/messages pour éviter les chaînes en dur.
// Notes:
//  - PRESENCE_STALE_MS borne la fraicheur des snapshots de présence avant fallback.
//  - STATUS_LABELS et STATUS_PRESETS garantissent des libellés cohérents dans toute l'UI.
//  - availabilityOptions sert directement aux listes déroulantes (aucune logique métier ici).

// ---- Délai pour considérer la présence obsolète ----
export const PRESENCE_STALE_MS = 60000

// ---- Labels normalisés pour les statuts de présence ----
export const STATUS_LABELS = {
  online: 'En ligne',
  available: 'Disponible',
  meeting: 'En réunion',
  busy: 'Occupé',
  dnd: 'Ne pas déranger',
  away: 'Absent',
  offline: 'Hors ligne',
}

// ---- Templates complets (libellé + message associé) ----
export const STATUS_PRESETS = {
  available: { label: 'Disponible', message: 'Disponible' },
  away: { label: 'Absent', message: 'Absent' },
  meeting: { label: 'En réunion', message: 'En réunion' },
  busy: { label: 'Occupé', message: 'Occupé' },
  dnd: { label: 'Ne pas déranger', message: 'Ne pas déranger' },
  offline: { label: 'Hors ligne', message: '' },
}

// ---- Liste d'options pour menus/radios de disponibilité ----
export const availabilityOptions = [
  { value: 'available', label: 'Disponible' },
  { value: 'away', label: 'Absent' },
  { value: 'meeting', label: 'En réunion' },
  { value: 'busy', label: 'Occupé' },
  { value: 'dnd', label: 'Ne pas déranger' },
  { value: 'offline', label: 'Hors ligne' },
]

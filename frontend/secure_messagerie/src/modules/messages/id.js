// ===== Module Header =====
// Module: messages/id
// Role: Generation d'identifiants locaux (UUID navigateur ou fallback).
// Usage: helper pur, utilisable dans les mappers/optimistic updates sans acces DOM.

// ---- Fabrique d'ID: UUID natif quand dispo, sinon prefix + random base36 ----
export function generateLocalId(prefix = 'msg') {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}

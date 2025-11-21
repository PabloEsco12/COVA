import { backendBase } from '@/utils/api'
import { detectGifLinks, stripGifLinks } from '@/utils/messageContent'
import { normalizeAvatarUrl } from '@/utils/profile'
import { generateLocalId } from '@/views/messages/id'

export function memberUserId(member) {
  if (!member) return null
  if (member.userId) return String(member.userId)
  if (member.user_id) return String(member.user_id)
  if (member.contact_user_id) return String(member.contact_user_id)
  return member.id ? String(member.id) : null
}

export function computeInitials(label = '') {
  if (!label) return 'C'
  const tokens = String(label)
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!tokens.length) return 'C'
  const first = tokens[0][0] || ''
  const second = tokens.length > 1 ? tokens[tokens.length - 1][0] : tokens[0][1] || ''
  const initials = (first + (second || '')).toUpperCase()
  return initials || 'C'
}

export function normalizeMember(member, { baseUrl = backendBase } = {}) {
  if (!member) return null
  const userId = member.user_id || member.userId || member.contact_user_id || null
  const membershipId = member.id || member.member_id || member.membership_id || userId
  if (!membershipId) return null
  const displayName = member.display_name || member.email || 'Membre'
  const avatarUrl = normalizeAvatarUrl(member.avatar_url || null, { baseUrl })
  return {
    id: String(membershipId),
    membershipId: membershipId ? String(membershipId) : null,
    userId: userId ? String(userId) : null,
    role: member.role || 'member',
    state: member.state || 'active',
    joinedAt: member.joined_at ? new Date(member.joined_at) : null,
    mutedUntil: member.muted_until ? new Date(member.muted_until) : null,
    displayName,
    email: member.email || '',
    avatarUrl,
    initials: computeInitials(displayName),
    statusMessage: member.status_message || '',
  }
}

export function normalizeConversation(payload, { selfId, baseUrl = backendBase } = {}) {
  if (!payload) return null
  const members = Array.isArray(payload.members)
    ? payload.members.map((member) => normalizeMember(member, { baseUrl })).filter(Boolean)
    : []
  const self = selfId ? String(selfId) : null
  const activeParticipants = members.filter((member) => {
    const userKey = memberUserId(member)
    return member.state === 'active' && (!self || userKey !== self)
  })
  const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
  let displayName = payload.title ? String(payload.title).trim() : ''
  if (!displayName) {
    const names = activeParticipants
      .map((member) => member.displayName || member.email)
      .filter(Boolean)
    displayName = names.join(', ')
  }
  if (!displayName) {
    displayName = members.length > 1 ? 'Conversation' : 'Nouvelle conversation'
  }
  let conversationAvatar = payload.avatar_url || null
  if (!conversationAvatar && payload.type === 'direct' && activeParticipants.length === 1) {
    conversationAvatar = activeParticipants[0]?.avatarUrl || null
  }
  const normalizedConversationAvatar = normalizeAvatarUrl(conversationAvatar, { baseUrl })
  return {
    id: String(payload.id),
    title: payload.title || null,
    topic: payload.topic || null,
    type: payload.type || 'group',
    archived: Boolean(payload.archived),
    createdAt,
    members,
    participants: activeParticipants,
    displayName,
    initials: computeInitials(displayName),
    avatarUrl: normalizedConversationAvatar,
    blockedByMe: Boolean(payload.blocked_by_viewer),
    blockedByOther: Boolean(payload.blocked_by_other),
  }
}

export function mapAttachmentPayload(raw) {
  if (!raw) return null
  return {
    id: String(raw.id || raw.attachment_id || generateLocalId()),
    fileName: raw.file_name || raw.filename || raw.name || 'Piece jointe',
    mimeType: raw.mime_type || raw.mimeType || null,
    sizeBytes: raw.size_bytes || raw.sizeBytes || null,
    sha256: raw.sha256 || null,
    downloadUrl: raw.download_url || raw.downloadUrl || null,
    encryption: raw.encryption || {},
  }
}

export function mapReferencePayload(raw) {
  if (!raw) return null
  return {
    id: String(raw.id || raw.message_id || generateLocalId()),
    authorDisplayName: raw.author_display_name || 'Participant',
    excerpt: raw.excerpt || '',
    createdAt: raw.created_at ? new Date(raw.created_at) : null,
    deleted: Boolean(raw.deleted),
    attachments: Number(raw.attachments || 0),
  }
}

export function normalizeMessage(payload, { selfId, baseUrl = backendBase } = {}) {
  const convId = String(payload.conversation_id || payload.conv_id || '')
  const authorId = payload.author_id ? String(payload.author_id) : null
  const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
  const displayName =
    payload.author_display_name || (authorId && selfId && authorId === String(selfId) ? 'Vous' : 'Participant')
  const content = (payload.content || '').toString()
  const gifLinks = detectGifLinks(content)
  const textWithoutGifs = stripGifLinks(content, gifLinks)
  const previewContent =
    gifLinks.length && !textWithoutGifs ? 'GIF partage' : textWithoutGifs || content
  const reactions = Array.isArray(payload.reactions)
    ? payload.reactions.map((reaction) => ({
        emoji: reaction.emoji,
        count: Number(reaction.count || 0),
        reacted: Boolean(reaction.reacted),
      }))
    : []
  const deliveredAt = payload.delivered_at ? new Date(payload.delivered_at) : null
  const readAt = payload.read_at ? new Date(payload.read_at) : null
  const pinnedAt = payload.pinned_at ? new Date(payload.pinned_at) : null
  const attachments = Array.isArray(payload.attachments)
    ? payload.attachments.map((attachment) => mapAttachmentPayload(attachment)).filter(Boolean)
    : []
  const editedAt = payload.edited_at ? new Date(payload.edited_at) : null
  const deletedAt = payload.deleted_at ? new Date(payload.deleted_at) : null
  const deleted = Boolean(payload.deleted)
  const replyTo = payload.reply_to ? mapReferencePayload(payload.reply_to) : null
  const forwardFrom = payload.forward_from ? mapReferencePayload(payload.forward_from) : null
  const streamPosition = Number(payload.stream_position ?? payload.streamPosition ?? null)
  const deliverySummaryRaw = payload.delivery_summary || {}
  const deliverySummary = {
    total: Number(deliverySummaryRaw.total || 0),
    delivered: Number(deliverySummaryRaw.delivered || 0),
    read: Number(deliverySummaryRaw.read || 0),
    pending: Number(deliverySummaryRaw.pending || 0),
  }
  return {
    id: String(payload.id || payload.message_id || generateLocalId()),
    conversationId: convId,
    authorId,
    displayName,
    avatarUrl: normalizeAvatarUrl(payload.author_avatar_url || null, { baseUrl }),
    content: deleted ? '' : content,
    createdAt,
    isSystem: Boolean(payload.is_system),
    sentByMe: Boolean(authorId && selfId && authorId === String(selfId)),
    deliveryState: payload.delivery_state || null,
    deliveredAt,
    readAt,
    reactions,
    pinned: Boolean(payload.pinned),
    pinnedAt,
    pinnedBy: payload.pinned_by ? String(payload.pinned_by) : null,
    security: {
      scheme: payload.encryption_scheme || 'confidentiel',
      metadata: payload.encryption_metadata || {},
    },
    preview: `${displayName}: ${previewContent || ''}`.trim(),
    attachments,
    editedAt,
    deletedAt,
    deleted,
    replyTo,
    forwardFrom,
    streamPosition,
    deliverySummary,
  }
}

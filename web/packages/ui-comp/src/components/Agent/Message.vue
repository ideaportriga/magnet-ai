<script setup lang="ts">
/**
 * Agent message bubble. Rewritten on `@ds` in Phase 4c — Pug → plain
 * template, all `<km-glyph>` replaced with inline SVG via `KmGlyph`, scoped
 * Stylus utility classes (`p-16`, `border-radius-12`) replaced with
 * `@ds` token-driven CSS. Public surface preserved: `message`, `reaction`,
 * `lastMessage`, `previewMode`, `isSelected`, `isDisabled`, `liveMode`,
 * `nextMessage`. Same emit list.
 */

import { computed, ref } from 'vue'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmInput from '@ds/components/domain/KmInput.vue'
import KmMarkdown from '@ds/components/domain/KmMarkdown.vue'
import AgentConfirmation from './Confirmation.vue'

interface AgentMessageData {
  id?: string
  role?: string
  content?: string
  created_at?: string | number
  action_call_requests?: unknown[]
  action_call_confirmations?: { confirmed: boolean }[]
  tool_call_id?: string
  tool_calls?: string
  feedback?: { type?: string }
  copied?: boolean
}

const props = withDefaults(
  defineProps<{
    message: AgentMessageData
    reaction?: string
    lastMessage?: boolean
    previewMode?: boolean
    isSelected?: boolean
    isDisabled?: boolean
    liveMode?: boolean
    nextMessage?: AgentMessageData | null
  }>(),
  { lastMessage: false, previewMode: false, isSelected: false, isDisabled: false, liveMode: false, nextMessage: null },
)

defineEmits<{
  copy: [id?: string]
  like: [id?: string]
  dislike: [id?: string]
  delete: [id?: string]
  save: [id?: string]
  focus: [id?: string]
  select: []
  confirm: [requests: unknown]
}>()

const hover = ref(false)
const editMode = ref(false)
const messageToEditContent = ref('')

const isUserMessage = computed(() => props.message.role === 'user')
const enableHoverSelection = computed(() => {
  if (isUserMessage.value || props.isSelected || props.previewMode || props.liveMode) return false
  return true
})
const backgroundClass = computed(() => (isUserMessage.value ? 'bg-agent-user-message' : 'bg-agent-message'))
const date = computed(() => {
  if (!props.message.created_at) return ''
  const dt = new Date(props.message.created_at)
  return `${dt.toLocaleDateString()} ${dt.toLocaleTimeString()}`
})
const showActions = computed(() => {
  if (props.message.role !== 'assistant' || !props.message.content) return false
  return hover.value || props.lastMessage
})

function isReacted(reaction: string) {
  if (props.message.feedback) return props.message.feedback.type === reaction
  return props.reaction === reaction
}
</script>

<template>
  <AgentConfirmation
    v-if="message.action_call_requests?.length"
    :message="message"
    :disabled="!lastMessage || (!liveMode && !previewMode)"
    :hover-enabled="enableHoverSelection"
    :is-selected="isSelected"
    :next-message="nextMessage"
    @confirm="$emit('confirm', $event)"
  />

  <div
    v-else
    class="agent-message"
    :class="{ 'agent-message--reverse': isUserMessage }"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <div
      class="agent-message__bubble"
      :class="[
        backgroundClass,
        {
          'agent-message__bubble--selected': isSelected,
          'agent-message__bubble--hover-select': enableHoverSelection && hover,
        },
      ]"
    >
      <div v-if="message.role === 'tool'" class="agent-message__tool-result">
        [Result for {{ message.tool_call_id }}]
      </div>

      <template v-if="message.content">
        <KmMarkdown v-if="!editMode" :source="message.content" class="agent-message__markdown" />
        <template v-else>
          <KmInput v-model="messageToEditContent" :rows="5" multiline class="agent-message__edit" />
          <div class="cluster gap-sm" data-justify="end">
            <button
              class="agent-message__icon-btn agent-message__icon-btn--clickable"
              type="button"
              aria-label="Save"
              @click="$emit('save', message.id)"
            >
              <KmGlyph name="save" size="12px" tone="brand" />
            </button>
            <button
              class="agent-message__icon-btn agent-message__icon-btn--clickable"
              type="button"
              aria-label="Cancel"
              @click="editMode = false"
            >
              <KmGlyph name="close" size="12px" tone="brand" />
            </button>
          </div>
        </template>
      </template>

      <template v-else-if="message.tool_calls">
        <pre class="agent-message__tool-calls">{{ message.tool_calls }}</pre>
      </template>

      <template v-else-if="message.action_call_confirmations">
        <div class="agent-message__confirmation-summary">
          <template v-if="message.action_call_confirmations.length > 1">
            {{ message.action_call_confirmations.filter((c) => c.confirmed).length }} of
            {{ message.action_call_confirmations.length }} confirmed
          </template>
          <template v-else>
            {{ message.action_call_confirmations[0]?.confirmed ? 'Confirmed' : 'Rejected' }}
          </template>
        </div>
      </template>
    </div>

    <div class="agent-message__footer cluster" data-justify="between" data-align="center">
      <span class="agent-message__date">{{ date }}</span>
      <div v-if="showActions && !previewMode" class="cluster gap-sm">
        <KmBtn
          v-if="isDisabled && hover && !isSelected"
          flat
          icon="copy"
          tone="subtle"
          label="View message details"
          icon-size="16px"
          size="xs"
          @click="$emit('select')"
        />
        <button
          v-if="!isDisabled || message.copied"
          class="agent-message__icon-btn"
          :class="{ 'agent-message__icon-btn--clickable': !isDisabled }"
          type="button"
          aria-label="Copy"
          @click="$emit('copy', message.id)"
        >
          <KmGlyph name="copy" size="16px" />
        </button>
        <button
          v-if="!isDisabled || isReacted('like')"
          class="agent-message__icon-btn"
          :class="{
            'agent-message__icon-btn--liked': isReacted('like'),
            'agent-message__icon-btn--clickable': !isDisabled,
          }"
          type="button"
          aria-label="Like"
          @click="$emit('like', message.id)"
        >
          <KmGlyph name="thumbs-up" size="16px" />
        </button>
        <button
          v-if="!isDisabled || isReacted('dislike')"
          class="agent-message__icon-btn"
          :class="{
            'agent-message__icon-btn--disliked': isReacted('dislike'),
            'agent-message__icon-btn--clickable': !isDisabled,
          }"
          type="button"
          aria-label="Dislike"
          @click="$emit('dislike', message.id)"
        >
          <KmGlyph name="thumbs-down" size="16px" />
        </button>
      </div>

      <div v-if="showActions && previewMode" class="cluster gap-sm">
        <button class="agent-message__icon-btn agent-message__icon-btn--clickable" type="button" @click="$emit('focus', message.id)">
          <KmGlyph name="bolt" size="12px" tone="brand" />
        </button>
        <button class="agent-message__icon-btn agent-message__icon-btn--clickable" type="button" @click="$emit('copy', message.id)">
          <KmGlyph name="copy" size="12px" tone="brand" />
        </button>
        <button class="agent-message__icon-btn agent-message__icon-btn--clickable" type="button" @click="$emit('delete', message.id)">
          <KmGlyph name="delete" size="12px" tone="brand" />
        </button>
        <button
          class="agent-message__icon-btn agent-message__icon-btn--clickable"
          type="button"
          @click="(editMode = !editMode), (messageToEditContent = message.content ?? '')"
        >
          <KmGlyph name="edit" size="12px" tone="brand" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-message { display: flex; flex-direction: column; }
.agent-message--reverse { flex-direction: column-reverse; align-items: flex-end; }

.agent-message__bubble {
  inline-size: 92%;
  padding: var(--ds-space-lg);
  border-radius: var(--ds-radius-xl);
  border: 1px solid transparent;
  box-sizing: border-box;
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.agent-message__bubble--selected { border-color: var(--ds-color-primary); }
.agent-message__bubble--hover-select { border-color: var(--ds-color-primary); cursor: pointer; }

.agent-message__tool-result { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); }
.agent-message__markdown { overflow-wrap: break-word; }
.agent-message__tool-calls { font-size: var(--ds-font-size-caption); white-space: pre-wrap; overflow-wrap: break-word; margin: 0; }
.agent-message__confirmation-summary { font-weight: var(--ds-font-weight-semibold); color: var(--ds-color-primary); overflow-wrap: break-word; }

.agent-message__footer { inline-size: 92%; block-size: 22px; padding: var(--ds-space-2xs) var(--ds-space-sm); }
.agent-message__date { font-size: var(--ds-font-size-xs); color: var(--ds-color-secondary-text); }

.agent-message__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 22px;
  block-size: 22px;
  padding: var(--ds-space-2xs);
  border-radius: var(--ds-radius-sm);
  background: transparent;
  border: 0;
  cursor: default;
}
.agent-message__icon-btn--clickable { cursor: pointer; }
.agent-message__icon-btn--clickable:hover { background: var(--ds-color-secondary-bg); }
.agent-message__icon-btn--liked { background: var(--ds-color-like-bg); }
.agent-message__icon-btn--disliked { background: var(--ds-color-dislike-bg); }
</style>

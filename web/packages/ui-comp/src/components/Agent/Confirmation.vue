<script setup lang="ts">
/**
 * Agent confirmation card — single-action or multi-action approval UI.
 * Rewritten on `@ds` in Phase 4c. Public API preserved (`message`,
 * `disabled`, `hoverEnabled`, `isSelected`, `nextMessage`, `t`).
 */

import { computed, ref, watch } from 'vue'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmCheckbox from '@ds/components/domain/KmCheckbox.vue'

const DEFAULT_T = {
  confirmAction: 'Confirm action',
  selectActions: 'Select actions to confirm',
  ofSelected: 'of ... selected',
  reject: 'Reject',
  confirm: 'Confirm',
  confirmChoice: 'Confirm choice',
}

interface ActionRequest { id: string; action_message: string }
interface ActionConfirmation { request_id: string; confirmed: boolean }
interface MessageWithRequests {
  action_call_requests?: ActionRequest[]
  created_at?: string | number
}

const props = withDefaults(
  defineProps<{
    message?: MessageWithRequests
    disabled?: boolean
    hoverEnabled?: boolean
    isSelected?: boolean
    nextMessage?: { action_call_confirmations?: ActionConfirmation[] } | null
    t?: Record<string, string>
  }>(),
  {
    message: () => ({} as MessageWithRequests),
    disabled: false,
    hoverEnabled: false,
    isSelected: false,
    nextMessage: null,
    t: () => ({}),
  },
)

const emit = defineEmits<{
  confirm: [confirmations: ActionConfirmation[]]
}>()

const hover = ref(false)
const confirm = ref<(string | null)[]>([])

const mergedT = computed(() => ({ ...DEFAULT_T, ...props.t }))
const requests = computed(() => props.message?.action_call_requests ?? [])
const multiple = computed(() => requests.value.length > 1)
const numberOfConfirmations = computed(() => confirm.value.filter(Boolean).length)
const date = computed(() => {
  if (!props.message?.created_at) return ''
  const dt = new Date(props.message.created_at)
  return `${dt.toLocaleDateString()} ${dt.toLocaleTimeString()}`
})

watch(
  requests,
  () => {
    if (!props.nextMessage) confirm.value = requests.value.map((r) => r.id)
  },
  { deep: true, immediate: true },
)

watch(
  () => props.nextMessage,
  () => {
    const confirmations = props.nextMessage?.action_call_confirmations
    if (!confirmations) return
    confirm.value = confirmations.map((c) => (c.confirmed ? c.request_id : null))
  },
  { deep: true, immediate: true },
)

function check(index: number, id: string) {
  if (confirm.value[index]) confirm.value[index] = null
  else confirm.value[index] = id
}

function confirmSelected() {
  if (!multiple.value) {
    emit('confirm', [{ request_id: requests.value[0]!.id, confirmed: true }])
    return
  }
  emit(
    'confirm',
    requests.value.map((request) => ({
      request_id: request.id,
      confirmed: confirm.value.includes(request.id),
    })),
  )
}

function cancel() {
  emit(
    'confirm',
    requests.value.map((r) => ({ request_id: r.id, confirmed: false })),
  )
}
</script>

<template>
  <div class="agent-confirmation" @mouseenter="hover = true" @mouseleave="hover = false">
    <div
      class="agent-confirmation__card"
      :class="{ 'agent-confirmation__card--hover': (hoverEnabled && hover) || isSelected }"
    >
      <header class="agent-confirmation__header">
        <span class="agent-confirmation__title">
          {{ !multiple ? mergedT.confirmAction : mergedT.selectActions }}
        </span>
      </header>

      <div class="agent-confirmation__body">
        <p v-if="!multiple" class="agent-confirmation__message">
          {{ requests[0]?.action_message }}
        </p>
        <div v-else class="stack" data-gap="sm">
          <KmCheckbox
            v-for="(request, index) in requests"
            :key="index"
            :model-value="!!confirm[index]"
            :display-text="request.action_message"
            :disable="disabled"
            @update:model-value="check(index, request.id)"
          />
        </div>
      </div>

      <footer v-if="!disabled" class="agent-confirmation__footer cluster gap-sm" data-justify="end" data-align="center">
        <span v-if="requests.length > 1" class="agent-confirmation__counter">
          {{ numberOfConfirmations }} {{ mergedT.ofSelected.replace('...', String(requests.length)) }}
        </span>
        <KmBtn
          v-else
          flat
          :label="mergedT.reject"
          tone="brand"
          :disable="disabled"
          @click="cancel"
        />
        <KmBtn
          :label="!multiple ? mergedT.confirm : mergedT.confirmChoice"
          :disable="disabled"
          @click="confirmSelected"
        />
      </footer>
    </div>

    <div class="agent-confirmation__meta cluster gap-sm" data-justify="between" data-align="center">
      <span class="agent-confirmation__date">{{ date }}</span>
      <div v-if="hoverEnabled && hover" class="cluster gap-sm">
        <KmBtn flat icon="copy" tone="subtle" label="View message details" icon-size="16px" size="xs" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-confirmation { display: flex; flex-direction: column; }

.agent-confirmation__card {
  border-radius: var(--ds-radius-xl);
  overflow: hidden;
  border: 1px solid var(--ds-color-border);
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
  cursor: pointer;
}
.agent-confirmation__card--hover { border-color: var(--ds-color-primary); }

.agent-confirmation__header {
  background: var(--ds-color-table-header);
  padding: var(--ds-space-sm) var(--ds-space-lg);
}
.agent-confirmation__title {
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-semibold);
  color: var(--ds-color-text-weak);
}

.agent-confirmation__body { padding: var(--ds-space-lg); }
.agent-confirmation__message { margin: 0; font-size: var(--ds-font-size-label); }

.agent-confirmation__footer { padding: 0 var(--ds-space-lg) var(--ds-space-lg); }
.agent-confirmation__counter { font-size: var(--ds-font-size-label); }

.agent-confirmation__meta {
  block-size: 22px;
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  margin-block-start: var(--ds-space-2xs);
}
.agent-confirmation__date {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-secondary-text);
}
</style>

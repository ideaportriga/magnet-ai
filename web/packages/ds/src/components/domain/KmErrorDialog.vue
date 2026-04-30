<script setup lang="ts">
/**
 * `<km-error-dialog>` — global error reporter used by the admin error
 * handler. Reads `appStore.errorMessage` (provided via `inject('appStore')`)
 * and renders a dialog with the message plus collapsible technical details
 * and a copy-to-clipboard button.
 */

import { computed, inject, onBeforeUnmount, ref } from 'vue'
import DsDialog from '../primitives/Dialog/DsDialog.vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmSeparator from './KmSeparator.vue'
import { copyToClipboard } from '../../utils/clipboard'

interface ErrorMessage {
  text?: string
  technicalError?: string
  stack?: string
}
interface AppStoreLike {
  errorMessage?: ErrorMessage | null
  setErrorMessage?: (value: ErrorMessage | null) => void
}

const DEFAULT_I18N = {
  error: 'Error',
  unexpectedError: 'An unexpected error occurred.',
  copied: 'Copied',
  copyError: 'Copy error',
  ok: 'OK',
}

const props = withDefaults(
  defineProps<{
    i18n?: Partial<typeof DEFAULT_I18N>
  }>(),
  {
    i18n: () => ({}),
  },
)

const i18n = computed(() => ({ ...DEFAULT_I18N, ...props.i18n }))

const appStore = inject<AppStoreLike | null>('appStore', null)

const visible = ref(true)
const showDetails = ref(false)
const copied = ref(false)
let copiedResetTimer: ReturnType<typeof setTimeout> | null = null

const errorMessage = computed<ErrorMessage>(() => appStore?.errorMessage ?? {})
const technicalError = computed(() => errorMessage.value.technicalError ?? '')
const text = computed(() => errorMessage.value.text ?? '')

function clearError() {
  appStore?.setErrorMessage?.(null)
  visible.value = false
}

async function copyError() {
  if (!technicalError.value) return
  try {
    await copyToClipboard(technicalError.value)
    copied.value = true
    if (copiedResetTimer) clearTimeout(copiedResetTimer)
    copiedResetTimer = setTimeout(() => {
      copied.value = false
      copiedResetTimer = null
    }, 1500)
  } catch {
    // Clipboard denied — leave the affordance unchanged.
  }
}

onBeforeUnmount(() => {
  if (copiedResetTimer) {
    clearTimeout(copiedResetTimer)
    copiedResetTimer = null
  }
})
</script>

<template>
  <DsDialog
    v-model:open="visible"
    size="md"
    :dismissible="false"
    data-test="km-error-dialog"
    @update:open="(v) => !v && clearError()"
  >
    <template #title>
      <span class="cluster gap-sm" data-align="center">
        <KmGlyph name="error" size="20px" tone="danger" />
        <span>{{ i18n.error }}</span>
      </span>
    </template>

    <KmSeparator />

    <div class="km-error-dialog__body stack" data-gap="md">
      <p v-if="text" class="km-error-dialog__message">{{ text }}</p>
      <p v-else class="km-error-dialog__message">{{ i18n.unexpectedError }}</p>

      <template v-if="technicalError">
        <button
          class="km-error-dialog__details-toggle cluster gap-sm"
          type="button"
          data-align="center"
          @click="showDetails = !showDetails"
        >
          <KmGlyph
            :name="showDetails ? 'chevron-down' : 'chevron-right'"
            size="12px"
            tone="muted"
          />
          <span class="km-error-dialog__details-label">Technical details</span>
        </button>

        <div v-if="showDetails" class="km-error-dialog__details">
          <pre>{{ technicalError }}</pre>
        </div>
      </template>
    </div>

    <KmSeparator />

    <template #footer>
      <KmBtn
        v-if="technicalError"
        flat
        :icon="copied ? 'check' : 'copy'"
        :label="copied ? i18n.copied : i18n.copyError"
        tone="weak"
        @click="copyError"
      />
      <KmBtn flat :label="i18n.ok" tone="brand" @click="clearError" />
    </template>
  </DsDialog>
</template>

<style>
.km-error-dialog__message {
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-black);
  margin: 0;
}
.km-error-dialog__details-toggle {
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
  color: var(--ds-color-text-grey);
  font: inherit;
}
.km-error-dialog__details-label {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
}
.km-error-dialog__details {
  padding: var(--ds-space-sm);
  background: var(--ds-color-light);
  border-radius: var(--ds-radius-sm);
  max-block-size: 200px;
  overflow: auto;
}
.km-error-dialog__details pre {
  font: var(--ds-font-size-caption) / 1.4 var(--ds-font-mono);
  color: var(--ds-color-text-weak);
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
</style>

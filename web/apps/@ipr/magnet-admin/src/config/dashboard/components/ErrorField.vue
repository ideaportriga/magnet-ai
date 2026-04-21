<template lang="pug">
template(v-if='row?.status === "error" && errorType')
  q-chip.km-small-chip(
    :color='chipColor',
    :text-color='chipTextColor',
    :label='chipLabel',
    :icon='chipIcon',
    style='text-transform: uppercase'
  )
    q-tooltip(:offset='[0, 10]', max-width='480px')
      .column.q-gap-4
        .km-heading-6 {{ errorType }}
        .km-field(v-if='errorMessage') {{ errorMessage }}
        .row.q-gap-8(v-if='errorSource || errorProvider')
          .column(v-if='errorSource')
            .km-input-label.text-text-grey Source
            .km-field {{ errorSource }}
          .column(v-if='errorProvider')
            .km-input-label.text-text-grey Provider
            .km-field {{ errorProvider }}
          .column(v-if='errorModel')
            .km-input-label.text-text-grey Model
            .km-field {{ errorModel }}
        .column(v-if='finishReason')
          .km-input-label.text-text-grey Finish reason
          .km-field {{ finishReason }}
        .column(v-if='retryAfter')
          .km-input-label.text-text-grey Retry after
          .km-field {{ retryAfter }} s
        .column(v-if='requestId')
          .km-input-label.text-text-grey Request ID
          .km-field.text-mono {{ requestId }}
template(v-else-if='row?.status === "error"')
  q-chip.km-small-chip(color='error-bg', text-color='error-text', label='ERROR')
</template>

<script>
import { defineComponent } from 'vue'

const GUARDRAIL_TYPES = new Set(['LLMGuardrailBlockedError'])
const EMPTY_TYPES = new Set([
  'LLMEmptyResponseError',
  'LLMTruncatedError',
])
const RATE_LIMIT_TYPES = new Set(['LLMRateLimitError'])

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    extra() {
      return this.row?.extra_data || {}
    },
    errorType() {
      return this.extra.error_type || null
    },
    errorMessage() {
      return this.extra.error_message || this.row?.status_message || null
    },
    errorSource() {
      return this.extra.error_source || null
    },
    errorProvider() {
      return this.extra.error_provider || null
    },
    errorModel() {
      return this.extra.error_model || null
    },
    finishReason() {
      return this.extra.error_finish_reason || this.extra.finish_reason || null
    },
    retryAfter() {
      return this.extra.error_retry_after ?? null
    },
    requestId() {
      return this.extra.error_request_id || null
    },
    chipLabel() {
      if (GUARDRAIL_TYPES.has(this.errorType)) return 'GUARDRAIL'
      if (RATE_LIMIT_TYPES.has(this.errorType)) return 'RATE LIMIT'
      if (EMPTY_TYPES.has(this.errorType)) return 'EMPTY'
      // Strip the LLM- prefix for compactness, keep the rest for clarity
      return (this.errorType || 'ERROR')
        .replace(/^LLM/, '')
        .replace(/Error$/, '')
        .toUpperCase()
    },
    chipIcon() {
      if (GUARDRAIL_TYPES.has(this.errorType)) return 'fa-solid fa-shield-halved'
      if (RATE_LIMIT_TYPES.has(this.errorType)) return 'fa-solid fa-gauge-high'
      if (EMPTY_TYPES.has(this.errorType)) return 'fa-solid fa-circle-exclamation'
      return 'fa-solid fa-triangle-exclamation'
    },
    chipColor() {
      if (GUARDRAIL_TYPES.has(this.errorType)) return 'orange-2'
      if (RATE_LIMIT_TYPES.has(this.errorType)) return 'yellow-3'
      return 'error-bg'
    },
    chipTextColor() {
      if (GUARDRAIL_TYPES.has(this.errorType)) return 'orange-9'
      if (RATE_LIMIT_TYPES.has(this.errorType)) return 'brown-9'
      return 'error-text'
    },
  },
})
</script>

<style scoped>
.text-mono {
  font-family: 'SFMono-Regular', ui-monospace, Menlo, Consolas, monospace;
  font-size: 11px;
}
</style>

<template lang="pug">
q-dialog(v-model='visible', persistent, @hide='clearError')
  q-card.error-dialog(style='min-width: 420px; max-width: 560px')
    //- Header
    q-card-section.row.items-center.q-pb-sm
      q-icon.q-mr-sm(name='fas fa-circle-exclamation', size='20px', color='negative')
      .km-heading-7.col {{ i18n.error }}
      q-btn(icon='close', flat, round, dense, size='sm', @click='visible = false')

    q-separator

    //- Body
    q-card-section
      .km-body.q-mb-sm(v-if='text') {{ text }}
      .km-body(v-else) {{ i18n.unexpectedError }}

      //- Technical details (collapsible)
      template(v-if='technicalError')
        .row.items-center.cursor-pointer.q-mt-md(@click='showDetails = !showDetails')
          q-icon(:name='showDetails ? "fas fa-chevron-down" : "fas fa-chevron-right"', size='12px', color='grey-7')
          .km-description.text-grey-7.q-ml-sm Technical details
        transition(name='slide')
          .q-mt-sm(v-if='showDetails')
            .error-details.q-pa-sm.rounded-borders
              pre.error-details-text.q-ma-none {{ technicalError }}

    q-separator

    //- Actions
    q-card-actions(align='right')
      q-btn.q-px-sm(
        v-if='technicalError',
        flat,
        no-caps,
        color='grey-7',
        size='sm',
        :icon='copied ? "fas fa-check" : "fas fa-copy"',
        :label='copied ? i18n.copied : i18n.copyError',
        @click='copyError'
      )
      q-space
      q-btn(flat, no-caps, color='primary', :label='i18n.ok', v-close-popup)
</template>

<script>
import { ref, inject } from 'vue'

const DEFAULT_I18N = {
  error: 'Error',
  unexpectedError: 'An unexpected error occurred.',
  copied: 'Copied',
  copyError: 'Copy error',
  ok: 'OK',
  errorReport: '--- Error Report ---',
  httpStatus: 'HTTP Status:',
  requestUrl: 'Request URL:',
  page: 'Page:',
  time: 'Time:',
  stackTrace: 'Stack Trace:',
  browser: 'Browser:',
}

export default {
  props: {
    i18n: {
      type: Object,
      default: () => ({ ...DEFAULT_I18N }),
    },
  },
  setup() {
    const appStore = inject('appStore', null)
    return {
      visible: ref(true),
      showDetails: ref(false),
      copied: ref(false),
      appStore,
    }
  },
  computed: {
    errorMessage() {
      return this.appStore?.errorMessage ?? {}
    },
    technicalError() {
      return this.errorMessage?.technicalError ?? ''
    },
    text() {
      return this.errorMessage?.text ?? ''
    },
  },
  beforeUnmount() {
    // Clear any pending copied-flag reset so setTimeout doesn't fire after
    // the dialog is torn down and try to mutate a vanished reactive.
    if (this._copiedResetTimer) {
      clearTimeout(this._copiedResetTimer)
      this._copiedResetTimer = null
    }
  },
  methods: {
    clearError() {
      this.appStore?.setErrorMessage(null)
      this.showDetails = false
      this.copied = false
      if (this._copiedResetTimer) {
        clearTimeout(this._copiedResetTimer)
        this._copiedResetTimer = null
      }
    },
    _resetCopiedLater() {
      if (this._copiedResetTimer) clearTimeout(this._copiedResetTimer)
      this._copiedResetTimer = setTimeout(() => {
        this.copied = false
        this._copiedResetTimer = null
      }, 2000)
    },
    async copyError() {
      const em = this.errorMessage || {}
      const lines = []
      lines.push(this.i18n.errorReport)
      if (this.text) lines.push(`Error: ${this.text}`)
      if (this.technicalError) lines.push(`Details: ${this.technicalError}`)
      if (em.statusCode) lines.push(`${this.i18n.httpStatus} ${em.statusCode}`)
      if (em.requestUrl) lines.push(`${this.i18n.requestUrl} ${em.requestUrl}`)
      lines.push(`${this.i18n.page} ${em.route || window.location.href}`)
      lines.push(`${this.i18n.time} ${em.timestamp || new Date().toISOString()}`)
      if (em.stack) lines.push(`\n${this.i18n.stackTrace}\n${em.stack}`)
      lines.push(`\n${this.i18n.browser} ${navigator.userAgent}`)

      try {
        await navigator.clipboard.writeText(lines.join('\n'))
        this.copied = true
        this._resetCopiedLater()
      } catch {
        // Fallback
        const textarea = document.createElement('textarea')
        textarea.value = lines.join('\n')
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        this.copied = true
        this._resetCopiedLater()
      }
    },
  },
}
</script>

<style lang="stylus" scoped>
.error-dialog
  border-radius var(--radius-lg, 12px)

.error-details
  background rgba(0, 0, 0, 0.04)
  border 1px solid rgba(0, 0, 0, 0.08)
  max-height 200px
  overflow auto

.error-details-text
  font-family 'SF Mono', Monaco, Menlo, monospace
  font-size 12px
  line-height 1.5
  color var(--q-secondary-text)
  white-space pre-wrap
  word-break break-all

.slide-enter-active, .slide-leave-active
  transition all 0.2s ease

.slide-enter-from, .slide-leave-to
  opacity 0
  max-height 0
</style>

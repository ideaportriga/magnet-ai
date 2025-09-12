<template lang="pug">
.row(@mouseenter='hover = true', @mouseleave='hover = false')
  .col-12.border-radius-12.overflow-hidden(
    :class='{ "ba-border": $theme === "default", "bg-agent-message": $theme !== "default", "ba-primary-important cursor-pointer": (hoverEnabled && hover) || isSelected }'
  )
    .row.q-px-16(:class='{ "bg-table-header q-py-8": $theme === "default", "q-pt-16": $theme !== "default" }')
      .km-title(:class='{ "text-text-weak": $theme === "default", "text-black": $theme !== "default" }') {{ !multiple ? 'Confirm action' : 'Select actions to confirm' }}
    .row.q-px-16.q-py-lg
      template(v-if='!multiple')
        .km-label {{ requests[0].action_message }}
      template(v-else)
        .column.q-gap-8
          template(v-for='(request, index) in requests', :key='index')
            km-checkbox(
              :label='request.action_message',
              :model-value='!!confirm[index]',
              @update:model-value='check(index, request.id)',
              size='42px',
              :disable='disabled'
            )
    .row.q-px-16.q-gap-8.q-pb-16(v-if='!disabled')
      .col
      .col-auto.flex.items-center.justify-center
        template(v-if='requests.length > 1')
          .km-label {{ numberOfConfirmations }} of {{ requests.length }} selected
        template(v-else)
          km-btn(flat, label='Reject', color='primary', @click='cancel', :disable='disabled')
      .col-auto
        km-btn(:label='!multiple ? "Confirm" : "Confirm choice"', @click='confirmSelected', :disable='disabled')
  .row.q-px-8.q-gap-8.items-center.justify-between.full-width.q-mt-4(style='height: 22px')
    .km-field.text-secondary-text {{ date }}
    .row.q-gap-8(v-if='hoverEnabled && hover')
      km-btn(flat, icon='fa fa-copy', color='secondary-text', labelClass='km-button-text', label='View message details', iconSize='16px', size='xs')
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    message: {
      type: Object,
      default: () => ({}),
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    hoverEnabled: {
      type: Boolean,
      default: false,
    },
    isSelected: {
      type: Boolean,
      default: false,
    },
    nextMessage: {
      type: Object,
      default: null,
    },
  },
  emits: ['confirm'],

  setup() {
    const hover = ref(false)
    return {
      hover,
      confirm: ref([]),
    }
  },

  computed: {
    requests() {
      return this.message?.action_call_requests || []
    },
    multiple() {
      return this.requests?.length > 1
    },
    numberOfConfirmations() {
      const selected = this.confirm.filter((item) => item)
      return selected.length
    },
    date() {
      if (!this.message.created_at) return ''
      const dateObject = new Date(this.message.created_at)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
  watch: {
    requests: {
      handler() {
        if (!this.nextMessage) {
          this.confirm = this.requests?.map((request) => request.id)
        }
      },
      deep: true,
      immediate: true,
    },
    nextMessage: {
      handler() {
        if (!this.nextMessage?.action_call_confirmations) return
        this.confirm = this.nextMessage?.action_call_confirmations?.map((request) => {
          if (request.confirmed) {
            return request.request_id
          }
          return null
        })
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    check(index, id) {
      if (this.confirm[index]) {
        this.confirm[index] = null
      } else {
        this.confirm[index] = id
      }
    },
    confirmSelected() {
      if (!this.multiple) {
        this.$emit('confirm', [{ request_id: this.requests[0].id, confirmed: true, comment: null }])
      } else {
        const selected = this.requests.map((request, index) => {
          if (this.confirm.includes(request.id)) {
            return {
              request_id: request.id,
              confirmed: true,
              comment: null,
            }
          }
          return {
            request_id: request.id,
            confirmed: false,
            comment: null,
          }
        })
        this.$emit('confirm', selected)
      }
    },
    cancel() {
      this.$emit(
        'confirm',
        this.requests.map((request) => ({
          request_id: request.id,
          confirmed: false,
          comment: null,
        }))
      )
    },
  },
}
</script>
<style lang="stylus">
.q-checkbox__inner
  color: var(--q-text-black) !important
</style>

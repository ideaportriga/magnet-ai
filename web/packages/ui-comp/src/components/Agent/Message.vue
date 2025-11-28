<template lang="pug">
template(v-if='message.action_call_requests?.length > 0')
  agent-confirmation(
    :message='message',
    @confirm='$emit("confirm", $event)',
    :disabled='!lastMessage || (!liveMode && !previewMode)',
    :hoverEnabled='enableHoverSelection',
    :isSelected='isSelected',
    :nextMessage='nextMessage'
  )
template(v-else)
  .row(:class='{ reverse: isUserMessage }', @mouseenter='hover = true', @mouseleave='hover = false')
    .col-11.border-radius-12.q-pa-16.ba-transparent(
      :style='{ "box-sizing": "border-box", transition: "all 0.1s" }',
      :class='[backgroundColor, { "ba-primary": isSelected, "ba-transparent": !isSelected, "ba-primary cursor-pointer": enableHoverSelection && hover }]'
    )
      .row
        template(v-if='message.role === "tool"')
          .km-label [Result for {{ message.tool_call_id }}]

        template(v-if='!!message.content')
          template(v-if='!editMode')
            km-markdown(:source='message.content', style='overflow-wrap: break-word')
          template(v-else)
            km-input.bg-light.full-width(v-model='messageToEditContent', rows='5', type='textarea')
            .row.justify-end.q-mt-md.full-width
              q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
                name='fas fa-save',
                @click='$emit("save", message.id)',
                size='12px',
                color='primary'
              )
              q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
                name='fas fa-times',
                @click='editMode = false',
                size='12px',
                color='primary'
              )
        template(v-else-if='!!message.tool_calls')
          .km-label.text-pre-wrap(style='overflow-wrap: break-word') {{ message.tool_calls }}
        template(v-else-if='!!message.action_call_confirmations')
          template(v-if='message.action_call_confirmations.length > 1')
            .km-title.text-primary(style='overflow-wrap: break-word') {{ message.action_call_confirmations.filter((c) => c.confirmed).length }} of {{ message.action_call_confirmations.length }} confirmed
          template(v-else)
            .km-title.text-primary(style='overflow-wrap: break-word') {{ message.action_call_confirmations[0].confirmed ? 'Confirmed' : 'Rejected' }}

    .col-11.q-pt-4.q-px-8
      .row.justify-between.items-center(style='height: 22px')
        .km-field.text-secondary-text {{ date }}
        .row.q-gap-8(v-if='showActions && !previewMode')
          km-btn(
            flat,
            icon='fa fa-copy',
            color='secondary-text',
            labelClass='km-button-text',
            label='View message details',
            iconSize='16px',
            @click='$emit("select")',
            size='xs',
            v-if='isDisabled && hover && !isSelected'
          )
          km-icon.q-pa-4.border-radius-6(
            name='copy',
            @click='$emit("copy", message.id)',
            width='22px',
            height='22px',
            :class='{ "cursor-pointer hover-bg-secondary-bg": !isDisabled }',
            v-if='!isDisabled || message?.copied'
          ) 
          km-icon.q-pa-4.border-radius-6(
            name='like',
            @click='$emit("like", message.id)',
            width='22px',
            height='22px',
            :class='{ "bg-like-bg": isReacted("like"), "cursor-pointer hover-bg-secondary-bg": !isDisabled }',
            v-if='!isDisabled || isReacted("like")'
          ) 
          km-icon.q-pa-4.border-radius-6(
            name='dislike',
            @click='$emit("dislike", message.id)',
            width='22px',
            height='22px',
            :class='{ "bg-dislike-bg": isReacted("dislike"), "cursor-pointer hover-bg-secondary-bg": !isDisabled }',
            v-if='!isDisabled || isReacted("dislike")'
          )
        .row.q-gap-8(v-if='showActions && previewMode')
          q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
            name='fas fa-bolt',
            @click='$emit("focus", message.id)',
            size='12px',
            color='primary'
          )
          q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
            name='fas fa-copy',
            @click='$emit("copy", message.id)',
            size='12px',
            color='primary'
          )
          q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
            name='fas fa-trash',
            @click='$emit("delete", message.id)',
            size='12px',
            color='primary'
          )
          q-icon.cursor-pointer.hover-bg-secondary-bg.border-radius-6.q-pa-4(
            name='fas fa-pencil',
            @click='(editMode = !editMode), (messageToEditContent = message.content)',
            size='12px',
            color='primary'
          )
</template>
<script>
import { ref } from 'vue'
export default {
  props: ['message', 'reaction', 'lastMessage', 'previewMode', 'isSelected', 'isDisabled', 'liveMode', 'nextMessage'],
  emits: ['copy', 'like', 'dislike', 'delete', 'save', 'focus', 'select', 'confirm'],
  setup() {
    return {
      hover: ref(false),
      editMode: ref(false),
      messageToEditContent: ref(''),
    }
  },
  computed: {
    enableHoverSelection() {
      if (this.isUserMessage) return false
      if (this.isSelected) return false
      if (this.previewMode) return false
      if (this.liveMode) return false
      return true
    },
    isUserMessage() {
      return this.message.role === 'user' //&& !this.message.action_call_confirmations?.length
    },
    backgroundColor() {
      if (this.isUserMessage) {
        return 'bg-agent-user-message'
      }
      return 'bg-agent-message'
    },
    date() {
      if (!this.message.created_at) return ''
      const dateObject = new Date(this.message.created_at)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
    showActions() {
      if (this.message.role != 'assistant') return false
      if (!this.message.content) return false
      if (this.hover) return true
      if (this.lastMessage) return true
      return false
    },
  },
  methods: {
    isReacted(reaction) {
      if (this.message.feedback) {
        return this.message.feedback.type === reaction
      }
      return this.reaction === reaction
    },
  },
}
</script>

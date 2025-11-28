<template lang="pug">
.row.items-center.q-pa-16.justify-between.bt-border.relative.full-width(style='z-index: 10')
  .col
  .col-auto
  km-btn.self-end(
    label='Close conversation',
    :disable='conversation?.status === "Closed" || loading',
    @click='close',
    color='primary',
    bg='background',
    iconSize='16px'
  ).
q-inner-loading(:showing='loading')
</template>

<script>
import { ref } from 'vue'
export default {
  name: 'ConversationHeader',
  setup() {
    const loading = ref(false)
    return {
      loading,
    }
  },
  computed: {
    conversation() {
      return this.$store.getters.conversation
    },
  },
  methods: {
    async close() {
      if (this.conversation?.status === 'closed' || this.loading) return
      this.loading = true
      try {
        await this.$store.dispatch('postProcessConversation', {
          conversation_id: this.conversation.id,
        })
        await this.$store.dispatch('getConversation', {
          conversation_id: this.conversation.id,
        })
      } catch (e) {
        this.loading = false
        throw e
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

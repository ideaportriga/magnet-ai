<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ conversation?.name }}
</template>

<script>
import { useConversationStore } from '@/stores/conversationStore'
import { m } from '@/paraglide/messages'
import { storeToRefs } from 'pinia'
export default {
  name: 'ConversationHeader',
  setup() {
    const convStore = useConversationStore()
    const { conversation } = storeToRefs(convStore)
    return { conversation }
  },
}
</script>

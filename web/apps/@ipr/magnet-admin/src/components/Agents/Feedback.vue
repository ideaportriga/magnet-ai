<template>
  <div class="cluster" data-gap="lg" style="block-size: 40px">
    <km-icon-btn :tone="liked ? &quot;brand&quot; : undefined" icon="thumbs-up" icon-size="16px" @click="react($event, true)" />
    <km-icon-btn :tone="disliked ? &quot;brand&quot; : undefined" icon="thumbs-down" icon-size="16px" @click="react($event, false)" />
  </div>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
export default {
  props: {
    message: {
      type: Boolean,
      default: false,
    },
    reaction: {
      type: Boolean,
      default: null,
    },
    index: {
      type: Number,
      default: null,
    },
  },
  emits: ['react'],
  setup() {
    const feedbackModal = ref(false)
    const feedbackConfirmModal = ref(false)
    const comment = ref('')
    const reason = ref([])
    const reasonsList = ref([
      { label: m.feedback_notRelevant(), value: "It isn't relevant" },
      { label: m.feedback_notCorrect(), value: "It isn't correct" },
    ])
    return {
      m,
      feedbackModal,
      feedbackConfirmModal,
      comment,
      reason,
      reasonsList,
    }
  },
  computed: {
    liked() {
      if (typeof this.reaction != 'boolean') return false
      return this.reaction
    },
    disliked() {
      if (typeof this.reaction != 'boolean') return false
      return !this.reaction
    },
  },
  methods: {
    react(event, type) {
      event.stopPropagation()
      event.preventDefault()
      this.$emit('react', type)
    },
  },
}
</script>

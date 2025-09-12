<template lang="pug">
.row.q-gap-16.items-center(style='height: 40px')
  km-icon-btn(:color='`${liked ? "primary" : "icon"}`', icon='fas fa-thumbs-up', iconSize='16px', @click='react($event, true)')

  km-icon-btn(:color='`${disliked ? "primary" : "icon"}`', icon='fas fa-thumbs-down', iconSize='16px', @click='react($event, false)')
</template>

<script>
import { ref } from 'vue'
export default {
  setup() {
    const feedbackModal = ref(false)
    const feedbackConfirmModal = ref(false)
    const comment = ref('')
    const reason = ref([])
    const reasonsList = ref([
      { label: 'It isn’t relevant', value: 'It isn’t relevant' },
      { label: 'It isn’t correct', value: 'It isn’t correct' },
    ])
    return {
      feedbackModal,
      feedbackConfirmModal,
      comment,
      reason,
      reasonsList,
    }
  },
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

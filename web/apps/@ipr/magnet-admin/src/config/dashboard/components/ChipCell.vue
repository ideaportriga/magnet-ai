<template>
  <km-chip v-if="label" class="my-xs" :label="label" :tone="tone" round :class="textClass" />
</template>
<script>
export default {
  props: {
    row: {
      type: Object,
      required: true,
    },
    name: {
      type: String,
      default: '',
    },
    color: {
      type: String,
      default: 'in-progress',
    },
    textColor: {
      type: String,
      default: 'text-text-grey',
    },
  },
  computed: {
    tone() {
      const tones = {
        'like-bg': 'success',
        'dislike-bg': 'danger',
        'in-progress': 'neutral',
      }
      return tones[this.color] || 'neutral'
    },
    textClass() {
      return this.textColor
        .split(' ')
        .filter((className) => !['text-text-grey', 'text-like-text', 'text-error-text'].includes(className))
        .join(' ')
    },
    label() {
      if (!this.name) return ''
      const keys = this.name.split('.')
      let value = this.row
      for (const key of keys) {
        if (!value) return ''
        value = value[key]
      }
      return value
    },
  },
}
</script>

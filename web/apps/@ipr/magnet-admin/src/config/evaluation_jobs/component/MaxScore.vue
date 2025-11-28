<template lang="pug">
.column.items-center
  q-chip.km-small-chip.chip(:color='color', :text-color='textColor', :label='label')
  .km-field.text-left(v-if='label !== "Not rated"') {{ maxScoreToolVariant }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    maxScoreToolVariant() {
      return this.getVariantLabel(this.row?.max_score_tool?.tool?.variant_name) || ''
    },

    label() {
      if (this.averageScore === 'Not rated') return 'Not rated'
      return this.averageScore.toFixed(2)
    },
    averageScore() {
      return this.row?.max_score_tool.average_score || 'Not rated'
    },
    statusStyles() {
      if (this.averageScore > 4) {
        return { color: 'status-ready', textColor: 'status-ready-text' }
      } else if ((this.averageScore >= 3 && this.averageScore <= 4) || this.averageScore === 'Not rated') {
        return { color: 'in-progress', textColor: 'text-gray' }
      } else if (this.averageScore < 3) {
        return { color: 'error-bg', textColor: 'error-text' }
      }
      return null
    },
    color() {
      return this.statusStyles?.color || ''
    },
    textColor() {
      return this.statusStyles?.textColor || ''
    },
  },
  methods: {
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
  },
})
</script>

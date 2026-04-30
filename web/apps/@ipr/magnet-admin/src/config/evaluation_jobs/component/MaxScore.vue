<template>
  <div class="stack items-center" data-gap="0">
    <km-chip class="km-small-chip chip" :tone="tone" :label="label" />
    <div v-if="label !== &quot;Not rated&quot;" class="km-field text-left">{{ maxScoreToolVariant }}</div>
  </div>
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
    tone() {
      if (this.averageScore > 4) {
        return 'success'
      } else if ((this.averageScore >= 3 && this.averageScore <= 4) || this.averageScore === 'Not rated') {
        return 'neutral'
      } else if (this.averageScore < 3) {
        return 'danger'
      }
      return undefined
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

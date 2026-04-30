<template>
  <div class="cluster" data-gap="xs" data-wrap="no">
    <div ref="textEl" class="km-field text-left answer">
      {{ text }}
      <km-tooltip v-if="showTooltip" class="bg-white block-shadow km-description" self="top middle" :offset="[-50, -50]">
        <div class="text-secondary-text" style="max-inline-size: 400px">{{ text }}</div>
      </km-tooltip>
    </div>
  </div>
</template>
<script>
import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: ['row', 'name'],
  setup() {
    return {
      //showTooltip: ref(false),
      textEl: ref(null),
    }
  },
  computed: {
    text() {
      if (!this.name) return undefined
      const keys = this.name.split('.')
      let value = this.row
      for (const key of keys) {
        value = value?.[key]
      }
      return value
    },
    tooltipText() {
      return this.row?.extra_data?.[this.name]
    },
    showTooltip() {
      if (!this.tooltipText) return false
      return this.checkOverflow()
    },
  },
  methods: {
    checkOverflow() {
      if (this.textEl && this.tooltipText) {
        const el = this.textEl
        return el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight
      }
      return false
    },
  },
})
</script>
<style>
.answer {
  white-space: break-spaces;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
</style>

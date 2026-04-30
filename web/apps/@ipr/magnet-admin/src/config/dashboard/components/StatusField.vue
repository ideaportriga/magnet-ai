<template>
  <km-chip class="km-small-chip" :tone="tone" :label="row?.status" style="text-transform: uppercase">
    <km-tooltip v-if="row?.status_message" :offset="[0, 10]">
      <div class="cluster">
        <div class="flex-none mr-sm">
          <div class="km-field">{{ row?.status_message }}</div>
        </div>
      </div>
    </km-tooltip>
  </km-chip>
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
    tone() {
      switch (this.row?.status) {
        case 'success':
          return 'success'
        case 'error':
          return 'danger'
        default:
          return 'neutral'
      }
    },
  },
})
</script>

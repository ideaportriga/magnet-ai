<template>
  <pre class="cursor-pointer wrapped-text km-heading-1">{{ tool }}
    <km-tooltip :offset="[0, 10]">
      <div v-if="row?.tool?.system_name" class="cluster">
        <div class="flex-none mr-sm">
          <div class="km-field">System name:</div>
        </div>
        <div class="flex-none">
          <div class="km-heading-1">{{ row?.tool?.system_name }}</div>
        </div>
      </div>
      <div v-if="row?.tool?.description" class="cluster mt-xs">
        <div class="flex-none mr-sm">
          <div class="km-field">Description:</div>
        </div>
        <div class="flex-none">
          <div class="km-heading-1">{{ row?.tool?.description }}</div>
        </div>
      </div>
    </km-tooltip></pre>
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
    tool() {
      return this.row?.tool.name || ''
    },
  },
})
</script>

<style scoped>
.wrapped-text {
  white-space: pre-wrap;
  overflow-wrap: break-word;
}
</style>

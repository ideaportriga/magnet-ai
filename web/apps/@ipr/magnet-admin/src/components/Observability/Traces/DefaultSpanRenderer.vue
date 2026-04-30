<template>
  <template v-if="!value || computedType == &quot;none&quot;">
    <div class="stack">
      <div class="km-button-text bb-border pb-xs pl-sm">{{ label }}</div><span class="text-text-grey pt-sm ml-sm km-body-sm" style="font-style: italic">N/A</span>
    </div>
  </template>
  <template v-else-if="computedType == &quot;text&quot;">
    <div class="flex-none ba-border border-radius-8">
      <div class="cluster bb-border p-sm bg-light km-body-sm">{{ label ?? 'Content' }}</div>
      <div class="cluster p-sm km-body-sm" style="min-block-size: 30px; white-space: pre-wrap">{{ value }}</div>
    </div>
  </template>
  <template v-else-if="computedType == &quot;object&quot;">
    <div class="stack">
      <div class="km-button-text bb-border pb-xs pl-sm">{{ label }}</div>
      <div v-if="valueAsKVArray.length &gt; 0" class="stack pt-sm ml-sm" data-gap="md">
        <div v-for="[key, value] in valueAsKVArray" :key="key" class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ key }}</div>
          <div class="km-heading-2">{{ value }}</div>
        </div>
      </div>
    </div>
  </template>
  <template v-else-if="computedType == &quot;embedding-vector&quot;">
    <div class="flex-none ba-border border-radius-8">
      <div class="cluster bb-border p-sm bg-light km-body-sm">Vector</div>
      <div class="cluster p-sm km-tiny" style="min-block-size: 50px">{{ value }}</div>
    </div>
  </template>
  <template v-else>
    <km-input autogrow :model-value="formattedValue" border-radius="8px" height="36px" type="textarea" readonly />
  </template>
</template>

<script>
import { m } from '@/paraglide/messages'
export default {
  props: {
    label: {
      type: String,
      default: 'none',
    },
    value: {
      type: [Object, Array],
      default: null,
    },
  },
  computed: {
    computedType() {
      if (!this.value) return 'none'

      // Try to guess the type from the value
      if (Array.isArray(this.value)) {
        if (this.value.length === 0) return 'none'
        const firstItem = this.value[0]
        if (typeof firstItem === 'number') return 'embedding-vector'
        if (typeof firstItem === 'object' && 'content' in firstItem && 'role' in firstItem) return 'none'
        return 'documents'
      }

      if (typeof this.value === 'object') return 'object'

      return 'text'
    },
    valueAsKVArray() {
      return Object.entries(this.excludeEmptyFields(this.value))
    },
  },
  methods: {
    excludeEmptyFields(obj) {
      return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== null && v !== undefined && v !== ''))
    },
  },
}
</script>

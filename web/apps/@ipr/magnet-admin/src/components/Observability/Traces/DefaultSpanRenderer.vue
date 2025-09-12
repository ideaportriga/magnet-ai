<template lang="pug">
template(v-if='!value || computedType == "none"')
  .column
    .km-button-text.bb-border.q-pb-4.q-pl-sm {{ label }}
    span.text-text-grey.q-pt-sm.q-ml-sm(style='font-style: italic; font-size: 13px') N/A
template(v-else-if='computedType == "text"')
  .col-auto.ba-border.border-radius-8
    .row.bb-border.q-pa-sm.bg-light(style='font-size: 13px') {{ label ?? 'Content' }}
    .row.q-pa-sm(style='min-height: 30px; font-size: 13px; white-space: pre-wrap') {{ value }}
template(v-else-if='computedType == "object"')
  .column
    .km-button-text.bb-border.q-pb-4.q-pl-sm {{ label }}
    .column.q-gap-12.q-pt-sm.q-ml-sm(v-if='valueAsKVArray.length > 0')
      .column.q-gap-6(v-for='[key, value] in valueAsKVArray')
        .km-input-label.text-text-grey {{ key }}
        .km-heading-2 {{ value }}
template(v-else-if='computedType == "embedding-vector"')
  .col-auto.ba-border.border-radius-8
    .row.bb-border.q-pa-sm.bg-light(style='font-size: 13px') Vector
    .row.q-pa-sm(style='min-height: 50px; font-size: 10px') {{ value }}
template(v-else)
  km-input(autogrow, :model-value='formattedValue', border-radius='8px', height='36px', type='textarea', readonly)
</template>

<script>
export default {
  props: {
    type: String,
    label: String,
    value: null,
  },
  computed: {
    computedType() {
      if (this.type) return this.type.toLowerCase()
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

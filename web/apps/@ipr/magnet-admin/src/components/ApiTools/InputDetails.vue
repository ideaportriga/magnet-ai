<template lang="pug">
.column.fit
  .col.fit(v-if='selectedRow')
    .row.km-table-chip.km-small-chip.text-black {{ selectedRow.in }}
    .row.justify-between.q-pt-8
      .col-12.q-py-8
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
        km-input(:model-value='selectedRow.name', readonly)
      .col-12.q-py-8
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
        km-input(v-model='description', type='textarea', rows='1', autogrow)
      .row.q-gap-16.no-wrap.full-width
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type

          km-select.full-width(v-model='type', :options='["string", "number", "integer", "boolean", "array", "object"]')
        .col
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Format
          km-select.full-width(
            v-model='format',
            :options='formatOptions',
            :disable='formatOptions.length === 0',
            :disabled='formatOptions.length === 0'
          )
      .column.q-mt-16.full-width
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Enum values
        template(v-for='(item, index) in enum', :key='index')
          .row.q-gap-8.no-wrap
            km-input.q-mb-sm.full-width(:model-value='item', @update:model-value='(e) => setEnum(e, index)')
            km-btn(@click='removeEnum(index)', flat, icon='fas fa-trash', icon-size='14px')
      km-btn(label='Add', @click='newEnum("")', flat, icon='fas fa-plus', icon-size='14px')
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    selectedRow: {
      type: Object,
      required: true,
    },
  },
  setup() {
    return {
      list: ref([]),
    }
  },

  computed: {
    formatOptions() {
      if (this.type === 'integer') {
        return ['', 'int32', 'int64']
      }
      if (this.type === 'number') {
        return ['', 'float', 'double']
      }
      if (this.type === 'string') {
        return ['', 'date', 'date-time', 'password', 'byte', 'binary', 'email', 'uuid', 'uri', 'hostname', 'ipv4', 'ipv6']
      }
      return []
    },
    apiTool() {
      return this.$store.getters.toolByName(this.$route.params.name)
    },
    input: {
      get() {
        if (this.selectedRow && this.apiTool) {
          return this.apiTool?.parameters?.input?.properties[this.selectedRow.in].properties[this.selectedRow.name]
        }
        return {}
      },
    },
    description: {
      get() {
        return this.input?.description
      },
      set(value) {
        this.setInputProp(value, 'description')
      },
    },
    type: {
      get() {
        return this.input?.type
      },
      set(value) {
        this.setInputProp(value, 'type')
      },
    },
    format: {
      get() {
        return this.input?.format ?? ''
      },
      set(value) {
        this.setInputProp(value, 'format')
      },
    },
    enum: {
      get() {
        return this.input?.enum
      },
    },
  },
  watch: {
    type() {
      const hasFormat = Object.hasOwn(this.input, 'format')
      if (hasFormat) {
        this.format = ''
      }
    },
  },
  methods: {
    setInputProp(value, key) {
      // .parameters?.input?.properties[this.selectedRow.in].properties[this.selectedRow.name]
      const target = `parameters.input.properties.${this.selectedRow.in}.properties.${this.selectedRow.name}.${key}`
      this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: target, value })
    },
    newEnum(value) {
      const array = this.enum || []
      array.push(value)
      this.setInputProp(array, 'enum')
    },
    setEnum(value, index) {
      const array = this.enum || []
      array[index] = value
      this.setInputProp(array, 'enum')
    },
    removeEnum(index) {
      const array = this.enum
      array?.splice(index, 1)
      this.setInputProp(array, 'enum')
    },
  },
}
</script>

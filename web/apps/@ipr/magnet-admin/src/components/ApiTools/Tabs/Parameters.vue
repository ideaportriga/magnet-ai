<template lang="pug">
.full-width
  div(style='width: 300px')
    km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey Inputs
  km-table(:rows='filteredRows', row-key='name', :columns='columns', @selectRow='select($event)', :selected='selectedRow ? [selectedRow] : []')
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    apiTool: {
      type: Object,
      required: true,
    },
    selectedRow: {
      type: Object,
      required: false,
    },
  },
  emits: ['select'],
  setup() {
    return {
      searchString: ref(''),
    }
  },
  computed: {
    parameters() {
      return this.$store.getters.api_tool_variant?.value?.parameters?.input?.properties
    },
    rows() {
      if (!this.parameters) return []
      const rows = []
      Object.keys(this.parameters).forEach((key) => {
        const properties = this.parameters[key].properties
        if (!properties) return
        Object.keys(properties).forEach((property) => {
          rows.push({
            description: '-',
            ...properties[property],
            name: property,
            in: key,
          })
        })
      })
      return rows
    },
    columns() {
      return [
        {
          name: 'Name',
          field: 'name',
          label: 'Name',
          align: 'left',
          class: 'km-title text-secondary-text',
        },
        {
          name: 'Description',
          field: 'description',
          label: 'Description',
          align: 'left',
        },
        {
          name: 'In',
          field: 'in',
          label: 'In',
          align: 'left',
          class: 'km-small-chip text-black km-table-chip',
        },
      ]
    },
    filteredRows() {
      if (!this.searchString.length) return this.rows
      return this.rows.filter((row) => {
        return (
          row.name.toLowerCase().includes(this.searchString.toLowerCase()) ||
          row.description.toLowerCase().includes(this.searchString.toLowerCase()) ||
          row.in.toLowerCase().includes(this.searchString.toLowerCase())
        )
      })
    },
  },
  watch: {
    rows(newVal) {
      this.select(newVal[0])
    },
  },
  methods: {
    select(row) {
      this.$emit('select', row)
      this.$store.commit('set', { apiToolSelectedProperty: row })
    },
  },
}
</script>

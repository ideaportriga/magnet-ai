<template lang="pug">
.full-width
  div(style='width: 300px')
    km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey Inputs
  km-table(:rows='filteredRows', row-key='name', :columns='columns', @selectRow='select($event)', :selected='selectedRow ? [selectedRow] : []')
</template>
<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
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
    const { items: agentItems } = useChroma('api_tools')

    return {
      searchString: ref(''),
      agentItems,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.routeParams?.actionId)
    },
    tool_object: {
      get() {
        return this.agentItems.find((item) => item.system_name === this.action?.tool_system_name)
      },
    },
    activeVariant() {
      return this.tool_object?.variants?.find((variant) => variant.variant === this.tool_object?.active_variant)
    },
    parameters() {
      return this.activeVariant?.value?.parameters.input.properties
    },
    rows() {
      if (!this.parameters) return []
      const rows = []
      Object.keys(this.parameters).forEach((key) => {
        const properties = this.parameters[key].properties || {}
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

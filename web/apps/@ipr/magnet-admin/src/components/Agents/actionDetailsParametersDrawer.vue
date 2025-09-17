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
    const { items: apiServers } = useChroma('api_servers')
    const { items: mcpItems } = useChroma('mcp_servers')

    return {
      searchString: ref(''),
      apiServers,
      mcpItems,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    activeTopic: {
      get() {
        return this.$store.getters.activeTopic
      },
      set(value) {
        this.$store.commit('setActiveTopic', value)
      },
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.activeTopic?.action)
    },
    tool_object: {
      get() {
        if (this.action?.type === 'mcp_tool') {
          const server = this.mcpItems.find((item) => item.system_name === this.action?.tool_provider)
          return server?.tools?.find((tool) => tool.name === this.action?.tool_system_name)
        }
        const server = this.apiServers.find((item) => item.system_name === this.action?.tool_provider)
        return server?.tools?.find((item) => item.system_name === this.action?.tool_system_name)
      },
    },
    activeVariant() {
      if (this.action?.type === 'mcp_tool') return this.tool_object
      if (this.action?.type === 'api') return this.tool_object
      return this.tool_object?.variants?.find((variant) => variant.variant === this.tool_object?.active_variant)
    },
    parameters() {
      if (this.action?.type === 'mcp_tool') return this.tool_object?.inputSchema?.properties
      if (this.action?.type === 'api') return this.tool_object?.parameters?.input?.properties
      return this.activeVariant?.value?.parameters.input.properties
    },
    rows() {
      if (!this.parameters) return []
      const rows = []
      Object.keys(this.parameters).forEach((key) => {
        if (this.action?.type === 'mcp_tool') {
          rows.push(this.formatMCPRows(key))
        } else {
          rows.push(...this.formatApiRows(key))
        }
      })
      return rows
    },
    columns() {
      const columns = [
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
      ]
      if (this.action?.type === 'api') {
        columns.push({
          name: 'In',
          field: 'in',
          label: 'In',
          align: 'left',
          class: 'km-small-chip text-black km-table-chip',
        })
      }
      return columns
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
    formatApiRows(key) {
      const properties = this.parameters[key].properties || {}
      return Object.keys(properties).map((property) => {
        return {
          description: '-',
          ...properties[property],
          name: property,
          in: key,
        }
      })
    },
    formatMCPRows(key) {
      const properties = this.parameters[key] || {}
      return {
        description: '-',
        ...properties,
        name: key,
        // in: key,
      }
    },
    select(row) {
      this.$emit('select', row)
      this.$store.commit('set', { apiToolSelectedProperty: row })
    },
  },
}
</script>

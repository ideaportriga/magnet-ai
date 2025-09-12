<template lang="pug">
.row.q-mb-12
  .col-12
    km-filter-bar(v-model:config='currentFilter', v-model:filterObject='activeFilters', ref='filterRef')
    .column.q-gap-16.full-width
      km-table.q-mt-md(
        @selectRow='$emit("selectRow", $event)',
        selection='single',
        row-key='start_time',
        :rows='visibleRows',
        :selected='selectedRow ? [selectedRow] : []',
        :columns='agentDetailsColumns',
        :pagination='{ rowsPerPage: 10 }',
        @cellAction='cellAction'
      )
</template>
<script>
import { fetchData } from '@shared'
import agentDetailsControls from '@/config/dashboard/agent-details-table'

export default {
  props: ['selectedRow'],
  emits: ['selectRow'],
  data() {
    const store = this?.$store
    return {
      activeFilters: {},
      detailedList: [],
      agentDetailsControls,
      searchString: '',
      listFilter: {
        source: {
          label: 'Consumer type',
          key: 'source',
          type: 'component',
          options: [
            { label: 'Runtime API', value: 'Runtime API' },
            { label: 'Runtime AI App', value: 'Runtime AI App' },
            { label: 'Preview', value: 'preview' },
            { label: 'Evaluation', value: 'evaluation' },
          ],
          multiple: true,
          default: ['Runtime AI App', 'Runtime API'],
        },
        start_time: {
          label: 'Time Period',
          key: 'start_time',
          type: 'timePeriod',
          default: 'P1D',
          overviewFilter: true,
        },
      },
    }
  },
  computed: {
    visibleRows() {
      if (!this.searchString) return this.detailedList
      const searchTerms = this.searchString.includes(',')
        ? this.searchString
            .split(',')
            .map((term) => term.trim().toLowerCase())
            .filter((term) => term)
        : [this.searchString.toLowerCase()]
      const containsSearchTerm = (value) => {
        if (typeof value === 'string') {
          const lowerCaseVal = value.toLowerCase()
          return searchTerms.some((term) => lowerCaseVal.includes(term))
        }
        if (typeof value === 'object' && value !== null) {
          return Object.values(value).some(containsSearchTerm)
        }
        return false
      }
      return this.detailedList.filter((el) => Object.values(el).some(containsSearchTerm))
    },
    currentFilter: {
      get() {
        return this.listFilter
      },
      set(value) {
        this.listFilter = value
      },
    },
    agentDetailsColumns() {
      return Object.values(this.agentDetailsControls).filter((column) => column.display)
    },
    endpoint() {
      return this.$store.getters.config.api.aiBridge.urlAdmin
    },
  },
  watch: {
    activeFilters: {
      deep: true,
      handler() {
        this.getDetailedList()
      },
    },
  },
  methods: {
    async getDetailedList() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/agent/list',
        body: JSON.stringify({
          filters: { ...this.activeFilters, feature_system_name: { eq: this.$store.getters.agent_detail?.system_name } },
          limit: 100,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const data = await response.json()
      this.detailedList = data.items
    },
    cellAction(e) {},
  },
}
</script>
<style lang="stylus"></style>

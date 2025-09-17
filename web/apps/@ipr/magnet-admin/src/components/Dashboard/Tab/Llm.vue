<template lang="pug">
.row
  .col-auto.center-flex-y
    q-tabs.full-width.q-mb-16(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
  .col-12.q-my-16
    .row.items-center.q-gap-4.q-pb-4.justify-between
      .col-auto.center-flex-y
        km-filter-bar(v-model:config='currentFilter', v-model:filterObject='activeFilters', ref='filterRef')
  .col-12
    template(v-if='tab === "summary"')
      .km-grid-2
        dashboard-board-card(header='Usage & cost', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(label='Total requests', :value='data.totalRequests')
              dashboard-board-label-value(label='Avg. request cost', :value='data.avgRequestCost')
              dashboard-board-label-value(label='Total cost', :value='data.totalCost')
        dashboard-board-card(header='Performance', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(label='Avg. request latency', :value='data.avgRequestLatency')
              dashboard-board-label-value(label='Error rate', :value='data.errorRate')
      .km-grid-1.q-mt-16(v-if='activeFilters.model')
        dashboard-board-card(header='Consumer Requests')
          template(v-slot:body)
            .column.q-gap-16
              km-table
      .km-grid-1.q-mt-16(v-else)
        dashboard-board-card(header='Top request consumers')
          template(v-slot:body)
            .column.q-gap-16
              km-table(:columns='topColumns', :rows='top', :pagination='{ rowsPerPage: 10 }', @cellAction='cellAction')
    template(v-if='tab === "list"')
      .column.q-gap-16.full-width
        //- .row
        //-   //- .col-auto.center-flex-y
        //-   //-   km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
        //-   q-space

        km-table(
          selection='single',
          row-key='_id',
          :rows='detailedList',
          :columns='detailedColumns',
          v-model:pagination='pagination',
          @cellAction='cellAction',
          @request='getDetailedList',
          :selected='selectedRow ? [selectedRow] : []',
          dense,
          @selectRow='$emit("selectRow", $event)',
          :filter='activeFilters',
          :binary-state-sort='true'
        )
</template>

<script>
import { ref } from 'vue'
import filter from '@/config/dashboard/llm-filters'
import topControls from '@/config/dashboard/llm-table'
import { fetchData } from '@shared'
import { formatDuration } from '@shared/utils'
import llmDetailsControls from '@/config/dashboard/llm-details-table'

export default {
  props: {
    selectedRow: {
      type: Object,
      default: null,
    },
  },
  emits: ['selectRow'],
  data() {
    return {
      tab: ref('list'),
      tabs: ref([
        { name: 'list', label: 'List' },
        { name: 'summary', label: 'Summary' },
      ]),
      listFilter: ref(filter),
      summaryFilter: ref(Object.fromEntries(Object.entries(filter))),
      activeFilters: ref({}),
      observability: ref({}),
      detailedList: ref([]),
      top: ref([]),
      topControls: ref(topControls),
      pagination: ref({
        page: 1,
        rowsPerPage: 10,
        sortBy: 'start_time',
        descending: true,
      }),
      llmDetailsControls: ref(llmDetailsControls),
    }
  },
  computed: {
    detailedColumns() {
      return Object.values(this.llmDetailsControls).filter((control) => control.display)
    },
    topColumns() {
      return Object.values(this.topControls)
    },
    endpoint() {
      return this.$store.getters.config.api.aiBridge.urlAdmin
    },
    currentFilter: {
      get() {
        return this.tab === 'list' ? this.listFilter : this.summaryFilter
      },
      set(value) {
        this.tab === 'list' ? (this.listFilter = value) : (this.summaryFilter = value)
      },
    },
    data() {
      return {
        totalRequests: this.observability?.total_calls ?? '-',
        avgRequestCost: this.observability?.avg_cost ? `${this.observability.avg_cost.toFixed(6)} $` : '-',
        totalCost: this.observability?.total_cost ? `${this.observability.total_cost.toFixed(6)} $` : '-',
        avgRequestLatency: this.observability?.avg_latency ? `${formatDuration(this.observability.avg_latency)}` : '-',
        errorRate: this.observability?.error_rate || this.observability.error_rate === 0 ? `${this.observability.error_rate.toFixed(2)}%` : '-',
      }
    },
  },
  watch: {
    tab(newVal) {
      this.$emit('selectRow', false)
      if (newVal === 'overview') {
        // this.$refs.filterRef.clearFilter([])
      }
    },
    activeFilters: {
      deep: true,
      handler() {
        this.refresh()
      },
    },
  },
  methods: {
    cellAction(e) {
      if (e.action === 'drilldown') {
      } else if (e.action === 'select') {
        this.$emit('selectRow', e.row)
      } else if (e.action === 'filterLlm') {
        this.setFilter('consumer_name', { label: e.row.name, value: e.row.name })
        this.tab = 'list'
      }
    },
    setFilter(key, { label, value }) {
      this.$refs.filterRef.setFilter(key, { label, value })
    },
    refresh() {
      this.getObservability()
      this.getDetailedList()
      this.getTop()
      this.getOptions()
    },
    async getOptions() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/llm/options',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const data = await response.json()
      this.$store.dispatch('setLlmDashboardOptions', data)
    },
    async getTop() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/llm/top',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.ok) {
        await response.json().then((data) => {
          this.top = data
        })
      }
    },
    async getDetailedList(input) {
      console.log('input', input?.pagination?.sortBy, input?.pagination?.descending)
      const props = input?.pagination ?? this.pagination
      const body = {
        limit: props.rowsPerPage,
        sort: props.sortBy,
        order: props.descending ? -1 : 1,
        filters: this.activeFilters,
        fields: [],
        // exclude_fields: ['input', 'output'],
        offset: (props.page - 1) * props.rowsPerPage,
      }
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/llm/list',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const data = await response.json()
      if (data.items) {
        this.detailedList = data.items
      } else {
        this.detailedList = []
      }
      this.pagination.rowsNumber = data.total
      this.pagination.page = props.page ?? 1
      this.pagination.sortBy = props.sortBy ?? 'start_time'
      this.pagination.descending = props.descending ?? true
    },
    async getObservability() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/llm',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.ok) {
        await response.json().then((data) => {
          this.observability = data
        })
      }
    },
  },
}
</script>

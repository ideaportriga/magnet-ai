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
              km-data-table(:table='topTable', hide-pagination)
      .km-grid-1.q-mt-16(v-else)
        dashboard-board-card(header='Top request consumers')
          template(v-slot:body)
            .column.q-gap-16
              km-data-table(:table='topTable', hide-pagination, @row-click='topRowClick')
    template(v-if='tab === "list"')
      .column.q-gap-16.full-width
        km-data-table(
          :table='detailsTable',
          row-key='_id',
          :loading='detailsLoading',
          hide-pagination,
          @row-click='detailsRowClick'
        )
        .row.items-center.q-px-md.q-py-sm.text-grey.ba-border(v-if='pagination.rowsNumber')
          .km-description {{ pagination.rowsNumber }} record{{ pagination.rowsNumber !== 1 ? 's' : '' }}
          q-space
          .row.items-center.q-gap-8
            span.km-description Rows per page: {{ pagination.rowsPerPage }}
          .row.items-center.q-ml-md.q-gap-4
            q-btn(flat, dense, round, icon='first_page', size='sm', :disable='pagination.page <= 1', @click='goToPage(1)')
            q-btn(flat, dense, round, icon='chevron_left', size='sm', :disable='pagination.page <= 1', @click='goToPage(pagination.page - 1)')
            span.km-description {{ pagination.page }} / {{ totalPages }}
            q-btn(flat, dense, round, icon='chevron_right', size='sm', :disable='pagination.page >= totalPages', @click='goToPage(pagination.page + 1)')
            q-btn(flat, dense, round, icon='last_page', size='sm', :disable='pagination.page >= totalPages', @click='goToPage(totalPages)')
</template>

<script>
import { ref, computed, h, markRaw } from 'vue'
import filter from '@/config/dashboard/llm-filters'
import topControls from '@/config/dashboard/llm-table'
import { fetchData } from '@shared'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import llmDetailsControls from '@/config/dashboard/llm-details-table'
import { useLocalDataTable } from '@/composables/useLocalDataTable'

export default {
  props: {
    selectedRow: {
      type: Object,
      default: null,
    },
  },
  emits: ['selectRow'],

  setup(props, { emit }) {
    const top = ref([])
    const detailedList = ref([])
    const detailsLoading = ref(false)

    // Top table columns
    const topControlsObj = topControls
    const topColumnsArr = Object.values(topControlsObj)

    const topColumns = topColumnsArr.map((col) => {
      const colDef = {
        id: col.name,
        accessorKey: col.field,
        header: col.label,
        enableSorting: col.sortable ?? false,
        meta: { align: col.align ?? 'left' },
      }
      if (col.format) {
        colDef.cell = ({ getValue }) => {
          const val = getValue()
          return val != null ? col.format(val) : '-'
        }
      }
      return colDef
    })

    const { table: topTable } = useLocalDataTable(top, topColumns, {
      defaultPageSize: 10,
    })

    // Details table columns
    const detailsControlsObj = llmDetailsControls
    const detailsColumnsArr = Object.values(detailsControlsObj).filter((col) => col.display)

    const detailsColumns = detailsColumnsArr.map((col) => {
      const colDef = {
        id: col.name,
        header: col.label,
        enableSorting: col.sortable ?? false,
        meta: {
          align: col.align ?? 'left',
          ...(col.headerStyle ? { width: col.headerStyle.replace('width: ', '').replace(';', '') } : {}),
        },
      }

      if (col.type === 'component' && col.component) {
        colDef.accessorFn = typeof col.field === 'function' ? col.field : (row) => row[col.field] ?? null
        colDef.cell = ({ row }) => {
          if (typeof col.component === 'function' && !col.component.__vccOpts && !col.component.setup && !col.component.render) {
            return col.component({ row: row.original })
          }
          return h(col.component, { row: row.original })
        }
        colDef.meta.component = col.component
      } else {
        colDef.accessorFn = typeof col.field === 'function' ? col.field : (row) => row[col.field]
        if (col.format) {
          colDef.cell = ({ getValue }) => {
            const val = getValue()
            return val != null ? col.format(val) : '-'
          }
        }
      }

      if (col.sort) {
        colDef.sortingFn = (a, b) => {
          const aVal = typeof col.field === 'function' ? col.field(a.original) : a.original[col.field]
          const bVal = typeof col.field === 'function' ? col.field(b.original) : b.original[col.field]
          return col.sort(aVal, bVal)
        }
      }

      return colDef
    })

    const { table: detailsTable } = useLocalDataTable(detailedList, detailsColumns, {
      defaultPageSize: 999,
      defaultSort: [{ id: 'start_time', desc: true }],
    })

    return {
      top,
      detailedList,
      detailsLoading,
      topTable,
      detailsTable,
    }
  },

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
      topControls: ref(topControls),
      pagination: ref({
        page: 1,
        rowsPerPage: 10,
        sortBy: 'start_time',
        descending: true,
      }),
      llmDetailsControls: ref(llmDetailsControls),
      dashboardOptions: ref({}),
    }
  },
  computed: {
    totalPages() {
      if (!this.pagination.rowsNumber) return 1
      return Math.ceil(this.pagination.rowsNumber / this.pagination.rowsPerPage)
    },
    detailedColumns() {
      return Object.values(this.llmDetailsControls).filter((control) => control.display)
    },
    topColumns() {
      return Object.values(this.topControls)
    },
    endpoint() {
      return this.$appConfig.api.aiBridge.urlAdmin
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
    goToPage(page) {
      this.pagination.page = page
      this.getDetailedList({ pagination: this.pagination })
    },
    topRowClick(row) {
      this.setFilter('consumer_name', { label: row.name, value: row.name })
      this.tab = 'list'
    },
    detailsRowClick(row) {
      this.$emit('selectRow', row)
    },
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
      // Dashboard options stored locally — no longer dispatched to Vuex
      this.dashboardOptions = data
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

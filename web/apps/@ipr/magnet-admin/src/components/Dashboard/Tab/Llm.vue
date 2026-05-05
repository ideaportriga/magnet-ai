<template>
  <div>
    <div class="flex-none center-flex-y">
      <km-tabs v-model="tab" class="full-width mb-lg" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </div>
    <div class="basis-12 my-lg">
      <div class="cluster pb-xs" data-gap="xs" data-justify="between">
        <div class="flex-none center-flex-y">
          <km-filter-bar ref="filterRef" v-model:config="currentFilter" v-model:filter-object="activeFilters" />
        </div>
      </div>
    </div>
    <div class="basis-12">
      <template v-if="tab === &quot;summary&quot;">
        <div class="km-grid-2">
          <dashboard-board-card header="Usage &amp; cost" theme="dark">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-label-value :label="m.dashboard_totalRequests()" :value="data.totalRequests" />
                <dashboard-board-label-value :label="m.dashboard_avgRequestCost()" :value="data.avgRequestCost" />
                <dashboard-board-label-value :label="m.dashboard_totalCost()" :value="data.totalCost" />
              </div>
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="Performance" theme="dark">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-label-value :label="m.dashboard_avgRequestLatency()" :value="data.avgRequestLatency" />
                <dashboard-board-label-value :label="m.dashboard_errorRate()" :value="data.errorRate" />
              </div>
            </template>
          </dashboard-board-card>
        </div>
        <div v-if="activeFilters.model" class="km-grid-1 mt-lg">
          <dashboard-board-card header="Consumer Requests">
            <template #body>
              <div class="stack" data-gap="lg">
                <km-data-table :table="topTable" hide-pagination />
              </div>
            </template>
          </dashboard-board-card>
        </div>
        <div v-else class="km-grid-1 mt-lg">
          <dashboard-board-card header="Top request consumers">
            <template #body>
              <div class="stack" data-gap="lg">
                <km-data-table :table="topTable" hide-pagination @row-click="topRowClick" />
              </div>
            </template>
          </dashboard-board-card>
        </div>
      </template>
      <template v-if="tab === &quot;list&quot;">
        <div class="stack full-width" data-gap="lg">
          <km-data-table :table="detailsTable" row-key="_id" :loading="detailsLoading" hide-pagination @row-click="detailsRowClick" />
          <div v-if="pagination.rowsNumber" class="cluster px-md py-sm text-grey ba-border" data-justify="between">
            <div class="km-description">{{ pagination.rowsNumber }} record{{ pagination.rowsNumber !== 1 ? 's' : '' }}</div>
            <div class="km-space" />
            <div class="cluster" data-gap="sm"><span class="km-description">Rows per page: {{ pagination.rowsPerPage }}</span></div>
            <div class="cluster ml-md" data-gap="xs">
              <km-btn flat dense round icon="first-page" size="sm" :disable="pagination.page &lt;= 1" @click="goToPage(1)" />
              <km-btn flat dense round icon="chevron_left" size="sm" :disable="pagination.page &lt;= 1" @click="goToPage(pagination.page - 1)" /><span class="km-description">{{ pagination.page }} / {{ totalPages }}</span>
              <km-btn flat dense round icon="chevron_right" size="sm" :disable="pagination.page &gt;= totalPages" @click="goToPage(pagination.page + 1)" />
              <km-btn flat dense round icon="last-page" size="sm" :disable="pagination.page &gt;= totalPages" @click="goToPage(totalPages)" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, computed, h, markRaw } from 'vue'
import { m } from '@/paraglide/messages'
import filter from '@/config/dashboard/llm-filters'
import topControls from '@/config/dashboard/llm-table'
import { fetchData } from '@shared'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import llmDetailsControls from '@/config/dashboard/llm-details-table'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { useCatalog } from '@/queries/catalog'
import { toMongoFilter } from '@/utils/filterTransforms'

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

    const { data: catalogData } = useCatalog()

    return {
      m,
      top,
      detailedList,
      detailsLoading,
      topTable,
      detailsTable,
      catalogData,
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
    mongoFilters() {
      return toMongoFilter(this.activeFilters ?? {}, this.listFilter ?? {})
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
    catalogData: {
      handler() {
        // Catalog options for dropdowns are read synchronously via
        // getCachedCatalog() inside the filter config getters. Reassign the
        // refs so KmFilterBar receives a new prop reference and re-resolves
        // its option lists once the catalog query has populated.
        this.listFilter = { ...filter }
        this.summaryFilter = { ...Object.fromEntries(Object.entries(filter)) }
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
          filters: this.mongoFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error || !response.ok) return
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
          filters: this.mongoFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.error && response.ok) {
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
        filters: this.mongoFilters,
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
      if (response.error || !response.ok) return
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
          filters: this.mongoFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.error && response.ok) {
        await response.json().then((data) => {
          this.observability = data
        })
      }
    },
  },
}
</script>

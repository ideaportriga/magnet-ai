<template lang="pug">
.row.q-mb-12
  .col-12
    km-filter-bar(v-model:config='currentFilter', v-model:filterObject='activeFilters', ref='filterRef')
    .column.q-gap-16.full-width
      km-data-table.q-mt-md(
        :table='detailsTable',
        row-key='start_time',
        hide-pagination,
        @row-click='selectRow'
      )
      .row.items-center.q-px-md.q-py-sm.text-grey.ba-border(v-if='pagination.rowsNumber')
        .km-description {{ m.common_recordCount({ total: pagination.rowsNumber }) }}
        q-space
        .row.items-center.q-gap-8
          span.km-description {{ m.common_rowsPerPage() }} {{ pagination.rowsPerPage }}
        .row.items-center.q-ml-md.q-gap-4
          q-btn(flat, dense, round, icon='first_page', size='sm', :disable='pagination.page <= 1', @click='goToPage(1)')
          q-btn(flat, dense, round, icon='chevron_left', size='sm', :disable='pagination.page <= 1', @click='goToPage(pagination.page - 1)')
          span.km-description {{ pagination.page }} / {{ totalPages }}
          q-btn(flat, dense, round, icon='chevron_right', size='sm', :disable='pagination.page >= totalPages', @click='goToPage(pagination.page + 1)')
          q-btn(flat, dense, round, icon='last_page', size='sm', :disable='pagination.page >= totalPages', @click='goToPage(totalPages)')
</template>
<script>
import { fetchData } from '@shared'
import { ref, h } from 'vue'
import { m } from '@/paraglide/messages'
import agentDetailsControls from '@/config/dashboard/agent-details-table'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useLocalDataTable } from '@/composables/useLocalDataTable'

export default {
  props: ['selectedRow'],

  setup() {
    const { draft } = useAgentEntityDetail()
    const detailedList = ref([])

    // Details table columns
    const detailsControlsObj = agentDetailsControls
    const detailsColumnsArr = Object.values(detailsControlsObj).filter((col) => col.display)

    const detailsColumns = detailsColumnsArr.map((col) => {
      const colDef = {
        id: col.name,
        header: col.label,
        enableSorting: col.sortable ?? false,
        meta: { align: col.align ?? 'left' },
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

    return { m, draft, detailedList, detailsTable }
  },

  data() {
    return {
      activeFilters: {},
      agentDetailsControls,
      searchString: '',
      listFilter: {
        source: {
          label: m.agents_consumerType(),
          key: 'source',
          type: 'component',
          options: [
            { label: m.agents_runtimeApi(), value: 'Runtime API' },
            { label: m.agents_runtimeAiApp(), value: 'Runtime AI App' },
            { label: m.agents_preview(), value: 'preview' },
            { label: m.agents_evaluation(), value: 'evaluation' },
          ],
          multiple: true,
          default: ['Runtime AI App', 'Runtime API'],
        },
        start_time: {
          label: m.agents_timePeriod(),
          key: 'start_time',
          type: 'timePeriod',
          default: 'P1D',
          overviewFilter: true,
        },
      },
      pagination: {
        rowsPerPage: 10,
        sortBy: 'start_time',
        descending: true,
        page: 1,
      },
    }
  },
  computed: {
    totalPages() {
      if (!this.pagination.rowsNumber) return 1
      return Math.ceil(this.pagination.rowsNumber / this.pagination.rowsPerPage)
    },
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
      return this.$appConfig.api.aiBridge.urlAdmin
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
    goToPage(page) {
      this.pagination.page = page
      this.getDetailedList({ pagination: this.pagination })
    },
    async getDetailedList(input) {

      const props = input?.pagination ?? this.pagination
      const body = {
        limit: props.rowsPerPage,
        sort: props.sortBy,
        order: props.descending ? -1 : 1,
        filters: { ...this.activeFilters, feature_system_name: { eq: this.draft?.system_name } },
        fields: [],
        exclude_fields: [],
        offset: (props.page - 1) * props.rowsPerPage,
      }
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/agent/list',
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
    selectRow(row) {
      if (row?.conversation_id) {
        window.open(this.$router.resolve({ path: `/conversation/${row.conversation_id}` }).href, '_blank')
      }
    },
  },
}
</script>
<style lang="stylus"></style>

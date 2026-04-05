<template lang="pug">
.column.full-height.full-width(style='min-height: 0')
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
  .row.items-center.q-gap-4.q-pb-4.justify-between.q-my-16
    .col-auto.center-flex-y
      km-filter-bar(v-model:config='currentFilter', v-model:filterObject='activeFilters', ref='filterRef')

  .col.full-width(style='min-height: 0; overflow: hidden')
    template(v-if='tab === "overview"')
      .overflow-auto.full-height
        .km-grid-2
          dashboard-board-card(header='Usage', theme='dark')
            template(v-slot:body)
              .column.q-gap-16
                dashboard-board-label-value(:label='m.dashboard_totalToolCalls()', :value='data.totalCalls')
                dashboard-board-label-value(:label='m.dashboard_uniqueUsers()', :value='data.uniqueUsers')
          dashboard-board-card(header='Performance & cost', theme='dark')
            template(v-slot:body)
              .column.q-gap-16
                .row
                  .col
                    dashboard-board-label-value(
                      :label='m.dashboard_avgToolCallCost()',
                      :value='data.avgCost',
                      tooltip='How much one RAG Tool call costs on average'
                    )
                  .col
                    dashboard-board-label-value(:label='m.dashboard_totalToolCost()', :value='data.totalCost')
                dashboard-board-label-value(
                  :label='m.dashboard_avgToolCallLatency()',
                  :value='data.avgLatency',
                  tooltip='How long one RAG Tool call takes on average'
                )
          dashboard-board-card(header='Answer rate')
            template(v-slot:body)
              .column.q-gap-16
                dashboard-board-label-value(:label='m.dashboard_answerRate()', :value='answerRate')
                .row
                  dashboard-board-label-value(:label='m.dashboard_answerRatio()')
                //- dashboard-board-bars(:data='data.questions')
                template(v-if='questionsDiagram.length')
                  dashboard-board-box-diagram(:data='questionsDiagram')
                template(v-else)
                  dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
                dashboard-board-min-label-value(
                  :label='m.dashboard_ragQueriesAnalyzed()',
                  :value='processRate.processed',
                  tooltip='Number of answers processed out of total questions'
                )
          dashboard-board-card(header='User satisfaction')
            template(v-slot:body)
              .column.q-gap-16.fit
                .row
                  .col
                    dashboard-board-label-value.q-mt-auto(
                      :label='m.dashboard_satisfactionRate()',
                      :value='satisfactionRate',
                      tooltip='The percentage of positive feedback out of all user feedback'
                    )

                .row
                  dashboard-board-label-value(:label='m.dashboard_feedbackRatio()')
                .col.full-width
                  template(v-if='data.likes + data.dislikes > 0')
                    dashboard-board-box-diagram(
                      :data='[ { title: "Liked", value: data.likes, icon: "fas fa-thumbs-up", iconColor: "like-text", backgroundColor: "like-bg", action: () => setFilterAndNavigate("extra_data.answer_feedback.type", { label: "Like", value: "like" }) }, { title: "Disliked", value: data.dislikes, icon: "fas fa-thumbs-down", iconColor: "error-text", backgroundColor: "dislike-bg", action: () => setFilterAndNavigate("extra_data.answer_feedback.type", { label: "Dislike", value: "dislike" }) }, ]'
                    )
                  template(v-else)
                    dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
                dashboard-board-min-label-value(
                  :label='m.dashboard_feedbackRate()',
                  :value='feedbackProcessRate',
                  tooltip='Percentage of RAG queries with user feedback vs. total RAG queries'
                )
        .km-grid.q-mt-16(v-if='$refs?.filterRef?.filterModel?.feature_system_name')
          dashboard-board-card.km-grid-item-2(header='Question topics')
            template(v-slot:body)
              .column.q-gap-16
                dashboard-board-bars(:data='data.topTopics')
          dashboard-board-card(header='Question languages')
            template(v-slot:body)
              dashboard-board-bars(:data='data.languages')
          dashboard-board-card(header='Copy answer rate', tooltip='How frequently the RAG Tool output is copied by users')
            template(v-slot:body)
              .column.q-gap-16
                .km-chart-value {{ data.copyRate }}
        .km-grid-1.q-mt-16(v-else)
          dashboard-board-card(header='RAG Tools overview')
            template(v-slot:body)
              .column.q-gap-16
                .km-table-compact
                  km-data-table(:table='overviewTable', row-key='name', hide-pagination, @row-click='overviewRowClick')
    template(v-if='tab === "list"')
      .column.full-height(style='min-height: 0')
        .row.q-mb-12
          q-space
          .col-auto
            dashboard-board-export-button(@exportToCsv='exportToFile("csv")', @exportToJson='exportToFile("json")')
        .col.overflow-auto(style='min-height: 0')
          km-data-table(
            :table='detailsTable',
            row-key='start_time',
            :loading='loading',
            fill-height,
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
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { ref, computed, markRaw, h } from 'vue'
import filter from '@/config/dashboard/rag-filters'
import controls from '@/config/dashboard/rag-table'
import ragDetailsControls from '@/config/dashboard/rag-details-table'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { textColumn, componentColumn } from '@/utils/columnHelpers'

const naTooltip = 'Data not available because post-processing was not enabled'

export default {
  props: ['selectedRow'],
  emits: ['selectRow'],

  setup(props, { emit }) {
    const rags = ref([])
    const detailedList = ref([])
    const loading = ref(false)

    // Overview table columns (RAG Tools overview)
    const overviewColumns = [
      {
        id: 'name',
        accessorKey: 'name',
        header: 'RAG Name',
        enableSorting: true,
        meta: { align: 'left' },
      },
      {
        id: 'count',
        accessorKey: 'count',
        header: 'Total tool calls',
        enableSorting: true,
        meta: { align: 'left' },
      },
      {
        id: 'unique_user_count',
        accessorKey: 'unique_user_count',
        header: 'Unique users',
        enableSorting: true,
        meta: { align: 'left' },
      },
      {
        id: 'avg_total_cost',
        accessorKey: 'avg_total_cost',
        header: 'Avg tool call cost',
        cell: ({ getValue }) => {
          const val = getValue()
          return val ? `${Number(val).toFixed(6)} $` : ''
        },
        enableSorting: true,
        meta: { align: 'left' },
      },
      {
        id: 'avg_latency',
        accessorKey: 'avg_latency',
        header: 'Avg tool call latency',
        cell: ({ getValue }) => {
          const val = getValue()
          return val ? `${formatDuration(val)}` : ''
        },
        enableSorting: true,
        meta: { align: 'left' },
      },
    ]

    const { table: overviewTable } = useLocalDataTable(rags, overviewColumns, {
      defaultPageSize: 10,
    })

    // Details table columns (RAG details list)
    const ragDetailsControlsObj = ragDetailsControls
    const detailsColumnsArr = Object.values(ragDetailsControlsObj).filter((col) => col.display)

    const detailsColumns = detailsColumnsArr.map((col) => {
      const colDef = {
        id: col.name,
        header: col.label,
        enableSorting: col.sortable ?? false,
        meta: {
          align: col.align ?? 'left',
          ...(col.style ? { width: col.style.replace('max-width: ', '').replace(';', '') } : {}),
        },
      }

      if (col.type === 'component' && col.component) {
        colDef.accessorFn = typeof col.field === 'function' ? col.field : (row) => row[col.field] ?? null
        colDef.cell = ({ row }) => {
          if (typeof col.component === 'function' && !col.component.__vccOpts && !col.component.setup && !col.component.render) {
            return col.component({ row: row.original, name: col.name })
          }
          return h(col.component, { row: row.original, name: col.name })
        }
        colDef.meta.component = col.component
      } else {
        colDef.accessorFn = typeof col.field === 'function' ? col.field : (row) => row[col.field]
        if (col.format) {
          colDef.cell = ({ getValue }) => {
            const val = getValue()
            return col.format(val)
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
      m,
      rags,
      detailedList,
      loading,
      overviewTable,
      detailsTable,
    }
  },

  data() {
    return {
      listFilter: ref(filter),
      summaryFilter: ref(Object.fromEntries(Object.entries(filter))),
      activeFilters: ref({}),
      tab: ref('list'),
      tabs: ref([
        { name: 'list', label: 'List' },
        { name: 'overview', label: 'Summary' },
      ]),
      controls: ref(controls),
      observability: ref({}),
      ragDetailsControls: ref(ragDetailsControls),
      searchString: ref(''),
      dashboardOptions: ref({}),
      pagination: ref({
        rowsPerPage: 10,
        sortBy: 'start_time',
        descending: true,
        page: 1,
      }),
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
        if (this.tab === 'overview') {
          return this.summaryFilter
        } else {
          return this.listFilter
        }
      },
      set(value) {
        if (this.tab === 'overview') {
          this.summaryFilter = value
        } else {
          this.listFilter = value
        }
      },
    },
    endpoint() {
      return this.$appConfig.api.aiBridge.urlAdmin
    },
    columns() {
      return Object.values(this.controls)
    },
    ragDetailsColumns() {
      return Object.values(this.ragDetailsControls).filter((column) => column.display)
    },
    ragTools() {
      // Legacy getter removed — rag tools list not needed for dashboard
      return []
    },
    data() {
      return {
        totalCalls: this.observability.total_calls ?? '-',
        avgLatency: this.observability.avg_latency ? `${formatDuration(this.observability.avg_latency)}` : '-',
        avgCost: this.observability.avg_cost ? `${this.observability.avg_cost.toFixed(6)} $` : '-',
        totalCost: this.observability?.total_cost ? `${this.observability.total_cost.toFixed(6)} $` : '-',
        //single
        copyRate: this.observability?.answer_summary?.copy_rate ? `${this.observability.answer_summary.copy_rate.toFixed(2)}%` : '-',
        uniqueUsers: this.observability?.unique_user_count ?? '-',
        topTopics:
          this.observability?.topic_summary?.breakdown
            .map((topic) => ({
              title: topic.name ?? 'N/A',
              value: topic.count,
              tooltip: topic.name ? null : naTooltip,
              action: topic.name ? () => this.setFilterAndNavigate('extra_data.topic', { label: topic.name, value: topic.name }) : null,
            }))
            .sort((a, b) => b.value - a.value) ?? [],
        languages:
          this.observability?.language_summary?.breakdown
            .map((lang) => ({
              title: lang.name ?? 'N/A',
              value: lang.count,
              tooltip: lang.name ? null : naTooltip,
              action: lang.name ? () => this.setFilterAndNavigate('extra_data.language', { label: lang.name, value: lang.name }) : null,
            }))
            .sort((a, b) => b.value - a.value) ?? [],
        questions:
          this.observability?.resolution_summary?.breakdown.map((question) => this.mapQuestions(question)).sort((a, b) => b.order - a.order) ?? [],
        likes: this.observability?.answer_summary?.feedback?.breakdown?.find((feedback) => feedback.name === 'like')?.count ?? 0,
        dislikes: this.observability?.answer_summary?.feedback?.breakdown?.find((feedback) => feedback.name === 'dislike')?.count ?? 0,
      }
    },
    processRate() {
      const totalQuestions = this.data.questions.reduce((acc, question) => acc + question.value, 0)
      const notProcessed = this.data.questions.filter((question) => question.title === null).reduce((acc, question) => acc + question.value, 0)
      const processed = totalQuestions - notProcessed

      return {
        processed:
          processed > 0 && totalQuestions > 0 && !isNaN(processed) && !isNaN(totalQuestions)
            ? `${((processed / totalQuestions) * 100).toFixed(2)}%`
            : '0%',
        notProcessed:
          notProcessed > 0 && totalQuestions > 0 && !isNaN(notProcessed) && !isNaN(totalQuestions)
            ? `${((notProcessed / totalQuestions) * 100).toFixed(2)}%`
            : '0%',
      }
    },
    feedbackProcessRate() {
      const totalFeedback = this.data.likes + this.data.dislikes
      const questions = this.data.totalCalls
      if (totalFeedback > 0 && questions > 0) {
        return `${((totalFeedback / questions) * 100).toFixed(2)}%`
      }
      return '0%'
    },
    satisfactionRate() {
      return this.data.likes + this.data.dislikes > 0 ? `${((this.data.likes / (this.data.likes + this.data.dislikes)) * 100).toFixed(2)}%` : '-'
    },
    questionsDiagram() {
      return this.data.questions.filter((question) => question.title !== null)
    },
    answerRate() {
      const totalQuestions =
        this.observability?.resolution_summary?.breakdown
          .filter((question) => question.name !== null)
          .reduce((acc, question) => acc + question.count, 0) ?? 0

      const answeredQuestions = this.observability?.resolution_summary?.breakdown.find((question) => question.name)?.count ?? 0

      return totalQuestions > 0 ? `${((answeredQuestions / totalQuestions) * 100).toFixed(2)}%` : '-'
    },
    languageOptions() {
      return (
        this.observability?.options.languages.map((lang) => ({
          label: lang,
          value: lang,
        })) ?? []
      )
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
  mounted() {},
  methods: {
    goToPage(page) {
      this.pagination.page = page
      this.getDetailedList({ pagination: this.pagination })
    },
    overviewRowClick(row) {
      this.$refs.filterRef.setFilter('feature_system_name', { label: row.name, value: row.name })
    },
    detailsRowClick(row) {
      this.$emit('selectRow', row)
    },
    refresh() {
      this.getObservability()
      this.getDetailedList()
      this.getRAG()
      this.getOptions()
    },
    mapQuestions(question) {
      const titles = {
        true: 'Yes',
        false: 'No',
      }
      const tooltips = {
        true: 'Questions where the model generated a response.',
        false: 'Questions where chunks of content were retrieved, but content was not sufficient or relevant for the model to generate response.',
      }
      const bg = {
        true: 'question_answered',
        false: 'dislike-bg',
      }
      const color = {
        true: 'like-text',
        false: 'error-text',
      }

      return {
        title: titles[question.name] ?? question.name ?? null,
        value: question.count,
        tooltip: tooltips[question.name] ?? 'Data not available because post-processing was not enabled',
        backgroundColor: bg[question.name] ?? null,
        iconColor: color[question.name] ?? 'secondary-text',
        order: question.name ? 1 : 0,
        action:
          question.name != null
            ? () => this.setFilterAndNavigate('extra_data.is_answered', { label: titles[question.name], value: question.name })
            : null,
      }
    },
    async getOptions() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/rag/options',
        body: JSON.stringify({
          filters: this.activeFilters,
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
    async getRAG() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/rag/top',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error || !response.ok) return
      this.rags = await response.json()
    },
    async getObservability() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/rag',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error || !response.ok) return
      const data = await response.json()
      this.observability = data
    },
    async getDetailedList(input) {
      const props = input?.pagination ?? this.pagination
      const body = {
        limit: props.rowsPerPage,
        sort: props.sortBy,
        order: props.descending ? -1 : 1,
        filters: this.activeFilters,
        fields: [],
        exclude_fields: [],
        offset: (props.page - 1) * props.rowsPerPage,
      }

      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        service: 'observability/monitoring/rag/list',
        credentials: 'include',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        this.detailedList = []
        return
      }
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
    async exportToFile(format) {
      const { sortBy, descending } = this.pagination
      const body = {
        limit: 999999,
        sort: sortBy,
        order: descending ? -1 : 1,
        filters: this.activeFilters,
        fields: [],
        exclude_fields: [],
      }

      // Get data from API
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        service: `observability/monitoring/rag/export?format=${format}`,
        credentials: 'include',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': format === 'json' ? 'application/json' : 'text/csv',
        },
      })

      // Create temporary link to download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rag-usage.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
    cellAction(e) {
      if (e.action === 'drilldown') {
        this.$refs.filterRef.setFilter('feature_system_name', { label: e.row.name, value: e.row.name })
      } else if (e.action === 'select') {
        this.$emit('selectRow', e.row)
      }
    },

    setFilter(key, { label, value }) {
      this.$refs.filterRef.setFilter(key, { label, value })
    },
    setFilterAndNavigate(key, { label, value }) {
      this.tab = 'list'
      this.listFilter = { ...this.listFilter, [key]: { ...this.listFilter[key], ['is_hidden']: false } }
      this.setFilter(key, { label, value })
    },
  },
}
</script>

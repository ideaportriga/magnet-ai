<template>
  <div class="stack full-height full-width" style="min-block-size: 0">
    <km-tabs v-model="tab" class="full-width mb-lg" narrow-indicator dense align="left" no-caps content-class="km-tabs">
      <template v-for="t in tabs" :key="t">
        <km-tab :name="t.name" :label="t.label" />
      </template>
    </km-tabs>
    <div class="cluster pb-xs my-lg" data-justify="between" data-gap="xs">
      <div class="flex-none center-flex-y">
        <km-filter-bar ref="filterRef" v-model:config="currentFilter" v-model:filter-object="activeFilters" />
      </div>
    </div>
    <div class="flex-1 full-width" style="min-block-size: 0; overflow: hidden">
      <template v-if="tab === &quot;overview&quot;">
        <div class="overflow-auto full-height">
          <div class="km-grid-2">
            <dashboard-board-card header="Usage" theme="dark">
              <template #body>
                <div class="stack" data-gap="lg">
                  <dashboard-board-label-value :label="m.dashboard_totalToolCalls()" :value="data.totalCalls" />
                  <dashboard-board-label-value :label="m.dashboard_uniqueUsers()" :value="data.uniqueUsers" />
                </div>
              </template>
            </dashboard-board-card>
            <dashboard-board-card header="Performance &amp; cost" theme="dark">
              <template #body>
                <div class="stack" data-gap="lg">
                  <div class="cluster">
                    <div class="flex-1">
                      <dashboard-board-label-value :label="m.dashboard_avgToolCallCost()" :value="data.avgCost" tooltip="How much one RAG Tool call costs on average" />
                    </div>
                    <div class="flex-1">
                      <dashboard-board-label-value :label="m.dashboard_totalToolCost()" :value="data.totalCost" />
                    </div>
                  </div>
                  <dashboard-board-label-value :label="m.dashboard_avgToolCallLatency()" :value="data.avgLatency" tooltip="How long one RAG Tool call takes on average" />
                </div>
              </template>
            </dashboard-board-card>
            <dashboard-board-card header="Answer rate">
              <template #body>
                <div class="stack" data-gap="lg">
                  <dashboard-board-label-value :label="m.dashboard_answerRate()" :value="answerRate" />
                  <div>
                    <dashboard-board-label-value :label="m.dashboard_answerRatio()" />
                  </div>
                  <template v-if="questionsDiagram.length">
                    <dashboard-board-box-diagram :data="questionsDiagram" />
                  </template>
                  <template v-else>
                    <dashboard-board-box-diagram :data="[{ title: &quot;N/A&quot;, icon: null, backgroundColor: &quot;table-header&quot; }]" />
                  </template>
                  <dashboard-board-min-label-value :label="m.dashboard_ragQueriesAnalyzed()" :value="processRate.processed" tooltip="Number of answers processed out of total questions" />
                </div>
              </template>
            </dashboard-board-card>
            <dashboard-board-card header="User satisfaction">
              <template #body>
                <div class="stack fit" data-gap="lg">
                  <div class="cluster">
                    <div class="flex-1">
                      <dashboard-board-label-value class="mt-auto" :label="m.dashboard_satisfactionRate()" :value="satisfactionRate" tooltip="The percentage of positive feedback out of all user feedback" />
                    </div>
                  </div>
                  <div>
                    <dashboard-board-label-value :label="m.dashboard_feedbackRatio()" />
                  </div>
                  <div class="flex-1 full-width">
                    <template v-if="data.likes + data.dislikes &gt; 0">
                      <dashboard-board-box-diagram :data="[ { title: &quot;Liked&quot;, value: data.likes, icon: &quot;thumbs-up&quot;, iconColor: &quot;like-text&quot;, backgroundColor: &quot;like-bg&quot;, action: () =&gt; setFilterAndNavigate(&quot;extra_data.answer_feedback.type&quot;, { label: &quot;Like&quot;, value: &quot;like&quot; }) }, { title: &quot;Disliked&quot;, value: data.dislikes, icon: &quot;thumbs-down&quot;, iconColor: &quot;error-text&quot;, backgroundColor: &quot;dislike-bg&quot;, action: () =&gt; setFilterAndNavigate(&quot;extra_data.answer_feedback.type&quot;, { label: &quot;Dislike&quot;, value: &quot;dislike&quot; }) }, ]" />
                    </template>
                    <template v-else>
                      <dashboard-board-box-diagram :data="[{ title: &quot;N/A&quot;, icon: null, backgroundColor: &quot;table-header&quot; }]" />
                    </template>
                  </div>
                  <dashboard-board-min-label-value :label="m.dashboard_feedbackRate()" :value="feedbackProcessRate" tooltip="Percentage of RAG queries with user feedback vs. total RAG queries" />
                </div>
              </template>
            </dashboard-board-card>
          </div>
          <div v-if="$refs?.filterRef?.filterModel?.feature_system_name" class="km-grid mt-lg">
            <dashboard-board-card class="km-grid-item-2" header="Question topics">
              <template #body>
                <div class="stack" data-gap="lg">
                  <dashboard-board-bars :data="data.topTopics" />
                </div>
              </template>
            </dashboard-board-card>
            <dashboard-board-card header="Question languages">
              <template #body>
                <dashboard-board-bars :data="data.languages" />
              </template>
            </dashboard-board-card>
            <dashboard-board-card header="Copy answer rate" tooltip="How frequently the RAG Tool output is copied by users">
              <template #body>
                <div class="stack" data-gap="lg">
                  <div class="km-chart-value">{{ data.copyRate }}</div>
                </div>
              </template>
            </dashboard-board-card>
          </div>
          <div v-else class="km-grid-1 mt-lg">
            <dashboard-board-card header="RAG Tools overview">
              <template #body>
                <div class="stack" data-gap="lg">
                  <div class="km-table-compact">
                    <km-data-table :table="overviewTable" row-key="name" hide-pagination @row-click="overviewRowClick" />
                  </div>
                </div>
              </template>
            </dashboard-board-card>
          </div>
        </div>
      </template>
      <template v-if="tab === &quot;list&quot;">
        <div class="stack full-height" style="min-block-size: 0">
          <div class="cluster mb-md" data-justify="end">
            <div class="km-space" />
            <div class="flex-none">
              <dashboard-board-export-button @export-to-csv="exportToFile(&quot;csv&quot;)" @export-to-json="exportToFile(&quot;json&quot;)" />
            </div>
          </div>
          <div class="flex-1 overflow-auto" style="min-block-size: 0">
            <km-data-table :table="detailsTable" row-key="start_time" :loading="loading" fill-height hide-pagination @row-click="detailsRowClick" />
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
        </div>
      </template>
    </div>
  </div>
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
import { useCatalog } from '@/queries/catalog'
import { toMongoFilter } from '@/utils/filterTransforms'

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

    const { data: catalogData } = useCatalog()

    return {
      m,
      rags,
      detailedList,
      loading,
      overviewTable,
      detailsTable,
      catalogData,
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
    mongoFilters() {
      return toMongoFilter(this.activeFilters ?? {}, this.listFilter ?? {})
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
    async getRAG() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/rag/top',
        body: JSON.stringify({
          filters: this.mongoFilters,
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
          filters: this.mongoFilters,
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
        filters: this.mongoFilters,
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
        filters: this.mongoFilters,
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

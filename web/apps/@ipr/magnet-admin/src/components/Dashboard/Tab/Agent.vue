<template>
  <div>
    <div class="center-flex-y">
      <km-tabs v-model="tab" class="full-width mb-lg" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in tabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </div>
    <div class="full-width my-lg">
      <km-filter-bar ref="filterRef" v-model:config="currentFilter" v-model:filter-object="activeFilters" />
    </div>
    <div class="full-width">
      <template v-if="tab === &quot;overview&quot;">
        <div class="km-grid-2">
          <dashboard-board-card header="Usage" theme="dark">
            <template #body>
              <div class="stack" data-gap="lg">
                <div class="cluster">
                  <div class="flex-1">
                    <dashboard-board-label-value :label="m.dashboard_totalConversations()" :value="data.totalConversations" />
                  </div>
                  <div class="flex-1">
                    <dashboard-board-label-value :label="m.dashboard_avgMessagesPerConversation()" :value="avgMessagesInConversation" />
                  </div>
                </div>
                <div class="cluster">
                  <div class="flex-1">
                    <dashboard-board-label-value :label="m.dashboard_uniqueUsers()" :value="data.uniqueUsers" />
                  </div>
                  <div class="km-space" />
                </div>
              </div>
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="Performance &amp; cost" theme="dark">
            <template #body>
              <div class="stack" data-gap="lg">
                <div class="cluster">
                  <div class="flex-1">
                    <dashboard-board-label-value :label="m.dashboard_avgConversationCost()" :value="data.avgCost" tooltip="How much one conversation costs on average" />
                  </div>
                  <div class="flex-1">
                    <dashboard-board-label-value :label="m.dashboard_totalToolCost()" :value="data.totalCost" />
                  </div>
                </div>
              </div>
              <dashboard-board-label-value :label="m.dashboard_avgLatency()" :value="data.avgLatency" tooltip="Time that it takes an Agent to respond on average" />
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="Case deflection">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-label-value :label="m.dashboard_caseDeflectionRate()" :value="caseDeflectionRate" tooltip="How many questions were answered by the agent" />
                <dashboard-board-label-value :label="m.dashboard_issuesProcessed()" tooltip="How many issues were processed by the agent" />
                <div class="flex-1">
                  <template v-if="resolutionDiagram.length">
                    <dashboard-board-box-diagram :data="resolutionDiagram" />
                  </template>
                  <template v-else>
                    <dashboard-board-box-diagram :data="[{ title: &quot;N/A&quot;, icon: null, backgroundColor: &quot;table-header&quot; }]" />
                  </template>
                </div>
                <dashboard-board-min-label-value :label="m.dashboard_caseProcessingRate()" :value="caseProcessingRate" tooltip="How many cases were processed by the agent" />
              </div>
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="User feedback">
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
                    <dashboard-board-box-diagram :data="[ { title: &quot;Liked&quot;, value: data.likes, icon: &quot;thumbs-up&quot;, iconColor: &quot;like-text&quot;, backgroundColor: &quot;like-bg&quot;, action: () =&gt; setFilterAndNavigate(&quot;feedback&quot;, { label: &quot;Like&quot;, value: &quot;like&quot; }) }, { title: &quot;Disliked&quot;, value: data.dislikes, icon: &quot;thumbs-down&quot;, iconColor: &quot;error-text&quot;, backgroundColor: &quot;dislike-bg&quot;, action: () =&gt; setFilterAndNavigate(&quot;feedback&quot;, { label: &quot;Dislike&quot;, value: &quot;dislike&quot; }) }, ]" />
                  </template>
                  <template v-else>
                    <dashboard-board-box-diagram :data="[{ title: &quot;N/A&quot;, icon: null, backgroundColor: &quot;table-header&quot; }]" />
                  </template>
                </div>
                <dashboard-board-min-label-value :label="m.dashboard_feedbackRate()" :value="feedbackProcessRate" tooltip="Number of feedback processed out of total questions" />
              </div>
            </template>
          </dashboard-board-card>
        </div>
        <div class="km-grid-1 mt-lg">
          <dashboard-board-card header="Final sentiment">
            <template #body>
              <div class="stack" data-gap="lg">
                <template v-if="sentimentDiagram.length">
                  <dashboard-board-box-diagram :data="sentimentDiagram" />
                </template>
                <template v-else>
                  <dashboard-board-box-diagram :data="[{ title: &quot;N/A&quot;, icon: null, backgroundColor: &quot;table-header&quot; }]" />
                </template>
              </div>
            </template>
          </dashboard-board-card>
        </div>
        <div v-if="$refs.filterRef?.filterModel?.feature_system_name" class="km-grid mt-lg">
          <dashboard-board-card class="km-grid-item-2" header="Most frequent topics">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-bars :data="topics" />
              </div>
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="User languages">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-bars :data="languages" />
              </div>
            </template>
          </dashboard-board-card>
          <dashboard-board-card header="Copy answer rate" tooltip="How frequently the RAG Tool output is copied by users">
            <template #body>
              <div class="stack" data-gap="lg">
                <dashboard-board-label-value :label="m.dashboard_copyAnswerRate()" :value="data.copyRate" />
              </div>
            </template>
          </dashboard-board-card>
        </div>
        <div v-else class="km-grid-1 mt-lg">
          <dashboard-board-card header="Agent overview">
            <template #body>
              <div class="stack" data-gap="lg">
                <div class="km-table-compact">
                  <km-data-table :table="overviewTable" row-key="name" hide-pagination @row-click="overviewRowClick" />
                </div>
              </div>
            </template>
          </dashboard-board-card>
        </div>
      </template>
    </div>
    <template v-if="tab === &quot;list&quot;">
      <div class="stack full-width" data-gap="lg">
        <div>
          <div class="center-flex-y full-width">
            <!--km-input(:placeholder='m.common_search()', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)-->
            <div class="km-space" />
            <div class="flex-none">
              <dashboard-board-export-button @export-to-csv="exportToFile(&quot;csv&quot;)" @export-to-json="exportToFile(&quot;json&quot;)" />
            </div>
          </div>
          <div class="km-space" />
        </div>
        <km-data-table :table="detailsTable" row-key="start_time" :loading="detailsLoading" hide-pagination @row-click="detailsRowClick" />
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
</template>
<script>
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { ref, computed, h, markRaw } from 'vue'
import filter from '@/config/dashboard/agent-filters'
import controls from '@/config/dashboard/agent-table'
import agentDetailsControls from '@/config/dashboard/agent-details-table'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { useCatalog } from '@/queries/catalog'
import { toMongoFilter } from '@/utils/filterTransforms'

const naTooltip = 'Data not available because post-processing was not done for this conversation yet'

export default {
  props: ['selectedRow'],
  emits: ['selectRow'],

  setup(props, { emit }) {
    const rags = ref([])
    const detailedList = ref([])
    const detailsLoading = ref(false)

    // Overview table columns (Agent overview)
    const overviewControlsObj = controls
    const overviewColumnsArr = Object.values(overviewControlsObj)

    const overviewColumns = overviewColumnsArr.map((col) => {
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
          return val != null ? col.format(val) : ''
        }
      }
      return colDef
    })

    const { table: overviewTable } = useLocalDataTable(rags, overviewColumns, {
      defaultPageSize: 10,
    })

    // Details table columns (Agent details list)
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

    const { data: catalogData } = useCatalog()

    return {
      m,
      rags,
      detailedList,
      detailsLoading,
      overviewTable,
      detailsTable,
      catalogData,
    }
  },

  data() {
    return {
      filter: ref(filter),
      activeFilter: ref({}),
      activeFilters: ref({}),
      tab: ref('list'),
      tabs: ref([
        { name: 'list', label: 'List' },
        { name: 'overview', label: 'Summary' },
      ]),
      controls: ref(controls),
      observability: ref({}),
      agentDetailsControls: ref(agentDetailsControls),
      searchString: ref(''),
      dashboardOptions: ref({}),
      summaryFilter: ref(Object.fromEntries(Object.entries(filter))),
      listFilter: ref(filter),
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
    agentDetailsColumns() {
      return Object.values(this.agentDetailsControls).filter((column) => column.display)
    },
    ragTools() {
      // Legacy getter removed — rag tools list not needed for dashboard
      return []
    },
    data() {
      return {
        totalConversations: this.observability?.total_conversations ?? '-',
        totalCost: this.observability?.total_cost ? `${this.observability.total_cost.toFixed(6)} $` : '-',
        uniqueUsers: this.observability?.unique_user_count ?? '-',
        avgCost: this.observability?.avg_cost ? `${this.observability.avg_cost.toFixed(6)} $` : '-',
        avgLatency: this.observability?.avg_tool_call_latency !== null ? `${formatDuration(this.observability.avg_tool_call_latency)}` : '-',
        likes: this.observability?.feedback_summary?.breakdown?.find((feedback) => feedback.name === 'likes')?.count ?? 0,
        dislikes: this.observability?.feedback_summary?.breakdown?.find((feedback) => feedback.name === 'dislikes')?.count ?? 0,
        resolutionStatus: this.mapResolutionStatus(),
        sentiment: this.mapCaseDeflectionStatus(),
        topics: [
          { title: 'Customer Portal', value: 1222, action: () => {} },
          { title: 'Mobile App', value: 400, action: () => {} },
          { title: 'Other', value: 100, action: () => {} },
        ],
        languages: [
          { title: 'English', value: 1222, action: () => {} },
          { title: 'Spanish', value: 400, action: () => {} },
          { title: 'French', value: 100, action: () => {} },
        ],
        copyRate: this.observability?.copy_rate ? `${this.observability.copy_rate.toFixed(2)}%` : '-',
        nextActions: [
          { title: 'Customer Portal', value: 1222, action: () => {} },
          { title: 'Mobile App', value: 400, action: () => {} },
          { title: 'Other', value: 100, action: () => {} },
        ],
        products: [
          { title: 'Customer Portal', value: 1222, action: () => {} },
          { title: 'Mobile App', value: 400, action: () => {} },
          { title: 'Other', value: 100, action: () => {} },
        ],
        scriptCompletionRate: '80.22%',
      }
    },
    topics() {
      return (this.observability?.topics_summary?.breakdown ?? []).map((item) => {
        return {
          title: item?.name,
          value: item?.count,
          action: () => this.setFilterAndNavigate('conversation_data.topics', { label: item.name, value: item.name }),
        }
      })
    },
    languages() {
      return (this.observability?.language_summary?.breakdown ?? []).map((item) => {
        return {
          title: item?.name ?? 'N/A',
          value: item?.count,
          tooltip: item?.name ? null : naTooltip,
          action: () => this.setFilterAndNavigate('conversation_data.language', { label: item.name, value: item.name }),
        }
      })
    },
    avgMessagesInConversation() {
      return (this.observability?.avg_messages_count ?? 0).toFixed(1)
    },
    resolutionDiagram() {
      return this.data.resolutionStatus.filter((item) => item.title !== null)
    },
    satisfactionRate() {
      return this.data.likes + this.data.dislikes > 0 ? `${((this.data.likes / (this.data.likes + this.data.dislikes)) * 100).toFixed(2)}%` : '-'
    },
    caseDeflectionRate() {
      const resolved = this.resolutionDiagram.find((item) => item.title === 'Resolved')?.value ?? 0
      const total = this.resolutionDiagram.reduce((acc, item) => {
        acc += item.value
        return acc
      }, 0)
      if (total === 0) return '0%'
      return `${((resolved / total) * 100).toFixed(2)}%`
    },
    feedbackProcessRate() {
      const totalFeedback = this.observability?.feedback_rate
      if (totalFeedback > 0) {
        return `${(totalFeedback * 100).toFixed(2)}%`
      }
      return '0%'
    },
    caseProcessingRate() {
      const total = this.data.resolutionStatus.reduce((acc, item) => acc + item.value, 0)
      const processed = this.resolutionDiagram.reduce((acc, item) => {
        acc += item.value
        return acc
      }, 0)
      if (processed > 0 && total > 0) {
        return `${((processed / total) * 100).toFixed(2)}%`
      }

      return '0%'
    },
    sentimentDiagram() {
      return this.data.sentiment.filter((item) => item.title)
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
        this.getAgents()
        this.getObservability()
        this.getDetailedList()
        this.getOptions()
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
    overviewRowClick(row) {
      this.setFilter('feature_system_name', { label: row.name, value: row.system_name })
    },
    detailsRowClick(row) {
      this.navigateToConversation(row)
    },
    mapCaseDeflectionStatus() {
      //- setntiment (positive, negative, neutral)
      const status = {
        positive: {
          title: 'Positive',
          iconColor: 'like-text',
          svgIcon: 'like-emoji',
          backgroundColor: 'like-bg',
          action: () => this.setFilterAndNavigate('conversation_data.sentiment', { label: 'Positive', value: 'positive' }),
          order: 1,
        },
        neutral: {
          title: 'Neutral',
          iconColor: 'secondary-text',
          svgIcon: 'neutral-emoji',
          backgroundColor: 'neutral-bg',
          action: () => this.setFilterAndNavigate('conversation_data.sentiment', { label: 'Neutral', value: 'neutral' }),
          order: 2,
        },
        negative: {
          title: 'Negative',
          iconColor: 'error-text',
          svgIcon: 'dislike-emoji',
          backgroundColor: 'dislike-bg',
          action: () => this.setFilterAndNavigate('conversation_data.sentiment', { label: 'Negative', value: 'negative' }),
          order: 3,
        },
      }

      const sentiment = this.observability?.sentiment_summary?.breakdown
      if (!sentiment) return []
      return sentiment
        .map((item) => {
          return { ...status[item.name], value: item.count }
        })
        .sort((a, b) => a.order - b.order)
    },
    mapResolutionStatus() {
      const resolutions = {
        resolved: {
          title: 'Resolved',
          backgroundColor: 'like-bg',
          iconColor: 'like-text',
          action: () => this.setFilterAndNavigate('conversation_data.resolution_status', { label: 'Resolved', value: 'resolved' }),
          order: 1,
        },
        not_resolved: {
          title: 'Not resolved',
          backgroundColor: 'dislike-bg',
          iconColor: 'error-text',
          action: () => this.setFilterAndNavigate('conversation_data.resolution_status', { label: 'Not resolved', value: 'not_resolved' }),
          order: 2,
        },
        transferred: {
          title: 'Transferred to human',
          backgroundColor: 'primary-light',
          iconColor: 'secondary-text',
          action: () => this.setFilterAndNavigate('conversation_data.resolution_status', { label: 'Transferred to human', value: 'transferred' }),
          order: 3,
        },
        null: {
          title: null,
          backgroundColor: 'table-header',
          iconColor: 'secondary-text',
          order: 4,
        },
      }
      const resolution = this.observability?.resolution_summary?.breakdown
      if (!resolution) return []
      return resolution
        .map((item) => {
          return { ...resolutions[item.name], value: item.count }
        })
        .sort((a, b) => a.order - b.order)
    },
    navigateToConversation(row) {
      if (row?.conversation_id) {
        this.$router.push(`/conversation/${row.conversation_id}`)
      }
    },
    updateVisibleFilters(key, value) {
      this.filter[key].hide = value
    },
    updateActiveFilters({ key = undefined, value = undefined } = {}) {
      if (!value && !key) {
        this.activeFilters = {}
        return
      }
      this.activeFilters[key] = value
    },
    async getAgents() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/agent/top',
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
        service: 'observability/monitoring/agent',
        body: JSON.stringify({
          filters: this.mongoFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error || !response.ok) return
      this.observability = await response.json()
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
        credentials: 'include',
        service: 'observability/monitoring/agent/list',
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
        service: `observability/monitoring/agent/export?format=${format}`,
        credentials: 'include',
        body: JSON.stringify(body),
        headers: {
          'Content-Type': format === 'json' ? 'application/json' : 'text/csv',
        },
      })

      if (response.error || !response.ok) return
      // Create temporary link to download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'agent-usage.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
    async getOptions() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/agent/options',
        body: JSON.stringify({
          filters: this.mongoFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (response.error || !response.ok) return
      const data = await response.json()
      if (data) {
        // Dashboard options stored locally — no longer dispatched to Vuex
        this.dashboardOptions = data
      }
    },

    cellAction(e) {
      if (e.action === 'filterAgent') {
        this.setFilter('feature_system_name', { label: e.row.name, value: e.row.system_name })
      }
    },
    setFilter(key, { label, value }) {
      this.$refs.filterRef.setFilter(key, { label, value })
    },
    setFilterAndNavigate(key, { label, value }) {
      this.tab = 'list'
      this.listFilter = { ...this.listFilter, [key]: { ...this.listFilter[key], ['is_hidden']: false } }
      // this.$refs.filterRef.clearFilter([])
      this.setFilter(key, { label, value })
    },
  },
}
</script>

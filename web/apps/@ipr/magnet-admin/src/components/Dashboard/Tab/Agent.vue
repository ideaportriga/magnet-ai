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
    km-filter-bar(v-model:config='currentFilter', v-model:filterObject='activeFilters', ref='filterRef')
  .col-12
    template(v-if='tab === "overview"')
      .km-grid-2
        dashboard-board-card(header='Usage', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              .row
                .col
                  dashboard-board-label-value(label='Total conversations', :value='data.totalConversations')
                .col
                  dashboard-board-label-value(label='Avg. messages per conversation', :value='avgMessagesInConversation')
              .row
                .col
                  dashboard-board-label-value(label='Unique users', :value='data.uniqueUsers')
                .col

        dashboard-board-card(header='Performance & cost', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              .row
                .col
                  dashboard-board-label-value(
                    label='Avg. conversation cost',
                    :value='data.avgCost',
                    tooltip='How much one conversation costs on average'
                  )
                .col
                  dashboard-board-label-value(label='Total tool cost', :value='data.totalCost')
            dashboard-board-label-value(label='Avg. latency', :value='data.avgLatency', tooltip='Time that it takes an Agent to respond on average')
        dashboard-board-card(header='Case deflection')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(
                label='Case deflection rate',
                :value='caseDeflectionRate',
                tooltip='How many questions were answered by the agent'
              )
              dashboard-board-label-value(label='Issues processed', tooltip='How many issues were processed by the agent')
              .col
                template(v-if='resolutionDiagram.length')
                  dashboard-board-box-diagram(:data='resolutionDiagram')
                template(v-else)
                  dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
              dashboard-board-min-label-value(
                label='Case processing rate',
                :value='caseProcessingRate',
                tooltip='How many cases were processed by the agent'
              )
        dashboard-board-card(header='User feedback')
          template(v-slot:body)
            .column.q-gap-16.fit
              .row
                //- .col
                //-   dashboard-board-label-value(label='Total votes', :value='data.likes + data.dislikes')
                .col
                  dashboard-board-label-value.q-mt-auto(
                    label='Satisfaction rate',
                    :value='satisfactionRate',
                    tooltip='The percentage of positive feedback out of all user feedback'
                  )
              .row
                dashboard-board-label-value(label='Feedback ratio') 
              .col.full-width
                template(v-if='data.likes + data.dislikes > 0')
                  dashboard-board-box-diagram(
                    :data='[ { title: "Liked", value: data.likes, icon: "fas fa-thumbs-up", iconColor: "like-text", backgroundColor: "like-bg", action: () => setFilterAndNavigate("feedback", { label: "Like", value: "like" }) }, { title: "Disliked", value: data.dislikes, icon: "fas fa-thumbs-down", iconColor: "error-text", backgroundColor: "dislike-bg", action: () => setFilterAndNavigate("feedback", { label: "Dislike", value: "dislike" }) }, ]'
                  )
                template(v-else)
                  dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
              dashboard-board-min-label-value(
                label='Feedback rate',
                :value='feedbackProcessRate',
                tooltip='Number of feedback processed out of total questions'
              )
      .km-grid-1.q-mt-16
        dashboard-board-card(header='Final sentiment')
          template(v-slot:body)
            .column.q-gap-16
              template(v-if='sentimentDiagram.length')
                dashboard-board-box-diagram(:data='sentimentDiagram')
              template(v-else)
                dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
      .km-grid.q-mt-16(v-if='$refs.filterRef?.filterModel?.feature_system_name')
        dashboard-board-card.km-grid-item-2(header='Most frequent topics')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-bars(:data='topics')
        dashboard-board-card(header='User languages')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-bars(:data='languages')
        dashboard-board-card(header='Copy answer rate', tooltip='How frequently the RAG Tool output is copied by users')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(label='Copy answer rate', :value='data.copyRate')
        //- dashboard-board-card(header='Most frequent next actions')
        //-   template(v-slot:body)
        //-     .column.q-gap-16
        //-       dashboard-board-bars(:data='data.nextActions')
        //- dashboard-board-card(header='Most frequent products')
        //-   template(v-slot:body)
        //-     .column.q-gap-16
        //-       dashboard-board-bars(:data='data.products')
        //- dashboard-board-card(header='Script completion rate')
        //-   template(v-slot:body)
        //-     .column.q-gap-16
        //-       dashboard-board-label-value(label='Script completion rate', :value='data.scriptCompletionRate')
      .km-grid-1.q-mt-16(v-else)
        dashboard-board-card(header='Agent overview')
          template(v-slot:body)
            .column.q-gap-16
              .km-table-compact
                km-table(row-key='name', :rows='rags', :columns='columns', :pagination='{ rowsPerPage: 10 }', @cellAction='cellAction')
  template(v-if='tab === "list"')
    .column.q-gap-16.full-width
      .row
        .col-auto.center-flex-y.full-width
          //km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
          q-space
          .col-auto
            dashboard-board-export-button(@exportToCsv='exportToFile("csv")', @exportToJson='exportToFile("json")')
        q-space
      km-table(
        @selectRow='navigateToConversation($event)',
        selection='single',
        row-key='start_time',
        :rows='visibleRows',
        :selected='selectedRow ? [selectedRow] : []',
        :columns='agentDetailsColumns',
        v-model:pagination='pagination',
        @cellAction='cellAction',
        @request='getDetailedList',
        dense,
        binary-state-sort,
        :filter='activeFilters'
      )
</template>
<script>
import { fetchData } from '@shared'
import { ref } from 'vue'
import filter from '@/config/dashboard/agent-filters'
import controls from '@/config/dashboard/agent-table'
import agentDetailsControls from '@/config/dashboard/agent-details-table'
import { formatDuration } from '@shared/utils'

const naTooltip = 'Data not available because post-processing was not done for this conversation yet'

export default {
  props: ['selectedRow'],
  emits: ['selectRow'],
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
      rags: ref([]),
      controls: ref(controls),
      observability: ref({}),
      detailedList: ref([]),
      agentDetailsControls: ref(agentDetailsControls),
      searchString: ref(''),
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
      return this.$store.getters.config.api.aiBridge.urlAdmin
    },
    columns() {
      return Object.values(this.controls)
    },
    agentDetailsColumns() {
      return Object.values(this.agentDetailsControls).filter((column) => column.display)
    },
    ragTools() {
      return this.$store.getters.chroma.rag_tools.publicItems
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
          { title: 'Customer Portal', value: 1222, action: () => console.log('liked') },
          { title: 'Mobile App', value: 400, action: () => console.log('disliked') },
          { title: 'Other', value: 100, action: () => console.log('disliked') },
        ],
        languages: [
          { title: 'English', value: 1222, action: () => console.log('liked') },
          { title: 'Spanish', value: 400, action: () => console.log('disliked') },
          { title: 'French', value: 100, action: () => console.log('disliked') },
        ],
        copyRate: this.observability?.copy_rate ? `${this.observability.copy_rate.toFixed(2)}%` : '-',
        nextActions: [
          { title: 'Customer Portal', value: 1222, action: () => console.log('liked') },
          { title: 'Mobile App', value: 400, action: () => console.log('disliked') },
          { title: 'Other', value: 100, action: () => console.log('disliked') },
        ],
        products: [
          { title: 'Customer Portal', value: 1222, action: () => console.log('liked') },
          { title: 'Mobile App', value: 400, action: () => console.log('disliked') },
          { title: 'Other', value: 100, action: () => console.log('disliked') },
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
      console.log('observability', this.observability)
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
        // this.$refs.filterRef.clearFilter([
        //   'conversation_data.resolution_status',
        //   'conversation_data.dislikes',
        //   'feedback',
        //   'conversation_data.sentiment',
        //   'conversation_data.language',
        //   'conversation_data.topics',
        // ])
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
  },
  methods: {
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
        window.open(this.$router.resolve({ path: `/conversation/${row.conversation_id}` }).href, '_blank')
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
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      this.rags = await response.json()
    },
    async getObservability() {
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'POST',
        credentials: 'include',
        service: 'observability/monitoring/agent',
        body: JSON.stringify({
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      this.observability = await response.json()
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
        service: `observability/monitoring/agent/export?format=${format}`,
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
          filters: this.activeFilters,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const data = await response.json()
      if (data) {
        this.$store.dispatch('setAgentDashboardOptions', data)
      }
    },

    cellAction(e) {
      if (e.action === 'filterAgent') {
        console.log('filterAgent', e.row)
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
<style lang="stylus"></style>

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
      //- .col-auto(v-if='tab === "overview"')
      //-   .row.items-center.q-gap-4
      //-     q-icon.col-auto(name='o_info', color='secondary')
      //-     .km-description Showing only production data

  .col-12
    template(v-if='tab === "overview"')
      .km-grid-2
        dashboard-board-card(header='Usage', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(label='Total tool calls', :value='data.totalCalls')
              dashboard-board-label-value(label='Unique users', :value='data.uniqueUsers')
        dashboard-board-card(header='Performance & cost', theme='dark')
          template(v-slot:body)
            .column.q-gap-16
              .row
                .col
                  dashboard-board-label-value(
                    label='Avg. tool call cost',
                    :value='data.avgCost',
                    tooltip='How much one RAG Tool call costs on average'
                  )
                .col
                  dashboard-board-label-value(label='Total tool cost', :value='data.totalCost')
              dashboard-board-label-value(
                label='Avg. tool call latency',
                :value='data.avgLatency',
                tooltip='How long one RAG Tool call takes on average'
              )
        dashboard-board-card(header='Answer rate')
          template(v-slot:body)
            .column.q-gap-16
              dashboard-board-label-value(label='Answer rate', :value='answerRate')
              .row
                dashboard-board-label-value(label='Answer ratio') 
              //- dashboard-board-bars(:data='data.questions')
              template(v-if='questionsDiagram.length')
                dashboard-board-box-diagram(:data='questionsDiagram')
              template(v-else)
                dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
              dashboard-board-min-label-value(
                label='RAG Queries analyzed',
                :value='processRate.processed',
                tooltip='Number of answers processed out of total questions'
              )
        dashboard-board-card(header='User satisfaction')
          template(v-slot:body)
            .column.q-gap-16.fit
              .row
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
                    :data='[ { title: "Liked", value: data.likes, icon: "fas fa-thumbs-up", iconColor: "like-text", backgroundColor: "like-bg", action: () => setFilterAndNavigate("extra_data.answer_feedback.type", { label: "Like", value: "like" }) }, { title: "Disliked", value: data.dislikes, icon: "fas fa-thumbs-down", iconColor: "error-text", backgroundColor: "dislike-bg", action: () => setFilterAndNavigate("extra_data.answer_feedback.type", { label: "Dislike", value: "dislike" }) }, ]'
                  )
                template(v-else)
                  dashboard-board-box-diagram(:data='[{ title: "N/A", icon: null, backgroundColor: "table-header" }]')
              dashboard-board-min-label-value(
                label='Feedback rate',
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
        @selectRow='$emit("selectRow", $event)',
        selection='single',
        row-key='start_time',
        :rows='visibleRows',
        :selected='selectedRow ? [selectedRow] : []',
        :columns='ragDetailsColumns',
        v-model:pagination='pagination',
        @cellAction='cellAction',
        @request='getDetailedList',
        :loading='loading',
        :filter='activeFilters',
        binary-state-sort
      )
</template>
<script>
import { fetchData } from '@shared'
import { ref } from 'vue'
import filter from '@/config/dashboard/rag-filters'
import controls from '@/config/dashboard/rag-table'
import ragDetailsControls from '@/config/dashboard/rag-details-table'
import { formatDuration } from '@shared/utils'

const naTooltip = 'Data not available because post-processing was not enabled'

export default {
  props: ['selectedRow'],
  emits: ['selectRow'],

  data() {
    return {
      loading: ref(false),
      listFilter: ref(filter),
      summaryFilter: ref(Object.fromEntries(Object.entries(filter))),
      activeFilters: ref({}),
      tab: ref('list'),
      tabs: ref([
        { name: 'list', label: 'List' },
        { name: 'overview', label: 'Summary' },
      ]),
      //selectedRow: ref(null),
      rags: ref([]),
      controls: ref(controls),
      observability: ref({}),
      detailedList: ref([]),
      ragDetailsControls: ref(ragDetailsControls),
      searchString: ref(''),
      // topicOptions: ref([]),
      // languageOptions: ref([]),
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
    ragDetailsColumns() {
      return Object.values(this.ragDetailsControls).filter((column) => column.display)
    },
    ragTools() {
      return this.$store.getters.chroma.rag_tools.publicItems
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
        // this.$refs.filterRef.clearFilter([
        //   //'channel',
        //   'extra_data.is_answered',
        //   'extra_data.language',
        //   'extra_data.topic',
        //   'extra_data.answer_feedback.type',
        // ])
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
        //no_results: 'Nothing retrieved, not answered',
      }
      const tooltips = {
        true: 'Questions where the model generated a response.',
        false: 'Questions where chunks of content were retrieved, but content was not sufficient or relevant for the model to generate response.',
        //no_results: 'Questions where no chunks of content were retrieved, therefore response could not be generated.',
      }
      const bg = {
        true: 'question_answered',
        false: 'dislike-bg',
        //no_results: 'no_results',
      }
      const color = {
        true: 'like-text',
        false: 'error-text',
        //no_results: 'no_results',
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
      const data = await response.json()
      this.$store.dispatch('setRagDashboardOptions', data)
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
      const data = await response.json()
      this.observability = data
      //      this.$store.dispatch('setRagDashboardOptions', this.rags.map((rag) => ({ label: rag.name, value: rag.name })))
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
        service: 'observability/monitoring/rag/list',
        credentials: 'include',
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
      console.log('detailedList', this.detailedList.length)
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
        console.log('drilldown', e.row)
        this.$refs.filterRef.setFilter('feature_system_name', { label: e.row.name, value: e.row.name })
      } else if (e.action === 'select') {
        this.$emit('selectRow', e.row)
      }
    },

    setFilter(key, { label, value }) {
      //this.$refs.filterRef.updateVisibleFilters({ value: key })
      this.$refs.filterRef.setFilter(key, { label, value })
    },
    setFilterAndNavigate(key, { label, value }) {
      console.log('setFilterAndNavigate', key, label, value)
      this.tab = 'list'
      this.listFilter = { ...this.listFilter, [key]: { ...this.listFilter[key], ['is_hidden']: false } }
      // this.$refs.filterRef.clearFilter([
      //   // 'channel',
      //   'extra_data.is_answered',
      //   'extra_data.language',
      //   'extra_data.topic',
      //   'extra_data.answer_feedback.type',
      // ])
      this.setFilter(key, { label, value })
    },
  },
}
</script>

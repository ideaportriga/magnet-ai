<template lang="pug">
.column.no-wrap.bg-white.fit.bl-border.height-100.fit(style='min-width: 500px; max-width: 500px', v-if='!!selectedRow')
  .col.q-pt-16.overflow-hidden
    .row.no-wrap.full-width.q-px-16
      q-tabs.bb-border.full-width(
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
        .fit
        q-btn(icon='close', flat, dense, @click='$emit("close")')
    .column.fit.no-wrap.q-pb-xl
      q-scroll-area.q-px-16.q-py-16.fit
        template(v-if='tab == "details"')
          .column.q-gap-16
            .col-6
              .km-description.text-secondary-text.q-pb-6 Tool Name
              .row.q-gap-8.items-center
                .km-label {{ selectedRow?.name }}
                q-icon.cursor-pointer(name='fa fa-external-link', color='secondary', size='10', @click='openRag', v-if='selectedRow?.feature_id')
                km-chip.text-grey.q-ml-sm(:label='variant', color='in-progress')
            .col-6
              .km-description.text-secondary-text.q-pb-6 Consumer type
              .row.q-gap-8.items-center
                .km-label {{ selectedRow?.source ?? '-' }}
                //- km-chip.text-grey.q-ml-sm(:label='selectedRow?.extra_data?.used_by_type ?? "-"', color='in-progress')
            .col-6
              .km-description.text-secondary-text.q-pb-6 Request Time
              .row
                .km-label {{ time }}
            //- .col-6
            //-   .km-description.text-secondary-text.q-pb-6 Source
            //-   .row
            //-     .km-label.text-capitalize {{ selectedRow?.source ?? '-' }}

            .col-6
              .km-description.text-secondary-text.q-pb-6 Question
              .row
                .km-label {{ selectedRow?.extra_data?.question ?? '-' }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Response
              .row
                dashboard-markdown(:source='selectedRow?.extra_data?.answer ?? "-"')
                //.km-label {{ selectedRow?.extra_data?.answer ?? '-' }}

        template(v-if='tab == "costs"')
          .column.q-gap-16
            .col-6
              .km-description.text-secondary-text.q-pb-6 Cost
              .row
                .km-label {{ cost }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Latency
              .row
                .km-label {{ duration }}
        template(v-if='tab == "insights"')
          .column.q-gap-16
            .km-button-text.bb-border.q-pb-4 Post-processing results
            .col-6
              .km-description.text-secondary-text Topic
              .row
                km-input.full-width(v-model='item.extra_data.topic')
            .col-6
              .km-description.text-secondary-text Language
              .row
                km-input.full-width(v-model='item.extra_data.language')
            .col-6
              .km-description.text-secondary-text Answered
              .row
                km-select.full-width(v-model='answered', :options='answeredOptions')
            .col-6(v-if='!this.item?.extra_data?.is_answered')
              .km-description.text-secondary-text.q-pb-6 Not answered reason
              .row
                km-select.full-width(v-model='answerReason', :options='resolutionOptions')

            .km-button-text.bb-border.q-pb-4 User satisfaction
            .col-6
              .km-description.text-secondary-text User feedback
              .row
                .km-label.text-capitalize {{ selectedRow?.extra_data?.answer_feedback?.type ?? '-' }}
            .col-6
              .km-description.text-secondary-text Feedback reason
              .row
                .km-label.text-capitalize {{ dislikeReason }}
            .col-6
              .km-description.text-secondary-text Feedback comment
              .row
                .km-label {{ selectedRow?.extra_data?.answer_feedback?.comment ?? '-' }}
            .col-6
              .km-description.text-secondary-text Copied
              .row
                .km-label {{ selectedRow?.extra_data?.answer_copy ? 'Yes' : 'No' }}
            .km-button-text.bb-border.q-pb-4 Substandard Result analysis
            .col-6
              .km-description.text-secondary-text Substandard Result Reason
              .row
                km-select.full-width(v-model='resultReason', :options='substandartResultReasons')
            .col-6
              .km-description.text-secondary-text Comment
              .row
                km-input.full-width.q-pb-16(autogrow, :rows='3', type='textarea', v-model='item.extra_data.comment')
  .row.items-center.q-pa-16.justify-between.bt-border(v-if='selectedRow?.trace_id || isUpdated')
    .row.items-center.q-gap-8.cursor-pointer(@click='openDetails', v-if='selectedRow?.trace_id')
      km-btn(flat, label='View trace', icon='fa fa-external-link', color='secondary-text', labelClass='km-button-text', iconSize='16px')

    .col-auto
    .row.items-center.q-gap-8
      km-btn.self-end(label='Cancel', @click='cancelUpdate', v-if='isUpdated', flat)
      km-btn.self-end(label='Update', @click='updateAnalytics', v-if='isUpdated')
</template>
<script>
import _ from 'lodash'
import { ref } from 'vue'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import { fetchData } from '@shared'
export default {
  props: ['selectedRow'],
  emits: ['close', 'refresh'],
  setup() {
    return {
      item: ref(null),
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: 'Details' },
        { name: 'costs', label: 'Cost & Latency' },
        { name: 'insights', label: 'Insights' },
      ]),
      substandartResultReasons: ref([
        { label: 'Knowledge source quality', value: 'knowledge_source_quality' },
        { label: 'Parsing issue', value: 'parsing_issue' },
        { label: 'Chunking issue', value: 'chunking_issue' },
        { label: 'Retrieval issue', value: 'retrieval_issue' },
        { label: 'Generation issue', value: 'generation_issue' },
        { label: 'User question', value: 'user_question' },
      ]),
      answeredOptions: ref([
        { label: 'Yes', value: true },
        { label: 'No', value: false },
      ]),
      resolutionOptions: ref([
        { label: 'Non-relevant content', value: 'question_not_answered' },
        { label: 'No content retrieved', value: 'no_results' },
      ]),
    }
  },

  computed: {
    answered: {
      get() {
        if (this.item?.extra_data?.is_answered) {
          return { label: 'Yes', value: true }
        }
        return { label: 'No', value: false }
      },
      set(option) {
        this.item.extra_data.is_answered = option.value
      },
    },
    answerReason: {
      get() {
        if (this.item?.extra_data?.resolution) {
          return this.resolutionOptions.find((option) => option.value === this.item?.extra_data?.resolution)
        }
        return '-'
      },
      set(option) {
        this.item.extra_data.resolution = option.value
      },
    },
    resultReason: {
      get() {
        if (this.item?.extra_data?.substandart_result_reason) {
          return this.substandartResultReasons.find((option) => option.value === this.item?.extra_data?.substandart_result_reason)
        }
        return '-'
      },
      set(option) {
        this.item.extra_data.substandart_result_reason = option.value
      },
    },
    duration() {
      if (this.selectedRow?.latency) {
        return formatDuration(this.selectedRow?.latency)
      }
      return '-'
    },
    cost() {
      if (this.selectedRow?.cost) {
        return `${Number(this.selectedRow?.cost).toFixed(6)} $`
      }
      return '-'
    },
    time() {
      if (this.selectedRow?.start_time) {
        return formatDateTime(this.selectedRow?.start_time)
      }
      return '-'
    },
    variant() {
      if (this.selectedRow?.variant) {
        return this.selectedRow.variant.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
      }
      return '-'
    },
    dislikeReason() {
      const reason = this.selectedRow?.extra_data?.answer_feedback?.reason
      if (reason) {
        return reason.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
      }
      return '-'
    },
    isUpdated() {
      return !_.isEqual(this.item, this.selectedRow)
    },
    endpoint() {
      return this.$store.getters.config.api.aiBridge.urlAdmin
    },
  },
  watch: {
    selectedRow: {
      handler(newVal) {
        this.item = _.cloneDeep(newVal)
      },
      immediate: true,
    },
  },
  methods: {
    openDetails() {
      window.open(this.$router.resolve({ path: `/observability-traces/${this.selectedRow.trace_id}` }).href, '_blank')
    },
    openRag() {
      window.open(this.$router.resolve({ path: `/rag-tools/${this.selectedRow.feature_id}` }).href, '_blank')
    },
    async updateAnalytics() {
      const body = {}
      if (this.item.extra_data.topic !== this.selectedRow.extra_data.topic) {
        body.topic = this.item.extra_data.topic
      }
      if (this.item.extra_data.language !== this.selectedRow.extra_data.language) {
        body.language = this.item.extra_data.language
      }
      if (this.item.extra_data.is_answered !== this.selectedRow.extra_data.is_answered) {
        body.is_answered = this.item.extra_data.is_answered
      }
      if (this.item.extra_data.resolution !== this.selectedRow.extra_data.resolution) {
        body.resolution = this.item.extra_data.resolution
      }
      if (this.item.extra_data.substandart_result_reason !== this.selectedRow.extra_data.substandart_result_reason) {
        body.substandart_result_reason = this.item.extra_data.substandart_result_reason
      }
      if (this.item.extra_data.comment !== this.selectedRow.extra_data.comment) {
        body.comment = this.item.extra_data.comment
      }

      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'PUT',
        credentials: 'include',
        service: `observability/monitoring/analytics/${this.selectedRow._id}`,
        body: JSON.stringify(body),
      })
      const data = await response.json()
      console.log(data)
      this.$emit('refresh')
    },
    cancelUpdate() {
      this.item = _.cloneDeep(this.selectedRow)
    },
  },
}
</script>

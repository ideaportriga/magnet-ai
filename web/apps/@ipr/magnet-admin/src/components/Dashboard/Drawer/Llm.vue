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
              .km-description.text-secondary-text.q-pb-6 Request Type
              .row
                .km-label {{ requestType }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Consumer
              .row
                .km-label {{ selectedRow?.consumer_name }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Consumer type
              .row
                .km-label {{ selectedRow?.source }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Request time
              .row
                .km-label {{ time }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Status
              .row
                .km-label.text-capitalize {{ selectedRow?.status }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Model
              .row
                .km-label {{ selectedRow?.extra_data?.model_details?.display_name }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Prompt Template
              .row
                .km-label {{ selectedRow?.feature_name }}
                km-chip.text-grey.q-ml-sm(:label='templateVariant', color='in-progress')

        template(v-if='tab == "costs"')
          .column
            .row.q-pb-16
              .col-6
                .km-description.text-secondary-text.q-pb-6 Latency
                .row
                  .km-label {{ latency }}
              .col-6
                .km-description.text-secondary-text.q-pb-6
                .row
                  .km-label
            .row
              .col-6
                template(
                  v-if='selectedRow?.feature_type === "prompt-template" || selectedRow?.feature_type === "chat-completion-api" || selectedRow?.feature_type === "embedding-api"'
                )
                  .km-description.text-secondary-text.q-pb-6 Total tokens
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.total }}
                template(v-else)
                  .km-description.text-secondary-text.q-pb-6 Total usage
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.total }} queries
              .col-6
                .km-description.text-secondary-text.q-pb-6 Total cost
                .row
                  .km-label {{ formatCost(selectedRow?.extra_data?.cost_details?.total) }}
            template(v-if='selectedRow?.feature_type === "prompt-template" || selectedRow?.feature_type === "chat-completion-api"')
              .row
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Standard input
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.input_details.standard }}
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Standard input cost
                  .row
                    .km-label {{ formatCost(selectedRow?.extra_data?.cost_details?.input_details.standard) }}
              .row
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Cached input
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.input_details.cached }}
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Cached input cost
                  .row
                    .km-label {{ formatCost(selectedRow?.extra_data?.cost_details?.input_details.cached) }}
              .row
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Standard output
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.output_details.standard }}
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Standard output cost
                  .row
                    .km-label {{ formatCost(selectedRow?.extra_data?.cost_details?.output_details.standard) }}
              .row
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Reasoning output
                  .row
                    .km-label {{ selectedRow?.extra_data?.usage_details?.output_details?.reasoning }}
                .col-6
                  .km-description.text-secondary-text.q-pb-6 Reasoning output cost
                  .row
                    .km-label {{ formatCost(selectedRow?.extra_data?.cost_details?.output_details?.reasoning) }}
        template(v-if='tab === "input_output"')
          template(v-if='selectedRow?.feature_type === "prompt-template" || selectedRow?.feature_type === "chat-completion-api"')
            observability-traces-chat-completion-input-output(:span='selectedRow.extra_data')
          template(v-else-if='selectedRow?.feature_type === "embedding-api"')
            observability-traces-embed-input-output(:span='selectedRow.extra_data')
          template(v-else-if='selectedRow?.feature_type === "reranking-api"')
            observability-traces-rerank-input-output(:span='selectedRow.extra_data')
        template(v-if='tab == "insights"')
          .column.q-gap-16
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
import { formatDuration, featureTypeToRequestType } from '@shared/utils'
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
        { name: 'input_output', label: 'Inputs & Outputs' },
        { name: 'insights', label: 'Insights' },
      ]),
      substandartResultReasons: ref([
        { label: 'Prompt issue', value: 'prompt_issue' },
        { label: 'Model limitation', value: 'model_limitation' },
        { label: 'Hallucination', value: 'hallucination' },
        { label: 'Format issue', value: 'format_issue' },
        { label: 'Incorrect output', value: 'incorrect_output' },
      ]),
      formatDuration,
    }
  },

  computed: {
    requestType() {
      return featureTypeToRequestType(this.selectedRow.feature_type) || '-'
    },
    time() {
      if (this.selectedRow?.start_time) {
        return formatDateTime(this.selectedRow?.start_time)
      }
      return '-'
    },
    templateVariant() {
      if (!this.selectedRow?.feature_variant) return '-'
      const variantString = this.selectedRow.feature_variant.replace(/_/g, ' ')
      return variantString.charAt(0).toUpperCase() + variantString.slice(1)
    },
    latency() {
      if (!this.selectedRow?.latency) return '-'
      return formatDuration(this.selectedRow?.latency)
    },
    dislikeReason() {
      const reason = this.selectedRow?.extra_data?.answer_feedback?.reason
      if (reason) {
        return reason.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
      }
      return '-'
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
    formatCost(val) {
      if (typeof val !== 'number') return '-'
      return `${val.toFixed(6)} $`
    },
    async updateAnalytics() {
      const body = {}
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
      await response.json()
      this.$emit('refresh')
    },
    cancelUpdate() {
      this.item = _.cloneDeep(this.selectedRow)
    },
  },
}
</script>

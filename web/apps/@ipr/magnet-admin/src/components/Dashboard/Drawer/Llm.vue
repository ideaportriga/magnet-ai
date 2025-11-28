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

  .row.items-center.q-pa-16.justify-between.bt-border(v-if='selectedRow?.trace_id || isUpdated')
    .row.items-center.q-gap-8.cursor-pointer(@click='openDetails', v-if='selectedRow?.trace_id')
      km-btn(flat, label='View trace', icon='fa fa-external-link', color='secondary-text', labelClass='km-button-text', iconSize='16px')
</template>
<script>
import _ from 'lodash'
import { ref } from 'vue'
import { formatDuration, featureTypeToRequestType } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'

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
  },
}
</script>

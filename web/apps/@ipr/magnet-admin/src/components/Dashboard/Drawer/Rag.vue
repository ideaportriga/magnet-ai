<template>
  <km-drawer-layout v-if="!!selectedRow" storage-key="drawer-dashboard-rag">
    <template #tabs>
      <div class="pt-lg px-lg">
        <div class="cluster" data-wrap="no">
          <km-tabs v-model="tab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
            <template v-for="t in tabs" :key="t">
              <km-tab :name="t.name" :label="t.label" />
            </template>
          </km-tabs>
          <km-btn class="ml-sm" icon="close" flat dense @click="$emit(&quot;close&quot;)" />
        </div>
      </div>
    </template>
    <template v-if="tab == &quot;details&quot;">
      <div class="dashboard-rag-drawer__grid">
        <div>
          <div class="km-description text-secondary-text pb-sm">Tool Name</div>
          <div class="cluster" data-gap="sm">
            <div class="km-label">{{ selectedRow?.name }}</div>
            <km-glyph v-if="selectedRow?.feature_id" class="cursor-pointer" name="external-link" size="10" @click="openRag" />
            <km-chip class="text-grey ml-sm" :label="variant" tone="neutral" />
          </div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Consumer type</div>
          <div class="km-label">{{ selectedRow?.source ?? '-' }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Request Time</div>
          <div class="km-label">{{ time }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Question</div>
          <div class="km-label">{{ selectedRow?.extra_data?.question ?? '-' }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Response</div>
          <dashboard-markdown :source="selectedRow?.extra_data?.answer ?? &quot;-&quot;" />
        </div>
      </div>
    </template>
    <template v-if="tab == &quot;costs&quot;">
      <div class="dashboard-rag-drawer__grid">
        <div>
          <div class="km-description text-secondary-text pb-sm">Cost</div>
          <div class="km-label">{{ cost }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Latency</div>
          <div class="km-label">{{ duration }}</div>
        </div>
      </div>
    </template>
    <template v-if="tab == &quot;insights&quot;">
      <div class="dashboard-rag-drawer__grid">
        <div class="dashboard-rag-drawer__section-title km-button-text bb-border pb-xs">Post-processing results</div>
        <div>
          <div class="km-description text-secondary-text">Topic</div>
          <km-input v-model="item.extra_data.topic" class="full-width" />
        </div>
        <div>
          <div class="km-description text-secondary-text">Language</div>
          <km-input v-model="item.extra_data.language" class="full-width" />
        </div>
        <div>
          <div class="km-description text-secondary-text">Answered</div>
          <km-select v-model="answered" class="full-width" :options="answeredOptions" />
        </div>
        <div v-if="!item?.extra_data?.is_answered">
          <div class="km-description text-secondary-text pb-sm">Not answered reason</div>
          <km-select v-model="answerReason" class="full-width" :options="resolutionOptions" />
        </div>
        <div class="dashboard-rag-drawer__section-title km-button-text bb-border pb-xs">User satisfaction</div>
        <div>
          <div class="km-description text-secondary-text">User feedback</div>
          <div class="km-label text-capitalize">{{ selectedRow?.extra_data?.answer_feedback?.type ?? '-' }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text">Feedback reason</div>
          <div class="km-label text-capitalize">{{ dislikeReason }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text">Feedback comment</div>
          <div class="km-label">{{ selectedRow?.extra_data?.answer_feedback?.comment ?? '-' }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text">Copied</div>
          <div class="km-label">{{ selectedRow?.extra_data?.answer_copy ? 'Yes' : 'No' }}</div>
        </div>
        <div class="dashboard-rag-drawer__section-title km-button-text bb-border pb-xs">Substandard Result analysis</div>
        <div>
          <div class="km-description text-secondary-text">Substandard Result Reason</div>
          <km-select v-model="resultReason" class="full-width" :options="substandartResultReasons" />
        </div>
        <div>
          <div class="km-description text-secondary-text">Comment</div>
          <div class="km-textarea-relaxed">
            <km-input v-model="item.extra_data.comment" class="full-width pb-lg" autogrow :rows="3" type="textarea" />
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div v-if="selectedRow?.trace_id || isUpdated" class="cluster" data-justify="between">
        <div v-if="selectedRow?.trace_id" class="cluster cursor-pointer" data-gap="sm" @click="openDetails">
          <km-btn flat label="View trace" icon="external-link" tone="subtle" label-class="km-button-text" icon-size="16px" />
        </div>
        <div class="km-space" />
        <div class="cluster" data-gap="sm">
          <km-btn v-if="isUpdated" class="self-end" :label="m.common_cancel()" flat @click="cancelUpdate" />
          <km-btn v-if="isUpdated" class="self-end" :label="m.common_update()" @click="updateAnalytics" />
        </div>
      </div>
    </template>
  </km-drawer-layout>
</template>
<script>
import _ from 'lodash'
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'
import { fetchData } from '@shared'
export default {
  props: ['selectedRow'],
  emits: ['close', 'refresh'],
  setup() {
    return {
      m,
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
      return this.$appConfig.api.aiBridge.urlAdmin
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
      this.$router.push(`/observability-traces/${this.selectedRow.trace_id}`)
    },
    openRag() {
      this.$router.push(`/rag-tools/${this.selectedRow.feature_id}`)
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
      if (response.error || !response.ok) return
      const data = await response.json()
      this.$emit('refresh')
    },
    cancelUpdate() {
      this.item = _.cloneDeep(this.selectedRow)
    },
  },
}
</script>

<style scoped>
.dashboard-rag-drawer__grid {
  display: grid;
  gap: var(--ds-space-lg);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dashboard-rag-drawer__section-title {
  grid-column: 1 / -1;
}

@media (max-width: 767px) {
  .dashboard-rag-drawer__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

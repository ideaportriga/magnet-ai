<template>
  <km-drawer-layout v-if="!!selectedRow" storage-key="drawer-dashboard-llm">
    <template #tabs>
      <div class="pt-lg px-lg">
        <km-tabs v-model="tab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
          <km-btn icon="close" flat dense @click="$emit(&quot;close&quot;)" />
        </km-tabs>
      </div>
    </template>
    <template v-if="tab == &quot;details&quot;">
      <div class="dashboard-llm-drawer__grid">
        <div>
          <div class="km-description text-secondary-text pb-sm">Request Type</div>
          <div class="km-label">{{ requestType }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Consumer</div>
          <div class="km-label">{{ selectedRow?.consumer_name }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Consumer type</div>
          <div class="km-label">{{ selectedRow?.source }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Request time</div>
          <div class="km-label">{{ time }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Status</div>
          <div class="km-label text-capitalize">{{ selectedRow?.status }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Model</div>
          <div class="km-label">{{ selectedRow?.extra_data?.model_details?.display_name }}</div>
        </div>
        <div>
          <div class="km-description text-secondary-text pb-sm">Prompt Template</div>
          <div class="cluster">
            <div class="km-label">{{ selectedRow?.feature_name }}</div>
            <km-chip class="text-grey ml-sm" :label="templateVariant" tone="neutral" />
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab == &quot;costs&quot;">
      <div>
        <div class="dashboard-llm-drawer__grid dashboard-llm-drawer__grid--spaced">
          <div>
            <div class="km-description text-secondary-text pb-sm">Latency</div>
            <div class="km-label">{{ latency }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm" />
            <div class="km-label" />
          </div>
        </div>
        <div class="dashboard-llm-drawer__grid">
          <div>
            <template v-if="selectedRow?.feature_type === 'prompt-template' || selectedRow?.feature_type === &quot;chat-completion-api&quot; || selectedRow?.feature_type === &quot;embedding-api&quot;">
              <div class="km-description text-secondary-text pb-sm">Total tokens</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.total }}</div>
            </template>
            <template v-else>
              <div class="km-description text-secondary-text pb-sm">Total usage</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.total }} queries</div>
            </template>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Total cost</div>
            <div class="km-label">{{ formatCost(selectedRow?.extra_data?.cost_details?.total) }}</div>
          </div>
        </div>
        <template v-if="selectedRow?.feature_type === &quot;prompt-template&quot; || selectedRow?.feature_type === &quot;chat-completion-api&quot;">
          <div class="dashboard-llm-drawer__grid">
            <div>
              <div class="km-description text-secondary-text pb-sm">Standard input</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.input_details.standard }}</div>
            </div>
            <div>
              <div class="km-description text-secondary-text pb-sm">Standard input cost</div>
              <div class="km-label">{{ formatCost(selectedRow?.extra_data?.cost_details?.input_details.standard) }}</div>
            </div>
          </div>
          <div class="dashboard-llm-drawer__grid">
            <div>
              <div class="km-description text-secondary-text pb-sm">Cached input</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.input_details.cached }}</div>
            </div>
            <div>
              <div class="km-description text-secondary-text pb-sm">Cached input cost</div>
              <div class="km-label">{{ formatCost(selectedRow?.extra_data?.cost_details?.input_details.cached) }}</div>
            </div>
          </div>
          <div class="dashboard-llm-drawer__grid">
            <div>
              <div class="km-description text-secondary-text pb-sm">Standard output</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.output_details.standard }}</div>
            </div>
            <div>
              <div class="km-description text-secondary-text pb-sm">Standard output cost</div>
              <div class="km-label">{{ formatCost(selectedRow?.extra_data?.cost_details?.output_details.standard) }}</div>
            </div>
          </div>
          <div class="dashboard-llm-drawer__grid">
            <div>
              <div class="km-description text-secondary-text pb-sm">Reasoning output</div>
              <div class="km-label">{{ selectedRow?.extra_data?.usage_details?.output_details?.reasoning }}</div>
            </div>
            <div>
              <div class="km-description text-secondary-text pb-sm">Reasoning output cost</div>
              <div class="km-label">{{ formatCost(selectedRow?.extra_data?.cost_details?.output_details?.reasoning) }}</div>
            </div>
          </div>
        </template>
      </div>
    </template>
    <template v-if="tab === &quot;input_output&quot;">
      <template v-if="selectedRow?.feature_type === &quot;prompt-template&quot; || selectedRow?.feature_type === &quot;chat-completion-api&quot;">
        <observability-traces-chat-completion-input-output :span="selectedRow.extra_data" />
      </template>
      <template v-else-if="selectedRow?.feature_type === &quot;embedding-api&quot;">
        <observability-traces-embed-input-output :span="selectedRow.extra_data" />
      </template>
      <template v-else-if="selectedRow?.feature_type === &quot;reranking-api&quot;">
        <observability-traces-rerank-input-output :span="selectedRow.extra_data" />
      </template>
    </template>
    <template #footer>
      <div v-if="selectedRow?.trace_id || isUpdated" class="cluster" data-justify="between">
        <div v-if="selectedRow?.trace_id" class="cluster cursor-pointer" data-gap="sm" @click="openDetails">
          <km-btn flat label="View trace" icon="external-link" tone="subtle" label-class="km-button-text" icon-size="16px" />
        </div>
      </div>
    </template>
  </km-drawer-layout>
</template>
<script>
import _ from 'lodash'
import { m } from '@/paraglide/messages'
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
      this.$router.push(`/observability-traces/${this.selectedRow.trace_id}`)
    },
    formatCost(val) {
      if (typeof val !== 'number') return '-'
      return `${val.toFixed(6)} $`
    },
  },
}
</script>

<style scoped>
.dashboard-llm-drawer__grid {
  display: grid;
  gap: var(--ds-space-lg);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dashboard-llm-drawer__grid--spaced {
  padding-block-end: var(--ds-space-lg);
}

@media (max-width: 767px) {
  .dashboard-llm-drawer__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

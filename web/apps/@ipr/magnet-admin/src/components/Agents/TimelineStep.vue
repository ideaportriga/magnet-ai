<template>
  <km-timeline-entry :key="step.started_at" :icon="step.icon" :tone="isExpanded ? &quot;success&quot; : &quot;brand&quot;">
    <template #subtitle>
      <div class="cluster timeline-step__row" data-justify="between">
        <div class="flex-1 mr-md">
          <km-chip label-class="km-heading-2" flat dense icon-size="16px" @click="step.type === &quot;classification&quot; || (step.type === &quot;topic_completion&quot; &amp;&amp; !step?.details?.action_call_requests) ? null : toggleExpand()">
            <div class="cluster full-width" data-justify="center">
              <km-glyph v-if="!(step.type === &quot;classification&quot; || (step.type === &quot;topic_completion&quot; &amp;&amp; !step?.details?.action_call_requests))" name="chevron-right" flat class="timeline-step__chevron" :data-expanded="isExpanded ? 'true' : 'false'" />
              <div class="ml-sm text-secondary-text cursor-pointer">{{ step?.typeLabel }}</div>
            </div>
          </km-chip>
        </div>
        <div class="flex-none mr-md km-field">{{ step?.duration_seconds }}</div>
      </div>
    </template>
    <div class="stack" data-gap="sm">
      <template v-if="step.type === &quot;classification&quot;">
        <div class="flex-1">
          <div class="cluster">
            <div class="agents-timeline-step__label flex-none mr-md">
              <div class="km-field text-secondary-text">{{ m.agents_intent() }}</div>
            </div>
            <div class="flex-1 km-flex-min-w-0">
              <km-chip :label="step.details.intent" tone="neutral" />
            </div>
          </div>
        </div>
        <div v-if="step.details?.topic" class="flex-1">
          <div class="cluster">
            <div class="agents-timeline-step__label flex-none mr-md">
              <div class="km-field text-secondary-text">{{ m.agents_topic() }}</div>
            </div>
            <div class="flex-1 km-flex-min-w-0">
              <km-chip :label="step.details?.topic" tone="neutral" />
            </div>
          </div>
        </div>
        <div class="flex-1">
          <div class="cluster">
            <div class="flex-none mr-md">
              <div class="km-field text-secondary-text">{{ m.agents_reason() }}</div>
            </div>
            <div class="flex-1 km-flex-min-w-0">{{ step.details.reason }}</div>
          </div>
        </div>
      </template>
      <template v-else-if="step.type === &quot;topic_completion&quot;">
        <div class="flex-1">
          <div class="cluster">
            <div class="flex-none mr-md">
              <div class="km-field text-secondary-text">{{ m.agents_topic() }}</div>
            </div>
            <div class="flex-1 km-flex-min-w-0">{{ step.details.topic.name }}</div>
          </div>
        </div>
        <div class="flex-1">
          <div class="cluster">
            <div class="flex-none mr-md">
              <div class="km-field text-secondary-text">{{ m.agents_topicDescription() }}</div>
            </div>
            <div class="flex-1 km-flex-min-w-0">{{ step.details.topic.description }}</div>
          </div>
          <div v-if="step.details?.action_call_requests" class="mt-sm">
            <div v-if="isExpanded &amp;&amp; step.details?.action_call_requests" class="mt-sm">
              <div v-for="(rq, rqIndex) in step.details?.action_call_requests" :key="rqIndex" class="text-secondary-text">
                <div class="cluster mb-sm">
                  <km-chip :label="rq.action_type" tone="neutral" />
                  <div class="ml-sm">{{ rq.function_name }}</div>
                </div>
                <div class="km-field text-secondary-text">{{ m.agents_request() }}</div>
                <km-codemirror :model-value="stringify(rq?.arguments)" readonly class="timeline-step__codemirror--md" />
              </div>
            </div>
          </div>
        </div>
      </template>
      <template v-else-if="step.type === &quot;topic_action_call&quot;">
        <div v-if="step.details" class="mt-sm">
          <div class="text-secondary-text">
            <div class="cluster mb-sm">
              <km-chip :label="step.details.request.action_type" tone="neutral" />
              <div class="ml-sm">{{ step.details.request.function_name }}</div>
            </div>
            <div v-if="step.details?.request &amp;&amp; !isExpanded" class="km-field text-secondary-text">
              {{ m.agents_request() }}
              <km-codemirror :model-value="stringify(step.details.request.arguments)" readonly class="timeline-step__codemirror--sm" />
            </div>
          </div>
        </div>
        <div v-if="step.details">
          <km-slide-transition>
            <div v-if="step.details?.request &amp;&amp; isExpanded">
              <div class="km-field text-secondary-text">{{ m.agents_request() }}</div>
              <km-codemirror :model-value="stringify(step?.details?.request)" readonly class="timeline-step__codemirror--md" />
              <div class="km-field text-secondary-text">{{ m.agents_response() }}</div>
              <km-codemirror :model-value="stringify(step?.details?.response)" readonly class="timeline-step__codemirror--md" />
            </div>
          </km-slide-transition>
        </div>
      </template>
      <teplate v-else>
        <km-codemirror :model-value="step.detailsJSON" class="timeline-step__codemirror--lg" readonly />
      </teplate>
    </div>
  </km-timeline-entry>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
export default {
  props: {
    step: Object,
  },
  setup() {
    return {
      m,
      isExpanded: ref(false),
    }
  },
  methods: {
    stringify(obj) {
      return JSON.stringify(obj, null, 2)
    },
    toggleExpand() {
      this.isExpanded = !this.isExpanded
    },
  },
}
</script>

<style scoped>
.agents-timeline-step__label {
  flex: 0 0 8.3333%;
  max-inline-size: 8.3333%;
}

.timeline-step__row {
  text-transform: none;
}

.timeline-step__chevron {
  transition: transform var(--ds-duration-base) var(--ds-ease-out);
}
.timeline-step__chevron[data-expanded='true'] {
  transform: rotate(90deg);
}

.timeline-step__codemirror--sm {
  min-block-size: 50px;
}
.timeline-step__codemirror--md {
  min-block-size: 100px;
}
.timeline-step__codemirror--lg {
  max-block-size: 300px;
}
</style>

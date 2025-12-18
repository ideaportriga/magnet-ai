<template lang="pug">
q-dialog(:model-value='modelValue', @update:model-value='$emit("update:modelValue", $event)', maximized)
  q-card(v-if='run')
    q-card-section.row.items-center.bg-primary.text-white
      .text-h6 Run Details: {{ run.id }}
      q-space
      q-btn(icon='close', flat, round, dense, v-close-popup)

    q-card-section
      .row.q-col-gutter-md
        .col-6
          .km-label.text-secondary Status
          q-badge(
            :color='getStatusColor(run.status)',
            :label='run.status.toUpperCase()',
            class='q-mt-xs'
          )
        .col-6
          .km-label.text-secondary Created
          .km-description.text-black {{ formatDate(run.created_at) }}
        .col-6(v-if='run.client_id')
          .km-label.text-secondary Client ID
          .km-description.text-black {{ run.client_id }}
        .col-6
          .km-label.text-secondary Updated
          .km-description.text-black {{ formatDate(run.updated_at) }}

      q-separator.q-my-md

      .text-h6.q-mb-md Input
      q-card.bg-grey-2.q-pa-md
        pre.q-ma-none {{ JSON.stringify(run.input, null, 2) }}

      q-separator.q-my-md

      .text-h6.q-mb-md Configuration
      .row.q-col-gutter-md
        .col-6
          .km-label.text-secondary Max Iterations
          .km-description.text-black {{ run.config?.max_iterations ?? 'N/A' }}
        .col-6
          .km-label.text-secondary Max Results
          .km-description.text-black {{ run.config?.max_results ?? 'N/A' }}
        .col-12
          .km-label.text-secondary Reasoning Prompt
          .km-description.text-black {{ run.config?.reasoning_prompt ?? 'N/A' }}

      q-separator.q-my-md

      .text-h6.q-mb-md Memory & Progress
      .row.q-col-gutter-md
        .col-4
          .km-label.text-secondary Search Queries
          .km-description.text-black {{ run.memory?.search_queries?.length || 0 }}
        .col-4
          .km-label.text-secondary Analyzed URLs
          .km-description.text-black {{ run.memory?.analyzed_urls?.size || 0 }}
        .col-4
          .km-label.text-secondary Processed URLs
          .km-description.text-black {{ run.memory?.processed_urls?.size || 0 }}

      .q-mt-md(v-if='run.memory?.search_queries?.length > 0')
        .km-label.text-secondary.q-mb-xs Search Queries:
        q-chip(
          v-for='(query, index) in run.memory.search_queries',
          :key='index',
          color='primary',
          text-color='white',
          dense
        ) {{ query }}

      q-separator.q-my-md

      .text-h6.q-mb-md Steps ({{ run.steps?.length || 0 }})
      q-timeline(color='primary', v-if='run.steps && run.steps.length > 0')
        q-timeline-entry(
          v-for='(step, index) in run.steps',
          :key='index',
          :title='`Step ${step.step_number}: ${step.action}`',
          :subtitle='formatDate(step.timestamp)',
          :icon='getStepIcon(step.action)',
          :color='step.error ? "negative" : "primary"'
        )
          .q-mt-sm
            .km-label.text-secondary Input
            q-card.bg-grey-2.q-pa-sm.q-mb-sm
              pre.q-ma-none(style='font-size: 11px; max-height: 200px; overflow-y: auto') {{ JSON.stringify(step.input_data, null, 2) }}

            template(v-if='step.output_data')
              .km-label.text-secondary Output
              q-card.bg-grey-2.q-pa-sm.q-mb-sm
                pre.q-ma-none(style='font-size: 11px; max-height: 200px; overflow-y: auto') {{ JSON.stringify(step.output_data, null, 2) }}

            template(v-if='step.error')
              .km-label.text-negative Error
              q-card.bg-red-1.q-pa-sm
                .text-negative {{ step.error }}

      q-card.q-pa-md.bg-grey-2(v-else)
        .text-center.text-secondary No steps recorded yet

      q-separator.q-my-md(v-if='run.result')

      template(v-if='run.result')
        .text-h6.q-mb-md Final Result
        q-card.bg-green-1.q-pa-md
          pre.q-ma-none(style='max-height: 400px; overflow-y: auto') {{ JSON.stringify(run.result, null, 2) }}

      template(v-if='run.error')
        q-separator.q-my-md
        .text-h6.q-mb-md Error
        q-card.bg-red-1.q-pa-md
          .text-negative {{ run.error }}
</template>

<script setup lang="ts">
import { date } from 'quasar'

interface Props {
  modelValue: boolean
  run: any
}

defineProps<Props>()
defineEmits(['update:modelValue'])

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  return date.formatDate(new Date(dateStr), 'YYYY-MM-DD HH:mm:ss')
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    running: 'blue',
    completed: 'green',
    failed: 'red',
  }
  return colors[status] || 'grey'
}

const getStepIcon = (action: string) => {
  const icons: Record<string, string> = {
    reasoning: 'psychology',
    search: 'search',
    analyze_search_results: 'analytics',
    process_search_result: 'article',
  }
  return icons[action] || 'check_circle'
}
</script>

<style scoped lang="scss">
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>

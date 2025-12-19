<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-if='!loading && run', style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1400px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col.full-width
            .col-auto.q-mb-lg
              .row.items-center.q-gap-12.q-mb-xs
                .km-heading-4.text-black Run: {{ run.id.slice(0, 8) }}
                q-space
                q-chip.q-ma-none.km-heading.text-uppercase(
                  :label='run.status',
                  :color='getStatusColor(run.status)',
                  text-color='white'
                )
                q-chip.q-ma-none.km-heading.text-uppercase(
                  v-if='configName',
                  :label='configName',
                  color='light'
                )
              .text-secondary-text Created: {{ formatDate(run.created_at) }}
            .row.justify-between.q-gap-12.full-width
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Status
                .text-primary.text-weight-medium(style='font-size: 16px') {{ run.status }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Iterations
                .text-primary.text-weight-medium(style='font-size: 16px') {{ iterations.length }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Total Steps
                .text-primary.text-weight-medium(style='font-size: 16px') {{ totalSteps }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Search Queries
                .text-primary.text-weight-medium(style='font-size: 16px') {{ searchQueries.length }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') URLs Processed
                .text-primary.text-weight-medium(style='font-size: 16px') {{ processedUrls.length }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm(v-if='totalUsage')
                .text-weight-medium(style='font-size: 12px') Tokens
                .text-primary.text-weight-medium(style='font-size: 16px') {{ formatTokens(totalUsage) }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm(v-if='totalLatency !== null')
                .text-weight-medium(style='font-size: 12px') Latency
                .text-primary.text-weight-medium(style='font-size: 16px') {{ formatLatency(totalLatency) }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm(v-if='totalCost !== null')
                .text-weight-medium(style='font-size: 12px') Cost
                .text-primary.text-weight-medium(style='font-size: 16px') {{ formatCost(totalCost) }}

        .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 260px) !important')
          .row.q-gap-16.full-width
            //- Final Report Section
            .col-12(v-if='finalReport')
              .ba-border.bg-white.border-radius-12.q-pa-lg.full-width
                .row.items-center.q-mb-md
                  q-icon.q-mr-sm(name='summarize', color='green', size='28px')
                  .text-h5.text-weight-bold Final Report

                .report-content.q-pa-md.bg-grey-1.border-radius-8
                  //- Display JSON nicely or plain text
                  template(v-if='isJsonReport')
                    pre.q-ma-none(style='white-space: pre-wrap; word-wrap: break-word; font-family: monospace; font-size: 13px') {{ JSON.stringify(finalReport, null, 2) }}
                  template(v-else)
                    .text-body1(v-html='renderMarkdown(finalReportText)')

            //- Webhook Call Section
            .col-12(v-if='webhookCall')
              .ba-border.bg-white.border-radius-12.q-pa-lg.full-width
                .row.items-center.q-mb-md
                  q-icon.q-mr-sm(name='webhook', :color='webhookCall.success ? "positive" : "negative"', size='28px')
                  .text-h5.text-weight-bold Webhook Call
                  q-space
                  q-chip(
                    :color='webhookCall.success ? "positive" : "negative"',
                    text-color='white',
                    :icon='webhookCall.success ? "check_circle" : "error"'
                  ) {{ webhookCall.success ? 'Success' : 'Failed' }}

                .q-gutter-md
                  .row.items-center
                    .col-3.text-weight-medium.text-grey-8 Timestamp:
                    .col {{ formatDate(webhookCall.timestamp) }}
                  
                  .row.items-center
                    .col-3.text-weight-medium.text-grey-8 API Server:
                    .col {{ webhookCall.api_server }}
                  
                  .row.items-center
                    .col-3.text-weight-medium.text-grey-8 API Tool:
                    .col {{ webhookCall.api_tool }}
                  
                  .row.items-start(v-if='webhookCall.request_payload')
                    .col-3.text-weight-medium.text-grey-8 Request:
                    .col
                      q-expansion-item.bg-grey-1.border-radius-8(
                        dense,
                        label='View Payload',
                        icon='code'
                      )
                        q-card.q-mt-xs
                          q-card-section.bg-grey-2
                            pre.q-ma-none(style='white-space: pre-wrap; word-wrap: break-word; font-family: monospace; font-size: 12px') {{ JSON.stringify(webhookCall.request_payload, null, 2) }}
                  
                  .row.items-start(v-if='webhookCall.response_body')
                    .col-3.text-weight-medium.text-grey-8 Response:
                    .col
                      .row.items-center.q-mb-xs(v-if='webhookCall.response_status')
                        .text-caption.text-grey-7 Status: {{ webhookCall.response_status }}
                      q-expansion-item.bg-grey-1.border-radius-8(
                        dense,
                        label='View Response',
                        icon='description'
                      )
                        q-card.q-mt-xs
                          q-card-section.bg-grey-2
                            pre.q-ma-none(style='white-space: pre-wrap; word-wrap: break-word; font-family: monospace; font-size: 12px') {{ JSON.stringify(webhookCall.response_body, null, 2) }}
                  
                  .row.items-start(v-if='webhookCall.error_message')
                    .col-3.text-weight-medium.text-grey-8 Error:
                    .col
                      q-banner.bg-negative.text-white.rounded-borders.q-pa-sm
                        .text-caption {{ webhookCall.error_message }}

            //- Input Section
            .col-12
              q-expansion-item.ba-border.bg-white.border-radius-12(
                default-opened,
                icon='input',
                label='Input',
                header-class='text-h6 text-weight-bold q-pa-md'
              )
                q-card.q-ma-md
                  q-card-section.bg-grey-2
                    pre.q-ma-none {{ JSON.stringify(run.input, null, 2) }}

            //- Search Queries Section
            .col-12(v-if='searchQueries.length > 0')
              q-expansion-item.ba-border.bg-white.border-radius-12(
                icon='search',
                :label='`Search Queries (${searchQueries.length})`',
                header-class='text-h6 text-weight-bold q-pa-md'
              )
                .q-pa-md
                  .row.q-gutter-sm
                    q-chip(
                      v-for='(query, index) in searchQueries',
                      :key='index',
                      color='primary',
                      text-color='white',
                      icon='search'
                    ) {{ query }}

            //- Iterations & Steps Section
            .col-12(v-if='iterations.length > 0')
              .ba-border.bg-white.border-radius-12.q-pa-lg.full-width
                .row.items-center.q-mb-md
                  q-icon.q-mr-sm(name='timeline', color='primary', size='28px')
                  .text-h5.text-weight-bold Research Timeline

                q-timeline(color='primary')
                  q-timeline-entry(
                    v-for='(iteration, iterIndex) in iterations',
                    :key='iterIndex',
                    :title='`Iteration ${iterIndex}`',
                    :subtitle='`${iteration.steps.length} steps`',
                    icon='layers'
                  )
                    .q-mt-sm(v-for='(step, stepIndex) in iteration.steps', :key='stepIndex')
                      q-expansion-item.q-mb-sm(
                        :default-opened='shouldExpandStep(step)',
                        :header-class='getStepHeaderClass(step)'
                      )
                        template(v-slot:header)
                          .row.items-center.full-width.q-py-xs
                            q-icon.q-mr-md(
                              :name='getStepIcon(step.type)',
                              :color='step.error ? "negative" : getStepIconColor(step.type)',
                              size='24px'
                            )
                            .col
                              .text-weight-bold {{ formatStepType(step.type) }}
                              .text-caption.text-grey-7 {{ step.title }}
                            .text-caption.text-secondary.q-mr-md(v-if='step.timestamp') {{ formatTime(step.timestamp) }}

                        q-card.q-ma-sm(:class='step.error ? "bg-red-1" : "bg-grey-1"')
                          q-card-section
                            //- Step Title
                            .text-body1.text-weight-medium.q-mb-md(v-if='step.title')
                              | {{ step.title }}

                            //- Error Display
                            .q-mb-md(v-if='step.error')
                              q-banner.bg-negative.text-white.rounded-borders
                                template(v-slot:avatar)
                                  q-icon(name='error', color='white')
                                .text-weight-bold {{ step.error }}

                            //- Step Details by Type
                            .step-details
                              //- Reasoning Step
                              template(v-if='step.type === "reasoning" && step.details')
                                .q-mb-sm
                                  .text-weight-bold.text-grey-8 Decided Action:
                                  q-chip.q-mt-xs(
                                    :color='step.details.decided_action === "search" ? "blue" : "green"',
                                    text-color='white'
                                  ) {{ step.details.decided_action }}

                              //- Search Step
                              template(v-if='step.type === "search" && step.details')
                                .q-mb-sm
                                  .text-weight-bold.text-grey-8 Query:
                                  q-chip.q-mt-xs(color='primary', text-color='white', icon='search')
                                    | {{ step.details.query }}
                                .row.q-gutter-sm
                                  .col
                                    .text-caption.text-grey-7 Results Found
                                    .text-h6.text-primary {{ step.details.results_count || 0 }}
                                  .col
                                    .text-caption.text-grey-7 New Results
                                    .text-h6.text-green {{ step.details.new_results_count || 0 }}

                              //- Analyze Results Step
                              template(v-if='step.type === "analyze_results" && step.details')
                                .row.q-gutter-sm.q-mb-md
                                  .col
                                    .text-caption.text-grey-7 Analyzed
                                    .text-h6.text-blue {{ step.details.analyzed_count || 0 }}
                                  .col
                                    .text-caption.text-grey-7 Relevant
                                    .text-h6.text-green {{ step.details.relevant_count || 0 }}
                                .q-mb-sm(v-if='step.details.relevant_urls && step.details.relevant_urls.length > 0')
                                  .text-weight-bold.text-grey-8.q-mb-xs Relevant URLs:
                                  .q-gutter-xs
                                    q-chip(
                                      v-for='(url, idx) in step.details.relevant_urls',
                                      :key='idx',
                                      size='sm',
                                      color='green',
                                      text-color='white',
                                      clickable,
                                      icon='check_circle',
                                      @click='openUrl(url)'
                                    ) {{ truncateUrl(url) }}

                              //- Process Page Step
                              template(v-if='step.type === "process_page" && step.details')
                                .q-mb-sm(v-if='step.details.page_title')
                                  .text-weight-bold.text-grey-8 Page Title:
                                  .q-pa-sm.bg-white.border-radius-4.q-mt-xs
                                    | {{ step.details.page_title }}
                                .q-mb-sm(v-if='step.details.url')
                                  .text-weight-bold.text-grey-8 URL:
                                  q-chip.q-mt-xs(
                                    color='blue-grey',
                                    text-color='white',
                                    clickable,
                                    icon='link',
                                    @click='openUrl(step.details.url)'
                                  ) {{ truncateUrl(step.details.url) }}
                                .q-mb-sm(v-if='step.details.summary')
                                  .text-weight-bold.text-grey-8 Extracted Information:
                                  .q-pa-md.bg-white.border-radius-4.q-mt-xs.summary-text
                                    | {{ step.details.summary }}

                            //- Step Metrics (Latency, Cost, Usage)
                            .row.q-gutter-sm.q-mt-md(v-if='step.latency || step.cost || step.usage')
                              q-separator.q-mb-sm
                              .col-12
                                .text-caption.text-grey-7.q-mb-xs Performance Metrics
                              .col-auto(v-if='step.latency')
                                q-chip(size='sm', color='blue-grey-2', text-color='blue-grey-8', icon='schedule')
                                  | {{ formatLatency(step.latency) }}
                              .col-auto(v-if='step.cost')
                                q-chip(size='sm', color='green-2', text-color='green-8', icon='attach_money')
                                  | {{ formatCost(step.cost) }}
                              .col-auto(v-if='step.usage')
                                q-chip(size='sm', color='orange-2', text-color='orange-8', icon='analytics')
                                  | {{ formatTokens(step.usage) }}

            //- Processed URLs Section
            .col-12(v-if='processedUrls.length > 0')
              q-expansion-item.ba-border.bg-white.border-radius-12(
                icon='fact_check',
                :label='`Processed URLs (${processedUrls.length})`',
                header-class='text-h6 text-weight-bold q-pa-md'
              )
                .q-pa-md
                  q-list.bg-grey-1.border-radius-8(separator)
                    q-item(
                      v-for='(url, idx) in processedUrls',
                      :key='idx',
                      clickable,
                      @click='openUrl(url)'
                    )
                      q-item-section(avatar)
                        q-icon(name='article', color='primary')
                      q-item-section
                        q-item-label {{ url }}
                      q-item-section(side)
                        q-icon(name='open_in_new', color='grey')

            //- Error Section
            .col-12(v-if='run.error')
              .ba-border.bg-white.border-radius-12.q-pa-lg.full-width
                q-banner.bg-negative.text-white.rounded-borders
                  template(v-slot:avatar)
                    q-icon(name='error', color='white', size='32px')
                  .text-h6.q-mb-sm Error
                  .text-body1 {{ run.error }}
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import { date, openURL } from 'quasar'

const store = useStore()
const route = useRoute()

const loading = ref(true)
const run = ref<any>(null)

const runId = computed(() => route.params.id as string)

const configName = computed(() => {
  if (!run.value) return null

  if (run.value.config_system_name) {
    return run.value.config_system_name
  }

  if (run.value.config?.name) {
    return run.value.config.name
  }

  if (run.value.config?.system_name) {
    return run.value.config.system_name
  }

  const configs = store.getters.configs || []
  const matchedConfig = configs.find((c: any) => c.id === run.value?.config_id)
  if (matchedConfig) {
    return matchedConfig.name || matchedConfig.system_name || null
  }

  return run.value.config_id || null
})

// Extract iterations from details or top level
const iterations = computed(() => {
  if (!run.value) return []

  // Check details.iterations first (new structure)
  if (run.value.details?.iterations && Array.isArray(run.value.details.iterations)) {
    return run.value.details.iterations
  }

  // Fallback to top-level iterations
  if (run.value.iterations && Array.isArray(run.value.iterations)) {
    return run.value.iterations
  }

  return []
})

// Extract memory from details or top level
const memory = computed(() => {
  if (!run.value) return null

  if (run.value.details?.memory) {
    return run.value.details.memory
  }

  return run.value.memory || null
})

// Extract webhook_call from details or top level
const webhookCall = computed(() => {
  if (!run.value) return null

  if (run.value.details?.webhook_call) {
    return run.value.details.webhook_call
  }

  return run.value.webhook_call || null
})

// Extract search queries
const searchQueries = computed(() => {
  if (!memory.value) return []
  return memory.value.search_queries || []
})

// Extract processed URLs
const processedUrls = computed(() => {
  if (!memory.value) return []

  const urls = memory.value.processed_urls

  // Handle Set (converted to array in JSON)
  if (Array.isArray(urls)) {
    return urls
  }

  // Handle object (Set serialized as object with numeric keys)
  if (typeof urls === 'object' && urls !== null) {
    return Object.values(urls)
  }

  return []
})

// Extract final report
const finalReport = computed(() => {
  if (!run.value) return null

  // Check details.result first
  if (run.value.details?.result) {
    return run.value.details.result
  }

  // Fallback to top-level result
  return run.value.result || null
})

// Check if final report is JSON (not just a plain text wrapped in {content: ...})
const isJsonReport = computed(() => {
  if (!finalReport.value) return false
  if (typeof finalReport.value !== 'object') return false

  // If it only has a 'content' key, treat it as plain text
  const keys = Object.keys(finalReport.value)
  if (keys.length === 1 && keys[0] === 'content') {
    return false
  }

  return true
})

// Get the text content for plain text reports
const finalReportText = computed(() => {
  if (!finalReport.value) return ''

  // If it's wrapped in {content: ...}, extract the content
  if (finalReport.value.content && typeof finalReport.value.content === 'string') {
    return finalReport.value.content
  }

  // Otherwise, it's already text
  return typeof finalReport.value === 'string' ? finalReport.value : ''
})

const totalSteps = computed(() => {
  return iterations.value.reduce((acc: number, iter: any) => acc + (iter.steps?.length || 0), 0)
})

// Extract total latency from details or top level
const totalLatency = computed(() => {
  if (!run.value) return null
  
  // Check details first
  if (run.value.details?.total_latency !== undefined && run.value.details?.total_latency !== null) {
    return run.value.details.total_latency
  }
  
  // Fallback to top-level
  if (run.value.total_latency !== undefined && run.value.total_latency !== null) {
    return run.value.total_latency
  }
  
  // Calculate from created_at and updated_at if available
  if (run.value.status === 'completed' && run.value.created_at && run.value.updated_at) {
    const start = new Date(run.value.created_at).getTime()
    const end = new Date(run.value.updated_at).getTime()
    return end - start // in milliseconds
  }
  
  return null
})

// Extract total cost from details or top level
const totalCost = computed(() => {
  if (!run.value) return null
  
  // Check details first
  if (run.value.details?.total_cost !== undefined && run.value.details?.total_cost !== null) {
    return run.value.details.total_cost
  }
  
  // Fallback to top-level
  return run.value.total_cost || null
})

// Extract total usage from details or top level
const totalUsage = computed(() => {
  if (!run.value) return null
  
  // Check details first
  if (run.value.details?.total_usage) {
    return run.value.details.total_usage
  }
  
  // Fallback to top-level
  return run.value.total_usage || null
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  return date.formatDate(new Date(dateStr), 'YYYY-MM-DD HH:mm:ss')
}

const formatTokens = (usage: any) => {
  if (!usage) return 'N/A'
  const input = usage.prompt_tokens || 0
  const output = usage.completion_tokens || 0
  return `${input.toLocaleString()}/${output.toLocaleString()}`
}

const formatLatency = (latencyMs: number) => {
  if (latencyMs < 1000) {
    return `${Math.round(latencyMs)}ms`
  } else if (latencyMs < 60000) {
    return `${(latencyMs / 1000).toFixed(2)}s`
  } else {
    const minutes = Math.floor(latencyMs / 60000)
    const seconds = Math.floor((latencyMs % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }
}

const formatCost = (cost: number) => {
  if (cost < 0.01) {
    // Show more decimal places for small amounts
    return `$${cost.toFixed(4)}`
  } else {
    // Show 2 decimal places for larger amounts
    return `$${cost.toFixed(2)}`
  }
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  return date.formatDate(new Date(dateStr), 'HH:mm:ss')
}

const formatStepType = (type: string) => {
  const formatted = type.replace(/_/g, ' ')
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
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

// Simple markdown renderer (basic support)
const renderMarkdown = (text: string) => {
  if (!text) return ''

  let html = text

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')

  // Line breaks
  html = html.replace(/\n/g, '<br>')

  return html
}

const getStepIcon = (stepType: string) => {
  const icons: Record<string, string> = {
    reasoning: 'psychology',
    search: 'search',
    analyze_results: 'analytics',
    process_page: 'article',
  }
  return icons[stepType] || 'check_circle'
}

const getStepIconColor = (stepType: string) => {
  const colors: Record<string, string> = {
    reasoning: 'purple',
    search: 'blue',
    analyze_results: 'orange',
    process_page: 'green',
  }
  return colors[stepType] || 'primary'
}

const getStepHeaderClass = (step: any) => {
  if (step.error) {
    return 'bg-red-2 text-negative'
  }
  return 'bg-grey-2'
}

const shouldExpandStep = (step: any) => {
  // Auto-expand reasoning steps and steps with errors
  return step.type === 'reasoning' || step.error
}

const truncateUrl = (url: string, maxLength = 50) => {
  if (!url) return ''
  if (url.length <= maxLength) return url

  try {
    const urlObj = new URL(url)
    const domain = urlObj.hostname.replace('www.', '')
    const path = urlObj.pathname + urlObj.search

    if (path.length > maxLength - domain.length - 3) {
      return `${domain}${path.substring(0, maxLength - domain.length - 6)}...`
    }

    return `${domain}${path}`
  } catch {
    return url.substring(0, maxLength - 3) + '...'
  }
}

const openUrl = (url: string) => {
  if (url) {
    openURL(url)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    if (!store.getters.configs?.length) {
      await store.dispatch('fetchConfigs')
    }

    const fetchedRun = await store.dispatch('fetchRun', runId.value)
    run.value = fetchedRun || store.getters.selectedRun
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.report-content {
  border-left: 4px solid #1976d2;
  transition: all 0.3s ease;

  &.bg-red-1 {
    border-left-color: #c10015;
  }

  &.bg-orange-1 {
    border-left-color: #f2c037;
  }

  &.bg-green-1 {
    border-left-color: #21ba45;
  }
}

.report-summary {
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.source-chip {
  max-width: 400px;

  :deep(.q-chip__content) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.step-details {
  font-size: 14px;
}

.summary-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

:deep(.q-expansion-item__container) {
  .q-expansion-item__toggle-icon {
    transition: transform 0.3s ease;
  }
}

:deep(.q-timeline__entry) {
  padding-bottom: 24px;
}

:deep(.q-card) {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
}

.border-radius-4 {
  border-radius: 4px;
}

.border-radius-8 {
  border-radius: 8px;
}

.border-radius-12 {
  border-radius: 12px;
}
</style>

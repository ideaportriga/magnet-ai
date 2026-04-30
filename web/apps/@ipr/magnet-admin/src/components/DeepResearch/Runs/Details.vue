<template>
  <div v-if="loading" class="cluster overflow-hidden full-height deep-research-run__viewport" data-wrap="no">
    <km-inner-loading :showing="loading" />
  </div>
  <div v-if="!loading &amp;&amp; run" class="cluster overflow-hidden full-height deep-research-run__viewport" data-wrap="no">
    <div class="flex flex-1 full-height fit deep-research-run__shell">
      <div class="flex-1 deep-research-run__column">
        <div class="full-height pb-md relative-position px-md">
          <div class="cluster full-width mt-lg mb-sm bg-white border-radius-8 py-md px-lg" data-gap="md" data-wrap="no">
            <div class="flex-1 full-width">
              <div class="flex-none mb-lg">
                <div class="cluster mb-xs" data-gap="md">
                  <div class="km-heading-4 text-black">Run: {{ run.id.slice(0, 8) }}</div>
                  <div class="km-space" />
                  <km-chip class="m-0 km-heading text-uppercase" :label="run.status" :tone="getStatusTone(run.status)" />
                  <km-chip v-if="configName" class="m-0 km-heading text-uppercase" :label="configName" tone="neutral" />
                </div>
                <div class="text-secondary-text">Created: {{ formatDate(run.created_at) }}</div>
              </div>
              <div class="deep-research-run__stats-grid">
                <div class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Status</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ run.status }}</div>
                </div>
                <div class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Iterations</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ iterations.length }}</div>
                </div>
                <div class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Total Steps</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ totalSteps }}</div>
                </div>
                <div class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Search Queries</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ searchQueries.length }}</div>
                </div>
                <div class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">URLs Processed</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ processedUrls.length }}</div>
                </div>
                <div v-if="totalUsage" class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Tokens</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ formatTokens(totalUsage) }}</div>
                </div>
                <div v-if="totalLatency !== null" class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Latency</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ formatLatency(totalLatency) }}</div>
                </div>
                <div v-if="totalCost !== null" class="bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium deep-research-run__stat-label">Cost</div>
                  <div class="text-primary text-weight-medium deep-research-run__stat-value">{{ formatCost(totalCost) }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="stack full-height full-width overflow-auto mb-md mt-lg deep-research-run__scroll" data-gap="lg">
            <div class="cluster full-width" data-gap="lg">
              <div v-if="finalReport" class="full-width">
                <div class="ba-border bg-white border-radius-12 p-lg full-width">
                  <div class="cluster mb-md">
                    <km-glyph class="mr-sm" name="summarize" tone="success" size="28px" />
                    <div class="text-h5 text-weight-bold">Final Report</div>
                  </div>
                  <div class="report-content p-md bg-grey-1 border-radius-8">
                    <template v-if="isJsonReport">
                      <pre class="m-0 deep-research-run__pre">{{ JSON.stringify(finalReport, null, 2) }}</pre>
                    </template>
                    <template v-else>
                      <div class="text-body1" v-html="renderMarkdown(finalReportText)" />
                    </template>
                  </div>
                </div>
              </div>
              <div v-if="webhookCall" class="full-width">
                <div class="ba-border bg-white border-radius-12 p-lg full-width">
                  <div class="cluster mb-md">
                    <km-glyph class="mr-sm" name="webhook" :tone="webhookCall.success ? &quot;success&quot; : &quot;danger&quot;" size="28px" />
                    <div class="text-h5 text-weight-bold">Webhook Call</div>
                    <div class="km-space" />
                    <km-chip :tone="webhookCall.success ? &quot;success&quot; : &quot;danger&quot;" :icon="webhookCall.success ? &quot;check&quot; : &quot;error&quot;">{{ webhookCall.success ? 'Success' : 'Failed' }}</km-chip>
                  </div>
                  <div class="gap-md">
                    <div class="cluster">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">Timestamp:</div>
                      <div class="deep-research-run__meta-value flex-1">{{ formatDate(webhookCall.timestamp) }}</div>
                    </div>
                    <div class="cluster">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">API Server:</div>
                      <div class="deep-research-run__meta-value flex-1">{{ webhookCall.api_server }}</div>
                    </div>
                    <div class="cluster">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">API Tool:</div>
                      <div class="deep-research-run__meta-value flex-1">{{ webhookCall.api_tool }}</div>
                    </div>
                    <div v-if="webhookCall.request_payload" class="cluster" data-align="start">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">Request:</div>
                      <div class="deep-research-run__meta-value flex-1">
                        <km-expansion-item class="bg-grey-1 border-radius-8" dense :label="m.common_viewPayload()" icon="code">
                          <km-card class="mt-xs">
                            <div class="km-card-section bg-grey-2">
                              <pre class="m-0 deep-research-run__pre deep-research-run__pre--sm">{{ JSON.stringify(webhookCall.request_payload, null, 2) }}</pre>
                            </div>
                          </km-card>
                        </km-expansion-item>
                      </div>
                    </div>
                    <div v-if="webhookCall.response_body" class="cluster" data-align="start">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">Response:</div>
                      <div class="deep-research-run__meta-value flex-1">
                        <div v-if="webhookCall.response_status" class="cluster mb-xs">
                          <div class="text-caption text-grey-7">Status: {{ webhookCall.response_status }}</div>
                        </div>
                        <km-expansion-item class="bg-grey-1 border-radius-8" dense :label="m.common_viewResponse()" icon="file-text">
                          <km-card class="mt-xs">
                            <div class="km-card-section bg-grey-2">
                              <pre class="m-0 deep-research-run__pre deep-research-run__pre--sm">{{ JSON.stringify(webhookCall.response_body, null, 2) }}</pre>
                            </div>
                          </km-card>
                        </km-expansion-item>
                      </div>
                    </div>
                    <div v-if="webhookCall.error_message" class="cluster" data-align="start">
                      <div class="deep-research-run__meta-label flex-none text-weight-medium text-grey-8">Error:</div>
                      <div class="deep-research-run__meta-value flex-1">
                        <km-banner>
                          <div class="text-caption">{{ webhookCall.error_message }}</div>
                        </km-banner>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="full-width">
                <km-expansion-item class="ba-border bg-white border-radius-12" default-opened icon="input" :label="m.common_input()" header-class="text-h6 text-weight-bold p-md">
                  <km-card class="m-md">
                    <div class="km-card-section bg-grey-2">
                      <pre class="m-0">{{ JSON.stringify(run.input, null, 2) }}</pre>
                    </div>
                  </km-card>
                </km-expansion-item>
              </div>
              <div v-if="searchQueries.length &gt; 0" class="full-width">
                <km-expansion-item class="ba-border bg-white border-radius-12" icon="search" :label="`Search Queries (${searchQueries.length})`" header-class="text-h6 text-weight-bold p-md">
                  <div class="p-md">
                    <div class="cluster" data-gap="sm">
                      <km-chip v-for="(query, index) in searchQueries" :key="index" tone="brand" icon="search">{{ query }}</km-chip>
                    </div>
                  </div>
                </km-expansion-item>
              </div>
              <div v-if="iterations.length &gt; 0" class="full-width">
                <div class="ba-border bg-white border-radius-12 p-lg full-width">
                  <div class="cluster mb-md">
                    <km-glyph class="mr-sm" name="timeline" tone="brand" size="28px" />
                    <div class="text-h5 text-weight-bold">Research Timeline</div>
                  </div>
                  <km-timeline>
                    <km-timeline-entry v-for="(iteration, iterIndex) in iterations" :key="iterIndex" :title="`Iteration ${iterIndex}`" :subtitle="`${iteration.steps.length} steps`" icon="layers">
                      <div v-for="(step, stepIndex) in iteration.steps" :key="stepIndex" class="mt-sm">
                        <km-expansion-item class="mb-sm" :default-opened="shouldExpandStep(step)" :header-class="getStepHeaderClass(step)">
                          <template #header>
                            <div class="cluster full-width py-xs">
                              <km-glyph class="mr-md" :name="getStepIcon(step.type)" :tone="step.error ? &quot;danger&quot; : getStepIconTone(step.type)" size="24px" />
                              <div class="flex-1">
                                <div class="text-weight-bold">{{ formatStepType(step.type) }}</div>
                                <div class="text-caption text-grey-7">{{ step.title }}</div>
                              </div>
                              <div v-if="step.timestamp" class="text-caption text-secondary mr-md">{{ formatTime(step.timestamp) }}</div>
                            </div>
                          </template>
                          <km-card class="m-sm" :class="step.error ? &quot;bg-red-1&quot; : &quot;bg-grey-1&quot;">
                            <div class="km-card-section">
                              <div v-if="step.title" class="text-body1 text-weight-medium mb-md">{{ step.title }}</div>
                              <div v-if="step.error" class="mb-md">
                                <km-banner>
                                  <template #avatar>
                                    <km-glyph name="error" tone="inverse" />
                                  </template>
                                  <div class="text-weight-bold">{{ step.error }}</div>
                                </km-banner>
                              </div>
                              <div class="step-details">
                                <template v-if="step.type === &quot;reasoning&quot; &amp;&amp; step.details">
                                  <div class="mb-sm">
                                    <div class="text-weight-bold text-grey-8">Decided Action:</div>
                                    <km-chip class="mt-xs" :tone="step.details.decided_action === &quot;search&quot; ? &quot;info&quot; : &quot;success&quot;">{{ step.details.decided_action }}</km-chip>
                                  </div>
                                </template>
                                <template v-if="step.type === &quot;search&quot; &amp;&amp; step.details">
                                  <div class="mb-sm">
                                    <div class="text-weight-bold text-grey-8">Query:</div>
                                    <km-chip class="mt-xs" tone="brand" icon="search">{{ step.details.query }}</km-chip>
                                  </div>
                                  <div class="cluster" data-gap="sm">
                                    <div class="flex-1">
                                      <div class="text-caption text-grey-7">Results Found</div>
                                      <div class="text-h6 text-primary">{{ step.details.results_count || 0 }}</div>
                                    </div>
                                    <div class="flex-1">
                                      <div class="text-caption text-grey-7">New Results</div>
                                      <div class="text-h6 text-green">{{ step.details.new_results_count || 0 }}</div>
                                    </div>
                                  </div>
                                </template>
                                <template v-if="step.type === &quot;analyze_results&quot; &amp;&amp; step.details">
                                  <div class="cluster mb-md" data-gap="sm">
                                    <div class="flex-1">
                                      <div class="text-caption text-grey-7">Analyzed</div>
                                      <div class="text-h6 text-blue">{{ step.details.analyzed_count || 0 }}</div>
                                    </div>
                                    <div class="flex-1">
                                      <div class="text-caption text-grey-7">Relevant</div>
                                      <div class="text-h6 text-green">{{ step.details.relevant_count || 0 }}</div>
                                    </div>
                                  </div>
                                  <div v-if="step.details.relevant_urls &amp;&amp; step.details.relevant_urls.length &gt; 0" class="mb-sm">
                                    <div class="text-weight-bold text-grey-8 mb-xs">Relevant URLs:</div>
                                    <div class="gap-xs">
                                      <km-chip v-for="(url, idx) in step.details.relevant_urls" :key="idx" size="sm" tone="success" clickable icon="check" @click="openUrl(url)">{{ truncateUrl(url) }}</km-chip>
                                    </div>
                                  </div>
                                </template>
                                <template v-if="step.type === &quot;process_page&quot; &amp;&amp; step.details">
                                  <div v-if="step.details.page_title" class="mb-sm">
                                    <div class="text-weight-bold text-grey-8">Page Title:</div>
                                    <div class="p-sm bg-white border-radius-4 mt-xs">{{ step.details.page_title }}</div>
                                  </div>
                                  <div v-if="step.details.url" class="mb-sm">
                                    <div class="text-weight-bold text-grey-8">URL:</div>
                                    <km-chip class="mt-xs" tone="neutral-strong" clickable icon="link" @click="openUrl(step.details.url)">{{ truncateUrl(step.details.url) }}</km-chip>
                                  </div>
                                  <div v-if="step.details.summary" class="mb-sm">
                                    <div class="text-weight-bold text-grey-8">Extracted Information:</div>
                                    <div class="p-md bg-white border-radius-4 mt-xs summary-text">{{ step.details.summary }}</div>
                                  </div>
                                </template>
                              </div>
                              <div v-if="step.latency || step.cost || step.usage" class="cluster mt-md" data-gap="sm">
                                <km-separator class="mb-sm" />
                                <div class="full-width">
                                  <div class="text-caption text-grey-7 mb-xs">Performance Metrics</div>
                                </div>
                                <div v-if="step.latency" class="flex-none">
                                  <km-chip size="sm" tone="neutral" icon="clock">{{ formatLatency(step.latency) }}</km-chip>
                                </div>
                                <div v-if="step.cost" class="flex-none">
                                  <km-chip size="sm" tone="success" icon="attach_money">{{ formatCost(step.cost) }}</km-chip>
                                </div>
                                <div v-if="step.usage" class="flex-none">
                                  <km-chip size="sm" tone="warning" icon="analytics">{{ formatTokens(step.usage) }}</km-chip>
                                </div>
                              </div>
                            </div>
                          </km-card>
                        </km-expansion-item>
                      </div>
                    </km-timeline-entry>
                  </km-timeline>
                </div>
              </div>
              <div v-if="processedUrls.length &gt; 0" class="full-width">
                <km-expansion-item class="ba-border bg-white border-radius-12" icon="clipboard-check" :label="`Processed URLs (${processedUrls.length})`" header-class="text-h6 text-weight-bold p-md">
                  <div class="p-md">
                    <ul class="km-list bg-grey-1 border-radius-8" separator>
                      <li v-for="(url, idx) in processedUrls" :key="idx" class="km-item" clickable @click="openUrl(url)">
                        <div class="km-item-section" avatar>
                          <km-glyph name="file-text" tone="brand" />
                        </div>
                        <div class="km-item-section">
                          <span class="km-item-label">{{ url }}</span>
                        </div>
                        <div class="km-item-section" side>
                          <km-glyph name="external-link" tone="muted" />
                        </div>
                      </li>
                    </ul>
                  </div>
                </km-expansion-item>
              </div>
              <div v-if="run.error" class="full-width">
                <div class="ba-border bg-white border-radius-12 p-lg full-width">
                  <km-banner>
                    <template #avatar>
                      <km-glyph name="error" tone="inverse" size="32px" />
                    </template>
                    <div class="text-h6 mb-sm">Error</div>
                    <div class="text-body1">{{ run.error }}</div>
                  </km-banner>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { DateTime } from 'luxon'
import { useDeepResearchStore } from '@/stores/deepResearchStore'

const drStore = useDeepResearchStore()
const route = useRoute()

const loading = ref(true)
const run = ref<any>(null)

const runId = ref(route.params.id)

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

  const configs = drStore.configs || []
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
  return DateTime.fromJSDate(new Date(dateStr)).toFormat('yyyy-MM-dd HH:mm:ss')
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
  return DateTime.fromJSDate(new Date(dateStr)).toFormat('HH:mm:ss')
}

const formatStepType = (type: string) => {
  const formatted = type.replace(/_/g, ' ')
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

const getStatusTone = (status: string) => {
  const tones: Record<string, string> = {
    pending: 'warning',
    running: 'info',
    completed: 'success',
    failed: 'danger',
  }
  return tones[status] || 'neutral'
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

const getStepIconTone = (stepType: string) => {
  const tones: Record<string, string> = {
    reasoning: 'context',
    search: 'info',
    analyze_results: 'warning',
    process_page: 'success',
  }
  return tones[stepType] || 'brand'
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
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    if (!drStore.configs?.length) {
      await drStore.fetchConfigs()
    }

    const fetchedRun = await drStore.fetchRun(runId.value)
    run.value = fetchedRun || drStore.selectedRun
  } finally {
    loading.value = false
  }
})

onActivated(async () => {
  runId.value = route.params.id
  if (runId.value && runId.value !== run.value?.id) {
    loading.value = true
    try {
      const fetchedRun = await drStore.fetchRun(runId.value)
      run.value = fetchedRun || drStore.selectedRun
    } finally {
      loading.value = false
    }
  }
})
</script>

<style scoped lang="scss">
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-caption);
}

.report-content {
  border-left: 4px solid var(--ds-color-info-solid);
  transition: border-left-color var(--ds-duration-slow) var(--ds-ease-out);

  &.bg-red-1 {
    border-left-color: var(--ds-color-danger-solid);
  }

  &.bg-orange-1 {
    border-left-color: var(--ds-color-warning-solid);
  }

  &.bg-green-1 {
    border-left-color: var(--ds-color-success-solid);
  }
}

.report-summary {
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.deep-research-run__viewport {
  min-inline-size: 1200px;
}

.deep-research-run__column {
  max-inline-size: 1400px;
  min-inline-size: 600px;
}

.deep-research-run__scroll {
  max-block-size: calc(100vh - 260px);
}

.deep-research-run__stat-label {
  font-size: var(--ds-font-size-xs);
}

.deep-research-run__stat-value {
  font-size: var(--ds-font-size-body-lg);
}

.deep-research-run__pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-label);
}

.deep-research-run__pre--sm {
  font-size: var(--ds-font-size-xs);
}

.deep-research-run__shell {
  justify-content: center;
  flex-wrap: nowrap;
}

.deep-research-run__stats-grid {
  display: grid;
  gap: var(--ds-space-md);
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.deep-research-run__meta-label {
  flex: 0 0 25%;
  max-inline-size: 25%;
}

.deep-research-run__meta-value {
  min-inline-size: 0;
}

.step-details {
  font-size: var(--ds-font-size-body);
}

.summary-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
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

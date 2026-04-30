<template>
  <div v-if="loading" class="cluster overflow-hidden full-height traces-detail__viewport" data-wrap="no">
    <km-inner-loading :showing="loading" />
  </div>
  <div class="cluster overflow-hidden full-height traces-detail__viewport" data-wrap="no">
    <div class="flex flex-1 full-height fit traces-detail__shell">
      <div class="flex-1 traces-detail__column">
        <div class="full-height pb-md relative-position px-md">
          <div class="cluster full-width mt-lg mb-sm bg-white border-radius-8 py-md px-lg" data-gap="md" data-wrap="no">
            <div class="flex-1 full-width">
              <div class="flex-none mb-lg">
                <div class="cluster mb-xs" data-gap="md">
                  <div class="km-heading-4 text-black">{{ name }}</div>
                  <div class="km-space" />
                  <km-chip v-if="channel" class="m-0 km-heading text-uppercase" :label="channel" tone="brand" />
                  <km-chip v-if="type" class="m-0 km-heading text-uppercase" :label="type" tone="neutral" />
                  <km-chip v-if="status === &quot;error&quot;" class="m-0 km-heading" :label="m.common_errorLabel()" tone="danger" />
                </div>
                <div class="text-secondary-text">{{ startTime }}</div>
              </div>
              <div class="cluster full-width" data-justify="between" data-gap="md">
                <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium traces-detail__stat-label">Latency</div>
                  <div class="text-primary text-weight-medium traces-detail__stat-value">{{ formattedLatency }}</div>
                </div>
                <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium traces-detail__stat-label">Chat Completion Cost</div>
                  <div class="text-primary text-weight-medium traces-detail__stat-value">{{ chatCompletionCost }}</div>
                </div>
                <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium traces-detail__stat-label">Embedding Cost</div>
                  <div class="text-primary text-weight-medium traces-detail__stat-value">{{ embeddingCost }}</div>
                </div>
                <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium traces-detail__stat-label">Rerank Cost</div>
                  <div class="text-primary text-weight-medium traces-detail__stat-value">{{ rerankCost }}</div>
                </div>
                <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
                  <div class="text-weight-medium traces-detail__stat-label">Total Cost</div>
                  <div class="text-primary text-weight-medium traces-detail__stat-value">{{ totalCost }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="stack full-height full-width overflow-auto mb-md mt-lg traces-detail__scroll" data-gap="lg">
            <div class="cluster full-height full-width" data-gap="lg">
              <div class="flex-1 full-height full-width">
                <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
                  <div class="ba-border bg-white border-radius-12 p-lg pr-xl full-width relative-position">
                    <template v-if="spans?.length">
                      <div class="full-width">
                        <div v-for="(span, index) in spansTree" :key="index" class="cluster border-radius-8 full-width" :class="span.ui.rowContainer.classes" :style="[span.ui.rowContainer.styles, selectedSpan?.id === span.id ? { backgroundColor: &quot;var(--ds-color-table-active)&quot; } : {}]" @click="openDrawer(span)">
                          <template v-if="span.type === &quot;idle&quot;">
                            <div class="cluster text-secondary-text full-width" data-justify="center" :style="span.ui.row.styles">Idle for {{ span.latency }}</div>
                          </template>
                          <template v-else>
                            <div class="flex-1">
                              <div class="cluster py-xs mt-xs" data-gap="2xs" data-wrap="no">
                                <div v-if="span.type" class="cluster span-default-background text-uppercase border-radius-6 py-xs px-sm" data-gap="xs" :style="span.ui.chip.styles">
                                  <km-glyph v-if="span.status === &quot;error&quot;" name="fa-solid fa-circle-exclamation" tone="danger" size="16px" />
                                  <div>{{ span.type }}</div>
                                </div>
                                <div class="text-secondary-text">{{ span.name }}</div>
                              </div>
                              <div class="cluster ml-xs mb-xs traces-detail__span-meta" data-gap="md">
                                <div>{{ span.latency }}</div>
                                <div>{{ span.computed.total_cost }}</div>
                              </div>
                            </div>
                            <div v-if="span.repeat_count" class="span-collapse-count text-secondary-text" title="Number of times this span was repeated sequentially">x{{ span.repeat_count }}</div>
                            <div class="flex px-sm traces-detail__timeline-col">
                              <div class="cluster span-default-background border-radius-4 p-xs my-md" :style="span.ui.timeline.styles">{{ span.latency }}</div>
                            </div>
                          </template>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div class="center-flex-x mt-sm">
                        <km-loader size="50px" />
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-none">
      <observability-traces-drawer v-if="drawerOpened" :open="drawerOpened" :trace="draft" :span="selectedSpan" />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { formatDuration, formatTraceType } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'

export default {
  setup() {
    const { draft, isLoading: loading } = useEntityDetail('observability_traces')

    return {
      m,
      draft,
      loading,
      drawerOpened: ref(true),
      selectedSpan: ref(null),
    }
  },
  computed: {
    name() {
      return this.draft?.name || ''
    },
    type() {
      return formatTraceType(this.draft?.type)
    },
    channel() {
      return this.draft?.channel || ''
    },
    startTime() {
      return formatDateTime(this.draft?.start_time)
    },
    endTime() {
      return formatDateTime(this.draft?.end_time)
    },
    formattedLatency() {
      return formatDuration(this.draft?.latency)
    },
    embeddingCost() {
      const cost = this.draft?.cost_details?.embed
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    chatCompletionCost() {
      const cost = this.draft?.cost_details?.chat
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    rerankCost() {
      const cost = this.draft?.cost_details?.rerank
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    totalCost() {
      const cost = this.draft?.cost_details?.total
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    status() {
      return this.draft?.status || ''
    },
    spans() {
      return this.draft?.spans || []
    },
    spansTree() {
      const spanMap = new Map()
      const rootSpans = []
      let idleTotalLatency = 0

      // First pass - create map of all spans
      this.spans?.forEach((span) => {
        spanMap.set(span.id, { ...span, children: [] })
        if (span.type === 'idle') {
          idleTotalLatency += span.latency
        }
      })

      // Second pass - build tree structure
      this.spans?.forEach((span) => {
        const spanNode = spanMap.get(span.id)
        if (span.parent_id && spanMap.has(span.parent_id)) {
          const parent = spanMap.get(span.parent_id)
          parent.children.push(spanNode)
        } else {
          rootSpans.push(spanNode)
        }
      })

      // Third pass - calculate levels
      const calculateLevels = (span, level = 0) => {
        span.level = level
        if (span.children.length === 0) return
        span.children.forEach((child) => calculateLevels(child, level + 1))
        span.children.sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      }
      for (const span of rootSpans) {
        calculateLevels(span)
      }

      const formatCost = (cost) => {
        if (typeof cost !== 'number') return ''
        return `$${cost.toFixed(6)}`
      }

      const calcSpanRowParams = (spanLevel) => {
        const rowLeftPadding = 20
        const leftMargin = 6
        const rightMargin = 15
        const lineWidth = 1
        const lines = []
        let offset = rowLeftPadding
        for (let i = 0; i < spanLevel; i++) {
          const beforeLine = `transparent ${offset}px, transparent ${offset + leftMargin}px`
          offset += leftMargin
          const line = `#e5e7eb ${offset}px, #e5e7eb ${offset + lineWidth}px`
          offset += lineWidth
          const afterLine = `transparent ${offset}px, transparent ${offset + rightMargin}px`
          offset += rightMargin
          lines.push(`${beforeLine},${line},${afterLine}`)
        }
        return [rowLeftPadding, leftMargin, rightMargin, lineWidth, lines]
      }
      const calcSpanTimelineParams = (spanStartTime, spanLatency, idleLatency) => {
        const trace = this.draft
        const traceLatency = (trace?.latency ?? 1000) - idleTotalLatency
        const traceStartTime = new Date(trace?.start_time).getTime()
        const spanStart = new Date(spanStartTime).getTime()
        const width = (spanLatency / traceLatency) * 100
        const start = ((spanStart - traceStartTime - (idleLatency ?? 0)) / traceLatency) * 100
        return [start, width]
      }

      const calcSpanColor = (spanType) => {
        switch (spanType) {
          case 'chat':
            return 'var(--ds-color-success-soft)'
          case 'embed':
            return 'var(--ds-color-warning-soft)'
          case 'rerank':
            return 'var(--ds-color-warning-100)'
          case 'search':
            return 'var(--ds-color-info-soft)'
          case 'tool':
            return 'var(--ds-color-primary-soft)'
          default:
            return 'var(--ds-color-primary-soft)'
        }
      }

      // Flatten tree to array while preserving levels
      let idleAccumulatedLatency = 0
      const flattenAndTransform = (spans) => {
        return spans.reduce((acc, span) => {
          span.ui = {}

          // Span row container parameters
          const [rowLeftPadding, leftMargin, rightMargin, lineWidth, lines] = calcSpanRowParams(span.level)
          span.ui.rowContainer = {
            classes: [span.type !== 'idle' && 'span-hoverable cursor-pointer'],
            styles: [
              span.type === 'idle'
                ? {
                    height: '38px',
                    margin: '10px 0',
                  }
                : {
                    paddingLeft: rowLeftPadding + span.level * (rightMargin + leftMargin + lineWidth) + 'px',
                    backgroundImage: `linear-gradient(to right, ${lines.join(', ')})`,
                  },
            ],
          }

          // Span row parameters
          span.ui.row = {
            styles: [
              span.type === 'idle' && {
                left: '0px',
                position: 'absolute',
                fontSize: '12px',
                padding: '10px 0',
                backgroundImage: 'repeating-linear-gradient(45deg, var(--ds-color-static-white) 0, var(--ds-color-static-white) 2.5px, var(--ds-color-light) 0, var(--ds-color-light) 50%)',
                backgroundSize: '8px 8px',
              },
            ],
          }

          // Span chip parameters
          span.ui.chip = {
            styles: [
              {
                fontSize: '12px',
                backgroundColor: calcSpanColor(span.type),
              },
            ],
          }

          // Span timeline parameters
          if (span.type === 'idle') {
            idleAccumulatedLatency += span.latency
          } else {
            const [spanTimelineStart, spanTimelineWidth] = calcSpanTimelineParams(span.start_time, span.latency, idleAccumulatedLatency)
            span.ui.timeline = {
              styles: [
                {
                  width: `${spanTimelineWidth}%`,
                  marginLeft: `${spanTimelineStart}%`,
                  backgroundColor: calcSpanColor(span.type),
                  fontSize: '12px',
                  verticalAlign: 'middle',
                  whiteSpace: 'nowrap',
                },
              ],
            }
          }

          span.latency = formatDuration(span.latency)
          span.computed = { total_cost: formatCost(span.cost_details?.total) }
          return [...acc, span, ...flattenAndTransform(span.children)]
        }, [])
      }

      return flattenAndTransform(rootSpans)
    },

  },

  watch: {
    draft: {
      handler(newVal) {
        if (newVal?.spans?.length && !this.selectedSpan) {
          this.selectedSpan = newVal.spans[0]
        }
      },
      immediate: true,
    },
  },
  methods: {
    openDrawer(span) {
      if (span.type === 'idle') return

      this.drawerOpened = true
      this.selectedSpan = span
    },
    closeDrawer() {
      this.drawerOpened = false
      this.selectedSpan = null
    },
  },
}
</script>

<style>
.traces-detail__viewport {
  min-inline-size: 1200px;
}
.traces-detail__shell {
  justify-content: center;
}
.traces-detail__column {
  max-inline-size: 1200px;
  min-inline-size: 600px;
}
.traces-detail__scroll {
  max-block-size: calc(100vb - 260px);
}
.traces-detail__stat-label {
  font-size: var(--ds-font-size-xs);
}
.traces-detail__stat-value {
  font-size: var(--ds-font-size-body-lg);
}
.traces-detail__span-meta {
  font-size: var(--ds-font-size-xs);
}
.traces-detail__timeline-col {
  inline-size: 400px;
  border-inline-start: 1px solid var(--ds-color-border);
}

.span-default-background {
  background-color: var(--ds-color-info-soft);
}
.span-hoverable:hover {
  background-color: var(--ds-color-table-hover);
}
.span-collapse-count {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 9px;
  background-color: var(--ds-color-border);
  border-radius: 50px;
  block-size: 30px;
  inline-size: 30px;
  margin-inline-end: 10px;
  align-self: center;
}
</style>

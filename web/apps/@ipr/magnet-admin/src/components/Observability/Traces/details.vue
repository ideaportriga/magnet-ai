<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col.full-width
            .col-auto.q-mb-lg
              .row.items-center.q-gap-12.q-mb-xs
                .km-heading-4.text-black {{ name }}
                q-space 
                q-chip.q-ma-none.km-heading.text-uppercase(v-if='channel', :label='channel', color='chip-accent-bg', textColor='primary')
                q-chip.q-ma-none.km-heading.text-uppercase(v-if='type', :label='type', color='light')
                q-chip.q-ma-none.km-heading.text-white(v-if='status === "error"', label='ERROR', color='red')
              .text-secondary-text {{ startTime }}
            .row.justify-between.q-gap-12.full-width
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Latency
                .text-primary.text-weight-medium(style='font-size: 16px') {{ formattedLatency }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Chat Completion Cost
                .text-primary.text-weight-medium(style='font-size: 16px') {{ chatCompletionCost }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Embedding Cost
                .text-primary.text-weight-medium(style='font-size: 16px') {{ embeddingCost }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Rerank Cost
                .text-primary.text-weight-medium(style='font-size: 16px') {{ rerankCost }}
              .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
                .text-weight-medium(style='font-size: 12px') Total Cost
                .text-primary.text-weight-medium(style='font-size: 16px') {{ totalCost }}

        .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 260px) !important')
          .row.q-gap-16.full-height.full-width
            .col.full-height.full-width
              .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                .ba-border.bg-white.border-radius-12.q-pa-lg.q-pr-xl.full-width.relative-position
                  template(v-if='spans?.length')
                    .row.full-width
                      .row.border-radius-8.full-width(
                        v-for='(span, index) in spansTree',
                        :key='index',
                        :class='span.ui.rowContainer.classes',
                        :style='[span.ui.rowContainer.styles, selectedSpan?.id === span.id ? { backgroundColor: "var(--q-table-active)" } : {}]',
                        @click='openDrawer(span)'
                      )
                        template(v-if='span.type === "idle"')
                          .row.items-center.justify-center.text-secondary-text.full-width(:style='span.ui.row.styles') Idle for {{ span.latency }}
                        template(v-else)
                          .col
                            .row.items-center.no-wrap.q-gap-6.q-py-xs.q-mt-xs
                              .row.q-gap-4.items-center.span-default-background.text-uppercase.border-radius-6.q-py-xs.q-px-sm(
                                v-if='span.type',
                                :style='span.ui.chip.styles'
                              )
                                q-icon(v-if='span.status === "error"', name='fa-solid fa-circle-exclamation', color='red', size='16px')
                                div {{ span.type }}
                              .text-secondary-text {{ span.name }}

                            .row.items-center.q-gap-12.q-ml-xs.q-mb-xs(style='font-size: 12px')
                              div {{ span.latency }}
                              div {{ span.computed.total_cost }}
                          .span-collapse-count.text-secondary-text(
                            v-if='span.repeat_count',
                            title='Number of times this span was repeated sequentially'
                          ) x{{ span.repeat_count }}
                          .row.q-px-sm(style='width: 400px; border-left: 1px solid #e5e7eb')
                            .row.items-center.span-default-background.border-radius-4.q-pa-xs.q-my-md(:style='span.ui.timeline.styles') {{ span.latency }}

                  template(v-else)
                    .center-flex-x.q-mt-sm
                      q-spinner-dots(color='primary', size='50px')

  .col-auto
    observability-traces-drawer(v-if='drawerOpened', :open='drawerOpened', :trace='selectedRow', :span='selectedSpan')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { formatDuration, formatTraceType } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'

export default {
  setup() {
    const { selected, selectedRow, get, loading } = useChroma('observability_traces')

    return {
      selectedRow,
      selected,
      get,
      loading,
      drawerOpened: ref(true),
      selectedSpan: ref(null),
    }
  },
  computed: {
    name() {
      return this.$store.getters.trace?.name || ''
    },
    type() {
      return formatTraceType(this.$store.getters.trace?.type)
    },
    channel() {
      return this.$store.getters.trace?.channel || ''
    },
    startTime() {
      return formatDateTime(this.$store.getters.trace?.start_time)
    },
    endTime() {
      return formatDateTime(this.$store.getters.trace?.end_time)
    },
    formattedLatency() {
      return formatDuration(this.$store.getters.trace?.latency)
    },
    embeddingCost() {
      const cost = this.$store.getters.trace?.cost_details?.embed
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    chatCompletionCost() {
      const cost = this.$store.getters.trace?.cost_details?.chat
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    rerankCost() {
      const cost = this.$store.getters.trace?.cost_details?.rerank
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    totalCost() {
      const cost = this.$store.getters.trace?.cost_details?.total
      if (!cost && cost !== 0) return ''
      return `$${cost.toFixed(6)}`
    },
    status() {
      return this.$store.getters.trace?.status || ''
    },
    spans() {
      return this.$store.getters.trace?.spans || []
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
        const trace = this.$store?.getters?.trace
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
            return '#DCFCE7'
          case 'embed':
            return '#FFEDD5'
          case 'rerank':
            return '#FFF7D9'
          case 'search':
            return '#DDE8F4'
          case 'tool':
            return '#E9D5FF'
          default:
            return 'rgba(104,64,194, .15)'
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
                backgroundImage: 'repeating-linear-gradient(45deg, #ffffff 0, #ffffff 2.5px, var(--q-light) 0, var(--q-light) 50%)',
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

    activeTraceId() {
      return this.$route.params?.id
    },
    // loading() {
    //   return !this.$store?.getters?.trace?.id
    // }
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setTrace', newVal)
        this.tab = 'retrieve'
        this.selectedSpan = this.selectedRow?.spans?.[0]
      }
    },
  },
  mounted() {
    if (!this.$store.getters.trace?.spans) {
      // this.getDetail({id: this.activeTraceId})
    }

    if (this.activeTraceId != this.$store.getters.trace?.id) {
      this.$store.commit('setTrace', this.selectedRow)
    }
    this.selectedSpan = this.selectedRow?.spans?.[0]
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

<style lang="stylus">
.span-default-background {
  background-color: #DBEAFE
}
.span-hoverable:hover{
    background-color: var(--q-table-hover)
}
.span-collapse-count {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 9px
  background-color: #E5E7EB
  border-radius: 50px;
  height: 30px;
  width: 30px;
  margin-right: 10px
  align-self: center
}
</style>

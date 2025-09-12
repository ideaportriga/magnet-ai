<template lang="pug">
.column.q-gap-8.fit.no-wrap
  .row.bar.items-center.relative-position.justify-between.no-wrap(
    v-for='(item, index) in data.slice(0, expanded ? data.length : show)',
    :key='index',
    @mouseenter='hover = index',
    @mouseleave='hover = null',
    @click='() => item.action(item.value)'
  )
    .bar-title.q-pl-8.relative-position.items-center.row.cursor-pointer(:style='{ width: `calc(100% - 55px)` }')
      .km-paragraph.ellipsis {{ item.title }}
      q-icon.col-auto.q-ml-4(name='o_info', color='secondary', v-if='item.tooltip')
        q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]')
          .text-secondary-text {{ item.tooltip }}
      .bar-bg(:style='`width: ${getPercentage(item.value)}%`', :class='[item.bg ? item.bg : "bg-primary-transparent"]')
    .row.items-center.q-gap-4.justify-end(style='min-width: 55px')
      .km-chart-value.row.justify-end {{ getFormatedValue(item.value) }}
      q-icon.cursor-pointer.col-auto.q-pt-2(v-if='hover === index && item.action', name='fas fa-chevron-right', color='secondary', size='12px')
  .text-center.q-mt-8(v-if='data.length > show')
    q-btn.col-auto(
      color='primary',
      @click='expanded = !expanded',
      flat,
      icon='fas fa-chevron-down',
      size='xs',
      :style='{ transform: `rotate(${expanded ? 180 : 0}deg)` }'
    )
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    data: {
      type: Array,
      default: () => [],
    },
    highestIsMax: {
      type: Boolean,
      default: false,
    },
    show: {
      type: Number,
      default: 5,
    },
  },
  setup() {
    return {
      hover: ref(null),
      expanded: ref(false),
    }
  },
  computed: {
    total() {
      if (this.highestIsMax) {
        return this.data.reduce((max, item) => Math.max(max, item.value), 0)
      }
      return this.data.reduce((acc, item) => acc + item.value, 0)
    },
  },
  methods: {
    getPercentage(value) {
      return (value * 100) / this.total
    },
    getFormatedValue(value) {
      if (value < 1000) return value
      if (value < 10000) return `${(value / 1000).toFixed(1)}k`
      if (value < 1000000) return `${(value / 1000).toFixed(0)}k`
      return `${(value / 1000000).toFixed(1)}M`
    },
  },
}
</script>
<style lang="stylus" scoped>
.bar
  height: 24px
  z-index: 2
  &-title
    height: 24px
  &-bg
    content: ''
    position: absolute
    left: 0
    top: 0
    height: 100%;
    // background-color: var(--q-primary-transparent)
    z-index: -1
    border-radius: 12px
</style>

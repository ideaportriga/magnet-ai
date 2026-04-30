<template>
  <div class="stack fit" data-gap="sm">
    <div v-for="(item, index) in data.slice(0, expanded ? data.length : show)" :key="index" class="cluster bar relative-position" data-wrap="no" data-justify="between" @mouseenter="hover = index" @mouseleave="hover = null" @click="() => item.action(item.value)">
      <div class="bar-title pl-sm relative-position cluster cursor-pointer" :style="{ width: `calc(100% - 55px)` }">
        <div class="km-paragraph ellipsis">{{ item.title }}</div>
        <km-glyph v-if="item.tooltip" class="flex-none ml-xs" name="info">
          <km-tooltip class="bg-white block-shadow km-description" self="top middle" :offset="[-50, -50]">
            <div class="text-secondary-text">{{ item.tooltip }}</div>
          </km-tooltip>
        </km-glyph>
        <div class="bar-bg" :style="`width: ${getPercentage(item.value)}%`" :class="[item.bg ? item.bg : &quot;bg-primary-transparent&quot;]" />
      </div>
      <div class="cluster" data-gap="xs" data-justify="end" style="min-inline-size: 55px">
        <div class="km-chart-value cluster" data-justify="end">{{ getFormatedValue(item.value) }}</div>
        <km-glyph v-if="hover === index &amp;&amp; item.action" class="cursor-pointer flex-none pt-2xs" name="chevron-right" size="12px" />
      </div>
    </div>
    <div v-if="data.length &gt; show" class="text-center mt-sm">
      <km-btn class="flex-none" tone="brand" flat icon="chevron-down" size="xs" :style="{ transform: `rotate(${expanded ? 180 : 0}deg)` }" @click="expanded = !expanded" />
    </div>
  </div>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
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
      m,
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
<style scoped>
.bar {
  block-size: 24px;
  z-index: 2;
}
.bar-title {
  block-size: 24px;
}
.bar-bg {
  content: '';
  position: absolute;
  inset-inline-start: 0;
  inset-block-start: 0;
  block-size: 100%;
  z-index: -1;
  border-radius: var(--ds-radius-xl);
}
</style>

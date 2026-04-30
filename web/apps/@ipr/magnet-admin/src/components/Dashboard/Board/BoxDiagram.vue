<template>
  <div class="cluster" data-gap="sm">
    <template v-for="(item, index) in data" :key="index">
      <div :style="{ flex: 1 }" @mouseenter="hover = index" @mouseleave="hover = null" @click="item.action &amp;&amp; item.action()"> 
        <div class="border-radius-12 cluster" data-justify="center" style="block-size: 90px" :class="`bg-${item.backgroundColor}`" :style="{ cursor: item.action ? &quot;pointer&quot; : &quot;default&quot; }">
          <div class="stack items-center p-md" data-gap="sm" data-wrap="no">
            <template v-if="item.icon">
              <km-glyph :name="item.icon" :tone="getIconTone(item.iconColor)" size="24px" />
            </template>
            <template v-else-if="item.svgIcon">
              <km-icon :name="item.svgIcon" width="20" height="20" :class="`text-${item.iconColor}`" />
            </template>
            <template v-else-if="item.title">
              <div class="text-center km-heading-4" :class="`text-${item.iconColor}`">{{ item.title }}</div>
            </template>
            <div class="km-chart-value full-width text-center" :class="`text-${item.iconColor}`">{{ item?.value }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
export default {
  props: {
    data: {
      type: Array,
      required: true,
    },
  },
  setup() {
    return {
      m,
      hover: ref(null),
    }
  },
  methods: {
    getIconTone(iconColor) {
      const tones = {
        'like-text': 'success',
        'error-text': 'danger',
        'secondary-text': 'subtle',
      }
      return tones[iconColor] || undefined
    },
  },
}
</script>
<style scoped>
.box-container {
  transition: transform 0.3s ease-in-out;
}
.box-container:hover {
  transform: translateY(-5px);
}
</style>

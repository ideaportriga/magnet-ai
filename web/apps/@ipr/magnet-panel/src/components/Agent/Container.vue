<template lang="pug">
.bg-panel-main-bg.full-height.column.no-wrap.bl-border.relative-position(v-if='selectedTab')
  .flex.row.justify-between.items-center.bg-header-bg.q-px-md(style='height: 55px; min-height: 55px; flex-shrink: 0')
    //logo
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }', :class='{ "bg-white": !isIconHide }')
      km-icon(:name='"magnet"', width='21', height='23', v-if='!is_icon_hide')
    //close button
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }')
      q-item(clickable, dense, v-if='show_close_button')
        q-icon.q-pa-xs.rounded-borders(name='close', rounded, size='20px', color='white', @click='hidePanel')
  km-image.redwood-strip(src='strip.png', v-if='$theme === "siebel"')
  // main scrollable content
  .col.overflow-auto
    agent-tab(:agent='selectedTab.config.agent', :tab='selectedTab', v-if='selectedTab')
  .bg-footer-bg.full-width.row.justify-center.items-center.footer.items-center(style='flex-shrink: 0')
    .footer-text Powered by Magnet AI by IdeaPort Riga
</template>
<script setup>
import { storeToRefs } from 'pinia'
import { useAiApps } from '@/pinia'
import { computed, watch } from 'vue'
import { getCurrentInstance } from 'vue'
const { appContext } = getCurrentInstance()
const aiApps = useAiApps()
const { selectedTab } = storeToRefs(aiApps)

const show_close_button = computed(() => selectedTab?.value?.entityObject?.channels?.web?.show_close_button || false)
const is_icon_hide = computed(() => selectedTab?.value?.entityObject?.channels?.web?.is_icon_hide || false)

const theme = computed(() => selectedTab?.value?.entityObject?.channels?.web?.theme || 'siebel')

watch(
  theme,
  (newVal) => {
    appContext.config.globalProperties.$setTheme(newVal)
  },
  { immediate: true }
)
// const channels = computed(() => selectedTab?.value?.entityObject?.channels)
</script>

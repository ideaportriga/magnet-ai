<template lang="pug">
.bg-panel-main-bg.full-height.column.no-wrap.bl-border.relative-position
  .flex.row.justify-between.items-center.bg-header-bg.q-px-md(style='height: 55px; min-height: 55px; flex-shrink: 0;')
    //logo
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }', :class='{ "bg-white": !isIconHide }')
      km-icon(:name='"magnet"', width='21', height='23', v-if='!isIconHide')
    //close button
    .flex.items-center.justify-center(:style='{ width: "32px", height: "32px", borderRadius: "50%" }')
      q-item(clickable, dense, v-if='show_close_button')
        q-icon.q-pa-xs.rounded-borders(name='close', rounded, size='20px', color='white', @click='hidePanel')
  km-image.redwood-strip(src='strip.png', v-if='$theme === "siebel"')
  .col
  // main scrollable content
  .col.overflow-auto
    agent-tab(:agent='aiApps.selectedTab.config.agent' :tab='aiApps.selectedTab' v-if='aiApps.selectedTab')
  .bg-footer-bg.full-width.row.justify-center.items-center.footer.items-center(style="flex-shrink: 0;")
    .footer-text Powered by Magnet AI by IdeaPort Riga


</template>
<script setup>
import { useAiApps } from '@/pinia'

const aiApps = useAiApps()

</script>
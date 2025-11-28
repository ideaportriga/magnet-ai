<template lang="pug">
.q-pa-xs.col-xs-12(:key='row.system_name', @mouseenter='hovered[row.system_name] = true', @mouseleave='hovered[row.system_name] = false')
  q-card.row(bordered, flat, style='min-width: 400px; min-height: 63px', @click='openTabDetails(row)')
    .row.items-center.q-px-md.full-width
      .col-auto(style='width: 60px')
        .row.items-center(v-if='hovered[row.system_name] && !isMoving')
          km-btn(flat, icon='fas fa-bars', iconSize='20px', color='secondary-text')
          q-tooltip(anchor='top middle', self='bottom middle') Drag to reorder AI Tab
      .col
        .row
          .col-auto.km-heading-4 {{ row.name }}
          .col-auto.q-ml-auto
        .row(v-if='row.description')
          .km-label {{ row.description }}
      .col-auto.q-mr-sm
        q-chip.q-my-none(text-color='primary', color='primary-light', size='12px') 
          div {{ getTabByVal(row.tab_type)?.label }}
      .col-auto(style='min-width: 85px')
        .row.items-center
          .col-auto
            km-btn.q-mr-sm(
              v-if='hovered[row.system_name] || row.inactive',
              flat,
              :icon='row?.inactive ? "fas fa-eye-slash" : "fas fa-eye"',
              @click.stop='setInactive',
              iconSize='14px',
              color='secondary-text'
            )
            q-tooltip(anchor='top middle', self='bottom middle') {{ row?.inactive ? 'Activate AI Tab' : 'Deactivate AI Tab' }}
          .col-auto
            km-btn(v-if='hovered[row.system_name]', flat, icon='fas fa-trash', @click.stop='removeRecord', iconSize='14px', color='secondary-text')
            q-tooltip(anchor='top middle', self='bottom middle') Delete AI Tab
</template>
<script>
import { getTabByVal } from '@/config/ai_apps/tab_types'
export default {
  props: {
    row: Object,
    hovered: Object,
    isMoving: Boolean,
    openTabDetails: Function,
    removeRecord: Function,
    setInactive: Function,
  },
  setup() {
    return {
      getTabByVal,
    }
  },
  // emits: ['openTabDetails']
}
</script>

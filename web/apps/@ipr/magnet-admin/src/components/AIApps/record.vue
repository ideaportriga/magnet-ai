<template>
  <div :key="row.system_name" class="ai-tab-row p-xs" @mouseenter="emit('hover', row.system_name, true)" @mouseleave="emit('hover', row.system_name, false)">
    <km-card bordered flat class="ai-tab-row__card" @click="openTabDetails(row)">
      <div class="cluster ai-tab-row__inner px-md py-sm full-width" data-align="center" data-wrap="no">
        <div class="ai-tab-row__handle">
          <km-btn
            flat
            icon="menu"
            icon-size="18px"
            tone="subtle"
            :tooltip="m.aiApps_dragToReorder()"
            :class="{ 'is-invisible': !hovered[row.system_name] || isMoving }"
          />
        </div>
        <div class="ai-tab-row__body">
          <div class="km-heading-4">{{ row.name }}</div>
          <div v-if="row.description" class="km-label text-secondary-text">{{ row.description }}</div>
        </div>
        <km-chip
          tone="brand"
          :label="getTabByVal(row.tab_type)?.label"
        />
        <div class="ai-tab-row__actions">
          <km-btn
            flat
            :icon="row?.inactive ? 'eye-off' : 'eye'"
            icon-size="14px"
            tone="subtle"
            :tooltip="row?.inactive ? m.aiApps_activateTab() : m.aiApps_deactivateTab()"
            :class="{ 'is-invisible': !(hovered[row.system_name] || row.inactive) }"
            @click.stop="setInactive"
          />
          <km-btn
            flat
            icon="delete"
            icon-size="14px"
            tone="subtle"
            :tooltip="m.aiApps_deleteTab()"
            :class="{ 'is-invisible': !hovered[row.system_name] }"
            @click.stop="removeRecord"
          />
        </div>
      </div>
    </km-card>
  </div>
</template>
<script>
import { getTabByVal } from '@/config/ai_apps/tab_types'
import { m } from '@/paraglide/messages'
export default {
  props: {
    row: Object,
    hovered: Object,
    isMoving: Boolean,
    openTabDetails: Function,
    removeRecord: Function,
    setInactive: Function,
  },
  emits: ['hover'],
  setup(_, { emit }) {
    return {
      m,
      getTabByVal,
      emit,
    }
  },
}
</script>

<style>
.ai-tab-row__card {
  cursor: pointer;
  min-inline-size: 400px;
}
/* Lock the row's vertical rhythm. Action buttons keep their slot whether
 * hovered or not (`.is-invisible` hides them without removing layout), so
 * the card no longer jumps in height when the eye/trash icons appear. */
.ai-tab-row__inner {
  min-block-size: 64px;
}
.ai-tab-row__handle {
  inline-size: 32px;
  display: inline-flex;
  justify-content: center;
}
.ai-tab-row__body {
  flex: 1 1 auto;
  min-inline-size: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ai-tab-row__actions {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-xs);
  inline-size: 72px;
  justify-content: flex-end;
}
.ai-tab-row .is-invisible {
  visibility: hidden;
  pointer-events: none;
}
</style>

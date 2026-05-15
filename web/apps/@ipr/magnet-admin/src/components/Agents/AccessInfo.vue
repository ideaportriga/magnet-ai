<template>
  <!--
    Record-level access metadata display (PR 9a of access-control plan).
    Two variants:
      - default (chip strip) — inline next to other action chips.
      - tooltip — vertical key/value rows for the record-info tooltip on
        the (i) icon in the details header.
    Renders nothing for legacy agents that haven't been migrated onto the
    PR 7/8 pipeline yet (no visibility / owner_id / department_id).
  -->
  <template v-if="!hasAccessInfo" />
  <template v-else-if="variant === 'tooltip'">
    <div class="details-header__record-tooltip-row stack" data-gap="2xs">
      <div class="details-header__record-tooltip-label km-button-xs-text">{{ m.access_visibilityLabel() }}</div>
      <div class="details-header__record-tooltip-value km-description">{{ visibilityLabel }}</div>
    </div>
    <div v-if="agent?.owner_id" class="details-header__record-tooltip-row stack" data-gap="2xs">
      <div class="details-header__record-tooltip-label km-button-xs-text">{{ m.access_ownerLabel() }}</div>
      <div class="details-header__record-tooltip-value km-description">{{ shortId(agent.owner_id) }}</div>
    </div>
    <div v-if="agent?.department_id" class="details-header__record-tooltip-row stack" data-gap="2xs">
      <div class="details-header__record-tooltip-label km-button-xs-text">{{ m.access_departmentLabel() }}</div>
      <div class="details-header__record-tooltip-value km-description">{{ shortId(agent.department_id) }}</div>
    </div>
  </template>
  <div v-else class="cluster gap-sm items-center" data-test="agent-access-info">
    <km-chip
      v-if="agent?.visibility"
      :icon="visibilityIcon"
      :label="visibilityLabel"
      tone="muted"
      size="sm"
      data-test="agent-visibility-chip"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

export default {
  name: 'AgentAccessInfo',
  props: {
    agent: {
      type: Object,
      default: null,
    },
    variant: {
      type: String,
      default: 'chip', // 'chip' | 'tooltip'
    },
  },
  setup(props) {
    const hasAccessInfo = computed(() => {
      const a = props.agent
      return Boolean(a && (a.visibility || a.owner_id || a.department_id))
    })

    const visibilityIcon = computed(() => {
      switch (props.agent?.visibility) {
        case 'private': return 'lock'
        case 'department': return 'group'
        case 'tenant': return 'globe'
        default: return 'info'
      }
    })

    const visibilityLabel = computed(() => {
      switch (props.agent?.visibility) {
        case 'private': return m.access_visibilityPrivate()
        case 'department': return m.access_visibilityDepartment()
        case 'tenant': return m.access_visibilityTenant()
        default: return props.agent?.visibility || ''
      }
    })

    function shortId(id) {
      return id ? String(id).slice(0, 8) : ''
    }

    return { hasAccessInfo, visibilityIcon, visibilityLabel, shortId, m }
  },
}
</script>

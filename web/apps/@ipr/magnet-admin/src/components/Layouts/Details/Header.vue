<template>
  <div class="details-header stack" data-gap="sm">
    <div class="details-header__top cluster" data-wrap="no" data-align="start" data-gap="md">
      <div class="details-header__identity stack flex-1 km-flex-min-w-0" data-gap="2xs">
        <km-input-flat class="km-heading-4 full-width text-black" data-test="name-input" :placeholder="namePlaceholder || m.common_name()" :model-value="name" @change="emit('update:name', $event)" />
        <km-input-flat v-if="showDescription" class="km-description full-width text-black" data-test="description-input" :placeholder="descriptionPlaceholder || m.common_description()" :model-value="description" @change="emit('update:description', $event)" />
      </div>
      <div v-if="hasToolbar" class="details-header__toolbar cluster flex-none" data-align="center" data-wrap="no" data-gap="xs">
        <slot name="actions" />
        <div v-if="showRecordInfoButton" class="details-header__record-info flex-none">
          <DsTooltip placement="bottom" :side-offset="8">
            <template #trigger>
              <km-btn flat round dense icon="info" icon-size="16px" :aria-label="m.common_recordInfo()" />
            </template>
            <div class="details-header__record-tooltip-content stack" data-gap="sm">
              <div v-for="field in recordInfoFields" :key="field.label" class="details-header__record-tooltip-row stack" data-gap="2xs">
                <div class="details-header__record-tooltip-label km-button-xs-text">{{ field.label }}</div>
                <div class="details-header__record-tooltip-value km-description">{{ field.value }}</div>
              </div>
            </div>
          </DsTooltip>
        </div>
      </div>
    </div>

    <div class="details-header__meta stack" data-gap="xs">
      <div class="details-header__system-name cluster" data-gap="sm" data-wrap="no" data-align="center">
        <div class="details-header__system-name-field">
          <slot name="system-name" :value="systemName" :update="(value) =&gt; emit('update:systemName', value)">
            <km-input-flat class="details-header__system-name-input km-description text-black full-width font-mono" data-test="system-name-input" :placeholder="systemNamePlaceholder || m.placeholder_enterSystemNameReadable()" :model-value="systemName" :rules="systemNameRules" @change="emit('update:systemName', $event)" @focus="showInfo = true" @blur="showInfo = false" />
          </slot>
        </div>
      </div>
      <div v-if="showInfo" class="details-header__system-name-hint km-description text-secondary-text">{{ infoText || m.hint_systemNameRecommendation() }}</div>
      <div v-if="$slots.meta" class="details-header__meta-extra">
        <slot name="meta" />
      </div>
    </div>

    <div v-if="$slots.variants" class="details-header__variants">
      <slot name="variants" />
    </div>
  </div>
</template>

<script setup>
/* eslint-disable */
import { computed, ref, useSlots } from 'vue'
import { m } from '@/paraglide/messages'
import { DsTooltip } from '@ds/primitives'

const props = defineProps({
  name: {
    type: String,
    default: '',
  },
  description: {
    type: String,
    default: '',
  },
  systemName: {
    type: String,
    default: '',
  },
  namePlaceholder: {
    type: String,
    default: '',
  },
  descriptionPlaceholder: {
    type: String,
    default: '',
  },
  systemNamePlaceholder: {
    type: String,
    default: '',
  },
  systemNameRules: {
    type: Array,
    default: () => [],
  },
  infoText: {
    type: String,
    default: '',
  },
  showDescription: {
    type: Boolean,
    default: true,
  },
  showRecordInfo: {
    type: Boolean,
    default: false,
  },
  createdAt: {
    type: [String, Number, Date],
    default: '',
  },
  updatedAt: {
    type: [String, Number, Date],
    default: '',
  },
  createdBy: {
    type: String,
    default: '',
  },
  updatedBy: {
    type: String,
    default: '',
  },
  updatedLabel: {
    type: String,
    default: '',
  },
})
const showInfo = ref(false)
const emit = defineEmits(['update:name', 'update:description', 'update:systemName'])
const slots = useSlots()

const showRecordInfoButton = computed(() => props.showRecordInfo || Boolean(props.createdAt || props.updatedAt))
const hasToolbar = computed(() => showRecordInfoButton.value || Boolean(slots.actions))

const recordInfoFields = computed(() => [
  { label: m.common_createdLabel(), value: formatDate(props.createdAt) },
  { label: props.updatedLabel || m.common_modified(), value: formatDate(props.updatedAt) },
  { label: m.common_createdBy(), value: props.createdBy || m.common_unknown() },
  { label: m.common_modifiedBy(), value: props.updatedBy || m.common_unknown() },
])

function formatDate(value) {
  if (!value) return m.common_unknown()
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`
}
</script>

<style>
.details-header {
  min-inline-size: 0;
}

.details-header__top {
  align-items: flex-start;
}

.details-header__identity {
  min-inline-size: 0;
}

.details-header__toolbar {
  align-items: center;
  padding-block-start: var(--ds-space-xs);
}

.details-header__record-info {
  display: inline-flex;
  align-items: center;
}

.details-header__meta {
  min-inline-size: 0;
}

.details-header__system-name {
  max-inline-size: 100%;
  min-inline-size: 0;
}

.details-header__system-name-field {
  flex: 0 1 24rem;
  min-inline-size: 0;
  max-inline-size: 24rem;
}

.details-header__system-name-input {
  inline-size: 100%;
}

.details-header__system-name-input .km-input-flat__field {
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-label);
}

.details-header__system-name-hint,
.details-header__meta-extra {
  margin-inline-start: var(--ds-space-2xs);
}

.details-header__system-name-hint {
  max-inline-size: 24rem;
}

.details-header__record-tooltip-content {
  min-inline-size: 12rem;
}

.details-header__record-tooltip-label {
  color: var(--ds-color-tooltip-text);
  opacity: 0.72;
}

.details-header__record-tooltip-value {
  font-family: var(--ds-font-mono);
  color: var(--ds-color-tooltip-text);
  white-space: nowrap;
}
</style>

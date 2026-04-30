<script setup lang="ts">
/**
 * `<km-select-flat>` — borderless / underlined select used in toolbar /
 * filter contexts. Built on top of `<DsSelect>` with an override layer that
 * removes the field border and renders a chip-like trigger.
 *
 * Public API preserved:
 *   modelValue, options, placeholder, hideSelected, showLabel, itemProps
 *
 * Slots: `option` (legacy custom item render with `{ option, modelValue,
 * select, itemProps }` — kept for compatibility with admin call-sites that
 * render rich list items inside the dropdown).
 */

import { computed, ref } from 'vue'
import {
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'
import DsSelect, { type DsSelectOption } from '../primitives/Select/DsSelect.vue'
import KmGlyph from './KmGlyph.vue'

interface KmSelectFlatOption {
  label?: string
  value?: unknown
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    placeholder?: string
    modelValue?: unknown
    options?: KmSelectFlatOption[] | string[]
    hideSelected?: boolean
    showLabel?: boolean
    itemProps?: Record<string, string>
  }>(),
  {
    placeholder: '',
    options: () => [],
    hideSelected: false,
    showLabel: false,
    itemProps: () => ({ class: 'km-select-flat__item' }),
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

defineSlots<{
  option?: (props: {
    option: KmSelectFlatOption
    modelValue: unknown
    select: (option: KmSelectFlatOption) => void
    itemProps?: Record<string, string>
  }) => unknown
}>()

const open = ref(false)

const normalisedOptions = computed<KmSelectFlatOption[]>(() =>
  (props.options as unknown[]).map((opt) =>
    typeof opt === 'string' ? { label: opt, value: opt } : (opt as KmSelectFlatOption),
  ),
)

/**
 * If no `option` slot is provided, the simple path renders `<DsSelect>`
 * directly (option objects → DsSelectOption shape). The output value mirrors
 * the legacy contract: emits the matched option object (or string if input
 * was a string list).
 */
const dsOptions = computed<DsSelectOption[]>(() =>
  normalisedOptions.value.map((opt) => ({
    value: String(opt.value ?? opt.label ?? ''),
    label: String(opt.label ?? opt.value ?? ''),
  })),
)

const dsModelValue = computed<string | undefined>(() => {
  if (props.modelValue == null || props.modelValue === '') return undefined
  if (typeof props.modelValue === 'object') {
    const v = (props.modelValue as KmSelectFlatOption).value
    return v == null ? undefined : String(v)
  }
  return String(props.modelValue)
})

const selectedLabel = computed(() => {
  if (!props.modelValue) return props.placeholder
  if (props.showLabel) {
    const match = normalisedOptions.value.find(
      (o) => o.value === (props.modelValue as KmSelectFlatOption).value,
    )
    return match?.label ?? props.placeholder
  }
  if (typeof props.modelValue === 'string') return props.modelValue
  return (props.modelValue as KmSelectFlatOption).label ?? props.placeholder
})

function handleSelect(option: KmSelectFlatOption) {
  emit('update:modelValue', option)
  open.value = false
}

function handleDsUpdate(next: string) {
  const match = normalisedOptions.value.find(
    (o) => String(o.value ?? o.label ?? '') === next,
  )
  if (match) emit('update:modelValue', match)
}

function shouldHide(option: KmSelectFlatOption): boolean {
  if (!props.hideSelected) return false
  const current = props.modelValue as KmSelectFlatOption | undefined
  return current?.value === option.value
}
</script>

<template>
  <!-- Slot-based path: legacy custom item render. Wrap DsSelect-styled
       chip trigger in a Popover so the slot's <li> markup keeps working. -->
  <PopoverRoot v-if="$slots.option" v-model:open="open">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="km-select-flat__trigger"
        data-test="km-select-flat"
      >
        <span class="km-select-flat__label">{{ selectedLabel }}</span>
        <KmGlyph
          name="chevron-down"
          size="20px"
          tone="seamless"
          class="km-select-flat__chevron"
          :style="{ transform: open ? 'rotate(180deg)' : '' }"
        />
      </button>
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent class="km-select-flat__menu" :side-offset="4" align="start">
        <template v-for="option in normalisedOptions" :key="String(option.value ?? option.label)">
          <button
            v-if="!shouldHide(option)"
            type="button"
            class="km-select-flat__option"
            :class="itemProps?.class"
            :data-selected="(modelValue as KmSelectFlatOption | undefined)?.value === option.value ? 'true' : undefined"
            data-test="km-select-flat-option"
            @click="handleSelect(option)"
          >
            <slot
              name="option"
              :option="option"
              :model-value="modelValue"
              :select="handleSelect"
              :item-props="itemProps"
            >
              {{ option.label ?? option }}
            </slot>
          </button>
        </template>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>

  <!-- Plain path: render via <DsSelect> with the borderless chip override. -->
  <DsSelect
    v-else
    class="km-select-flat km-select-flat--ds"
    :model-value="dsModelValue"
    :options="dsOptions"
    :placeholder="placeholder"
    data-test="km-select-flat"
    @update:model-value="handleDsUpdate"
  />
</template>

<style>
/* DsSelect-rendered variant: strip the field chrome so it reads as a chip. */
.km-select-flat--ds .ds-select__trigger {
  min-block-size: auto;
  block-size: auto;
  padding-inline: var(--ds-space-sm);
  padding-block: var(--ds-space-2xs);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-pill, 999px);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
}
.km-select-flat--ds .ds-select__trigger:hover {
  background: var(--ds-color-light);
}
.km-select-flat--ds .ds-select__trigger:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

/* Slot-based custom-render variant: a button-shaped chip trigger. */
.km-select-flat__trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  background: transparent;
  color: var(--ds-color-black);
  border: 0;
  border-radius: var(--ds-radius-pill, 999px);
  cursor: pointer;
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  user-select: none;
}
.km-select-flat__trigger:hover { background: var(--ds-color-light); }
.km-select-flat__trigger:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

.km-select-flat__label {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}
.km-select-flat__chevron {
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
  flex: none;
}

.km-select-flat__menu {
  z-index: var(--ds-z-popover);
  min-inline-size: 12rem;
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  padding: var(--ds-space-2xs);
}
.km-select-flat__option {
  display: block;
  inline-size: 100%;
  text-align: start;
  padding: var(--ds-space-xs) var(--ds-space-md);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
}
.km-select-flat__option:hover { background: var(--ds-color-light); }
.km-select-flat__option[data-selected='true'] {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
}
</style>

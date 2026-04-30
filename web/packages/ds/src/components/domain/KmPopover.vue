<script setup lang="ts">
/**
 * `<km-popover>` — drop-in popover that auto-attaches to its previous DOM
 * sibling (Quasar parity). New code should prefer `<DsPopover>` with an
 * explicit trigger slot.
 *
 * Public API (preserved): `modelValue, anchor, placement, offset,
 * persistent`. Visuals are inherited from `<DsPopover>` (`.ds-popover`).
 */

import { computed, onBeforeUnmount, onMounted, ref, useTemplateRef } from 'vue'
import {
  PopoverAnchor,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
} from 'reka-ui'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    /** Quasar-style anchor `<vert> <horz>` (e.g. `bottom right`). */
    anchor?: string
    /** Quasar-style self alignment — informational only, kept for parity. */
    self?: string
    /** Explicit placement (overrides `anchor` if provided). */
    placement?: 'top' | 'right' | 'bottom' | 'left'
    /** `[skidding, distance]` in pixels. */
    offset?: [number, number]
    /** When true, clicking outside / Esc does NOT close the popover. */
    persistent?: boolean
  }>(),
  {
    modelValue: undefined,
    persistent: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const internalOpen = ref(false)
const isControlled = computed(() => props.modelValue !== undefined)
const effectiveOpen = computed({
  get: () => (isControlled.value ? !!props.modelValue : internalOpen.value),
  set: (v: boolean) => {
    internalOpen.value = v
    if (isControlled.value) emit('update:modelValue', v)
  },
})

const anchorRef = useTemplateRef<HTMLElement>('anchor')
let parent: HTMLElement | null = null

function onParentClick(event: Event) {
  event.stopPropagation()
  effectiveOpen.value = !effectiveOpen.value
}

onMounted(() => {
  const node = anchorRef.value
  if (!node) return
  parent = (node.previousElementSibling as HTMLElement) ?? (node.parentElement as HTMLElement)
  parent?.addEventListener('click', onParentClick)
})
onBeforeUnmount(() => parent?.removeEventListener('click', onParentClick))

const side = computed<'top' | 'right' | 'bottom' | 'left'>(() => {
  if (props.placement) return props.placement
  const a = props.anchor?.split(' ')[0]
  if (a === 'top') return 'top'
  if (a === 'left') return 'left'
  if (a === 'right') return 'right'
  return 'bottom'
})
const align = computed<'start' | 'center' | 'end'>(() => {
  const a = props.anchor?.split(' ')[1]
  if (a === 'left' || a === 'start') return 'start'
  if (a === 'right' || a === 'end') return 'end'
  return 'center'
})
const sideOffset = computed(() => props.offset?.[1] ?? 6)
const alignOffset = computed(() => props.offset?.[0] ?? 0)

function onPointerDownOutside(event: Event) {
  if (props.persistent) event.preventDefault()
}
function onEscape(event: KeyboardEvent) {
  if (props.persistent) event.preventDefault()
}
</script>

<template>
  <PopoverRoot v-model:open="effectiveOpen">
    <PopoverAnchor as-child>
      <span ref="anchor" class="km-popover__anchor" aria-hidden="true" />
    </PopoverAnchor>
    <PopoverPortal>
      <PopoverContent
        class="ds-popover km-popover"
        :side="side"
        :align="align"
        :side-offset="sideOffset"
        :align-offset="alignOffset"
        data-test="km-popover"
        @pointer-down-outside="onPointerDownOutside"
        @escape-key-down="onEscape"
      >
        <slot />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
.km-popover__anchor { display: contents; }
.km-popover {
  /* Inherits .ds-popover visuals; same z-index stacking as the menu primitive. */
  z-index: var(--ds-z-popover, 5000);
}
</style>

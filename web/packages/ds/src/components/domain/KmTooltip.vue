<script setup lang="ts">
/**
 * `<km-tooltip>` — auto-attaching tooltip. Quasar's `<q-tooltip>` lived
 * *inside* the trigger element and wired itself to that parent on hover /
 * focus. We replicate that pattern: the component watches its previous DOM
 * sibling (or, fallback, its parent) for `mouseenter` / `mouseleave` /
 * `focusin` / `focusout` and renders content via Reka's Tooltip in
 * controlled-open mode.
 *
 * Visuals are reused from `<DsTooltip>` — we render the same Reka primitives
 * and inherit `.ds-tooltip` / `.ds-tooltip__arrow` styles that DsTooltip
 * exposes globally. For new code prefer `<DsTooltip>` with an explicit
 * trigger.
 */

import { ref, computed, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'
import {
  TooltipArrow,
  TooltipContent,
  TooltipPortal,
  TooltipProvider,
  TooltipRoot,
} from 'reka-ui'

const props = withDefaults(
  defineProps<{
    /** Tooltip text (legacy prop name). */
    label?: string
    /** Alternate prop name accepted by some legacy call-sites. */
    text?: string
    /** Quasar-style anchor `vert horiz` (e.g. `top middle`). */
    anchor?: string
    /** Quasar-style self alignment — informational only, kept for parity. */
    self?: string
    /** Explicit DsTooltip-style placement (overrides `anchor` if given). */
    placement?: 'top' | 'right' | 'bottom' | 'left'
    /** `[skidding, distance]` in pixels. */
    offset?: [number, number]
    /** Delay before showing, in ms. */
    delay?: number
  }>(),
  {
    label: '',
    text: '',
    anchor: 'top middle',
    self: 'bottom middle',
    delay: 250,
  },
)

const open = ref(false)
const anchorRef = useTemplateRef<HTMLElement>('anchor')
let parent: HTMLElement | null = null
let showTimer: number | null = null

function show() {
  if (showTimer) clearTimeout(showTimer)
  showTimer = window.setTimeout(() => { open.value = true }, props.delay)
}
function hide() {
  if (showTimer) { clearTimeout(showTimer); showTimer = null }
  open.value = false
}

onMounted(() => {
  parent = (anchorRef.value?.previousElementSibling as HTMLElement) ?? (anchorRef.value?.parentElement as HTMLElement)
  if (!parent) return
  parent.addEventListener('mouseenter', show)
  parent.addEventListener('mouseleave', hide)
  parent.addEventListener('focusin', show)
  parent.addEventListener('focusout', hide)
})
onBeforeUnmount(() => {
  if (!parent) return
  parent.removeEventListener('mouseenter', show)
  parent.removeEventListener('mouseleave', hide)
  parent.removeEventListener('focusin', show)
  parent.removeEventListener('focusout', hide)
  if (showTimer) clearTimeout(showTimer)
})

/** Map legacy `anchor` (or new `placement`) → Reka `side`. */
const side = computed<'top' | 'right' | 'bottom' | 'left'>(() => {
  if (props.placement) return props.placement
  const a = props.anchor?.split(' ')[0]
  if (a === 'right') return 'right'
  if (a === 'bottom') return 'bottom'
  if (a === 'left') return 'left'
  return 'top'
})
const align = computed<'start' | 'center' | 'end'>(() => {
  const a = props.anchor?.split(' ')[1]
  if (a === 'left' || a === 'start') return 'start'
  if (a === 'right' || a === 'end') return 'end'
  return 'center'
})
const sideOffset = computed(() => props.offset?.[1] ?? 6)
const alignOffset = computed(() => props.offset?.[0] ?? 0)
</script>

<template>
  <TooltipProvider :delay-duration="0" :disable-hoverable-content="false">
    <TooltipRoot :open="open" @update:open="open = $event">
      <span ref="anchor" class="km-tooltip__anchor" aria-hidden="true" />
      <TooltipPortal>
        <TooltipContent
          v-if="open"
          class="ds-tooltip km-tooltip"
          :side="side"
          :align="align"
          :side-offset="sideOffset"
          :align-offset="alignOffset"
          data-test="km-tooltip"
        >
          <slot>{{ label || text }}</slot>
          <TooltipArrow class="ds-tooltip__arrow km-tooltip__arrow" />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<style>
.km-tooltip__anchor { display: contents; }
.km-tooltip {
  /* Inherits .ds-tooltip visuals; ensure z-index sits above legacy overlays. */
  z-index: var(--ds-z-tooltip, 6000);
  user-select: none;
  pointer-events: none;
  max-inline-size: 320px;
}
</style>

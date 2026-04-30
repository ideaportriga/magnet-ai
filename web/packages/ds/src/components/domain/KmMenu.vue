<script setup lang="ts">
/**
 * `<km-menu>` — popup menu attached to its preceding sibling element.
 *
 * Quasar's `<q-menu>` lived inside the trigger and attached itself on
 * mount. We replicate that pattern so call-sites continue to work
 * unchanged: a `pointerdown` listener on the previous DOM sibling toggles
 * the menu.
 *
 * Visuals are inherited from `<DsDropdownMenu>` (`.ds-menu` class) —
 * DsDropdownMenu itself takes an `items` array which doesn't fit the
 * slot-based legacy contract, so we render Reka's primitives directly and
 * style them with the same class.
 *
 * Public API (preserved): `modelValue, anchor, self, offset, autoClose`,
 * plus `placement` / `align` / `sideOffset` for new call-sites.
 */
import { computed, onBeforeUnmount, onMounted, ref, useTemplateRef } from 'vue'
import { PopoverAnchor, PopoverContent, PopoverPortal, PopoverRoot } from 'reka-ui'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    /** Quasar-style anchor `<vert> <horz>` (e.g. `bottom right`). */
    anchor?: string
    /** Quasar-style self alignment — informational only. */
    self?: string
    /** `[skidding, distance]` in pixels. */
    offset?: [number, number]
    /** Close the menu automatically when an item is clicked. */
    autoClose?: boolean
    /** Explicit placement override. */
    placement?: 'top' | 'right' | 'bottom' | 'left'
    /** Explicit align override. */
    align?: 'start' | 'center' | 'end'
    sideOffset?: number
  }>(),
  {
    modelValue: undefined,
    autoClose: true,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const open = ref(false)
const isControlled = computed(() => props.modelValue !== undefined)
const effectiveOpen = computed({
  get: () => (isControlled.value ? !!props.modelValue : open.value),
  set: (v: boolean) => {
    open.value = v
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
const alignComputed = computed<'start' | 'center' | 'end'>(() => {
  if (props.align) return props.align
  const a = props.anchor?.split(' ')[1]
  if (a === 'left' || a === 'start') return 'start'
  if (a === 'right' || a === 'end') return 'end'
  return 'start'
})
const sideOffsetComputed = computed(() => props.sideOffset ?? props.offset?.[1] ?? 4)
const alignOffsetComputed = computed(() => props.offset?.[0] ?? 0)
</script>

<template>
  <PopoverRoot v-model:open="effectiveOpen">
    <PopoverAnchor as-child>
      <span ref="anchor" class="km-menu__anchor" aria-hidden="true" />
    </PopoverAnchor>
    <PopoverPortal>
      <PopoverContent
        class="ds-menu km-menu"
        :side="side"
        :align="alignComputed"
        :side-offset="sideOffsetComputed"
        :align-offset="alignOffsetComputed"
        data-test="km-menu"
        @click="autoClose && (effectiveOpen = false)"
      >
        <slot />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
.km-menu__anchor { display: contents; }
.km-menu {
  /* Inherits .ds-menu visuals from DsDropdownMenu's stylesheet. */
  z-index: var(--ds-z-overlay, 2000);
  min-inline-size: 160px;
}
</style>

<script setup lang="ts">
/**
 * `<km-nav-btn>` — primary navigation button for the admin sidebar/toolbar.
 * The legacy component combines an icon, a label, an optional chevron and
 * an "active" highlight tied to the current route. The Vue Router
 * integration stays thin: callers either pass `:to` and we render via
 * `<RouterLink>`, or they pass a click handler.
 */

import { computed, useSlots } from 'vue'
import KmGlyph from './KmGlyph.vue'
import KmIcon from './KmIcon.vue'

const props = withDefaults(
  defineProps<{
    label?: string
    icon?: string
    svgIcon?: string
    /** When set, the component renders as a `<RouterLink :to="to">`. */
    to?: string | object
    /**
     * Route slug (no leading `/`). When provided, clicking the button emits
     * `navigate` with this path so the parent can route via `$router.push`.
     */
    path?: string
    /**
     * Currently active route — full path (e.g. `/deep-research/runs/123`).
     * The button lights up when this path equals `/<path>` or starts with
     * `/<path>/`, so multi-segment slugs (`deep-research/runs`, `usage/rag`)
     * highlight on detail/sub-routes too.
     */
    parentRoute?: string
    /** Other route slugs that should also light up this button. */
    alternativePaths?: string[]
    active?: boolean
    /** Visual size. */
    size?: 'sm' | 'md'
    /** Show a small expand-chevron at the end. */
    expandable?: boolean
    expanded?: boolean
    disabled?: boolean
  }>(),
  {
    size: 'md',
    alternativePaths: () => [],
  },
)

const emit = defineEmits<{
  click: [Event]
  navigate: [path: string]
}>()

const tag = computed(() => (props.to ? 'router-link' : 'button'))
const slots = useSlots()
const hasDefault = computed(() => Boolean(slots.default))

function pathMatches(currentPath: string | undefined, candidate: string): boolean {
  if (!currentPath || !candidate) return false
  const target = `/${candidate}`
  return currentPath === target || currentPath.startsWith(`${target}/`)
}

const isActive = computed(() => {
  if (props.active) return true
  if (!props.parentRoute || !props.path) return false
  if (pathMatches(props.parentRoute, props.path)) return true
  return props.alternativePaths.some((p) => pathMatches(props.parentRoute, p))
})

function onClick(event: Event) {
  emit('click', event)
  if (props.path && !props.to) emit('navigate', props.path)
}
</script>

<template>
  <component
    :is="tag"
    :to="to"
    class="km-nav-btn"
    :data-size="size"
    :data-active="isActive ? 'true' : undefined"
    :data-disabled="disabled ? 'true' : undefined"
    :type="tag === 'button' ? 'button' : undefined"
    :disabled="tag === 'button' && disabled ? true : undefined"
    data-test="km-nav-btn"
    @click="onClick"
  >
    <KmGlyph v-if="icon" :name="icon" size="16px" />
    <KmIcon v-if="svgIcon" :name="svgIcon" width="24" height="18" />
    <span v-if="label || hasDefault" class="km-nav-btn__label">
      <slot>{{ label }}</slot>
    </span>
    <svg
      v-if="expandable"
      class="km-nav-btn__chevron"
      :data-expanded="expanded ? 'true' : undefined"
      width="14"
      height="14"
      viewBox="0 0 14 14"
      aria-hidden="true"
    >
      <path d="M5 4 L9 7 L5 10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  </component>
</template>

<style>
.km-nav-btn {
  /* Icons inside the nav button follow the button's text color, so the
     hover/active state recolor reaches the leading glyph too. */
  --km-glyph-color: currentColor;

  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-sm);
  inline-size: 100%;
  padding: var(--ds-space-sm) var(--ds-space-md);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  color: var(--ds-color-secondary-text);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  text-align: start;
  text-decoration: none;
  cursor: pointer;
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out);
}
.km-nav-btn:hover { background: var(--ds-color-light); color: var(--ds-color-black); }
.km-nav-btn:focus-visible { outline: 2px solid var(--ds-color-primary); outline-offset: 2px; }

.km-nav-btn[data-size='sm'] { padding: var(--ds-space-xs) var(--ds-space-sm); font-size: var(--ds-font-size-caption); }
.km-nav-btn[data-active='true'] {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
}
.km-nav-btn[data-disabled='true'] { opacity: 0.5; pointer-events: none; }

.km-nav-btn__label { flex: 1 1 auto; min-inline-size: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.km-nav-btn__chevron {
  flex: none;
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
  color: var(--ds-color-icon);
}
.km-nav-btn__chevron[data-expanded='true'] { transform: rotate(90deg); }
</style>

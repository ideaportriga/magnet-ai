<script setup lang="ts">
/**
 * `<km-nav-section>` — collapsible nav section for the admin sidebar. Drop-in
 * over the legacy implementation: same `label`, `icon`, `items`,
 * `collapsed`, `sidebarCollapsed`, `currentPath` props, same
 * `@toggle`/`@navigate` emits.
 *
 * Behaviour:
 *   - `sidebarCollapsed=true` → collapsed mode: shows a single icon button
 *     with a popup menu listing items.
 *   - `sidebarCollapsed=false` → expanded: section header + nav items via
 *     default slot. The header toggles `collapsed` via `@toggle`.
 */

import { computed } from 'vue'
import { DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger } from 'reka-ui'
import KmBtn from './KmBtn.vue'
import KmSeparator from './KmSeparator.vue'
import KmGlyph from './KmGlyph.vue'

interface NavItem {
  label: string
  icon?: string
  path: string
  alternativePaths?: string[]
}

const props = withDefaults(
  defineProps<{
    label: string
    icon?: string
    items?: NavItem[]
    collapsed?: boolean
    sidebarCollapsed?: boolean
    /**
     * Currently active route — full path (e.g. `/deep-research/runs/123`).
     * An item matches when this path equals `/<item.path>` or starts with
     * `/<item.path>/`, so multi-segment slugs highlight on detail routes too.
     */
    parentRoute?: string
  }>(),
  {
    icon: 'folder',
    items: () => [],
    collapsed: false,
    sidebarCollapsed: false,
    parentRoute: '',
  },
)

defineEmits<{
  toggle: []
  navigate: [path: string]
}>()

function pathMatches(currentPath: string, candidate: string): boolean {
  if (!currentPath || !candidate) return false
  const target = `/${candidate}`
  return currentPath === target || currentPath.startsWith(`${target}/`)
}

function isItemActive(item: NavItem) {
  if (!props.parentRoute) return false
  if (pathMatches(props.parentRoute, item.path)) return true
  return item.alternativePaths?.some((p) => pathMatches(props.parentRoute, p)) ?? false
}

const hasActiveItem = computed(() => props.items.some(isItemActive))
</script>

<template>
  <DropdownMenuRoot v-if="sidebarCollapsed">
    <DropdownMenuTrigger as-child>
      <span class="km-nav-section--collapsed" :data-active="hasActiveItem ? 'true' : undefined">
        <KmBtn
          flat
          :icon="icon"
          :selected="hasActiveItem"
          icon-size="18px"
          :tooltip="label"
          data-test="km-nav-section-collapsed"
        />
      </span>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        class="ds-menu km-nav-section__popup"
        side="right"
        align="start"
        :side-offset="8"
      >
        <header class="km-nav-section__popup-header">{{ label }}</header>
        <DropdownMenuItem
          v-for="(item, index) in items"
          :key="index"
          class="ds-menu__item"
          :data-active="isItemActive(item) ? 'true' : undefined"
          @select="$emit('navigate', item.path)"
        >
          <KmGlyph
            v-if="item.icon"
            :name="item.icon"
            size="14px"
            :tone="isItemActive(item) ? 'brand' : undefined"
          />
          <span>{{ item.label }}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>

  <div
    v-else
    class="km-nav-section stack"
    :class="collapsed ? 'km-nav-section--tight' : 'km-nav-section--loose'"
    data-test="km-nav-section"
  >
    <button
      type="button"
      class="km-nav-section__header cluster"
      data-align="center"
      @click="$emit('toggle')"
    >
      <span class="km-nav-section__title">{{ label }}</span>
      <span class="ms-auto">
        <KmGlyph
          :name="collapsed ? 'chevron-down' : 'chevron-up'"
          size="14px"
        />
      </span>
    </button>
    <KmSeparator v-if="!collapsed" />
    <div v-if="!collapsed" class="km-nav-section__body">
      <slot />
    </div>
  </div>
</template>

<style>
.km-nav-section { inline-size: 100%; }
.km-nav-section--tight { gap: var(--ds-space-2xs); }
.km-nav-section--loose { gap: var(--ds-space-xs); }

.km-nav-section__header {
  background: transparent;
  border: 0;
  padding: 0 var(--ds-space-2xs);
  cursor: pointer;
  inline-size: 100%;
}
.km-nav-section__title {
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-semibold);
  color: var(--ds-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Center the icon button horizontally within the collapsed sidebar column. */
.km-nav-section--collapsed {
  display: flex;
  justify-content: center;
  inline-size: 100%;
}
/* Active section indicator: leading edge accent so the active section is
 * obvious even when the bar is collapsed and only icons are visible. */
.km-nav-section--collapsed[data-active='true'] {
  position: relative;
}
.km-nav-section--collapsed[data-active='true']::before {
  content: '';
  position: absolute;
  inset-block: 4px;
  inset-inline-start: 0;
  inline-size: 3px;
  border-radius: 0 var(--ds-radius-sm) var(--ds-radius-sm) 0;
  background: var(--ds-color-primary);
}

.km-nav-section__popup-header {
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  font-size: var(--ds-font-size-xs);
  text-transform: uppercase;
  color: var(--ds-color-secondary);
}
.ds-menu__item[data-active='true'] {
  color: var(--ds-color-primary);
  background: var(--ds-color-primary-bg);
}
</style>

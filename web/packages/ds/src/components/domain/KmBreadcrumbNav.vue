<script setup lang="ts">
/**
 * KmBreadcrumbNav — domain wrapper around DsBreadcrumb primitives for the
 * recurring "section header crumbs" pattern (49 hand-rolled section headers
 * at the time of extraction). The last item renders as the current page;
 * preceding items are clickable.
 *
 *   <KmBreadcrumbNav :items="[{ label: app.name, to: `/ai-apps/${app.id}` }, { label: tab.name }]" />
 */

import type { RouteLocationRaw } from 'vue-router'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import {
  DsBreadcrumb,
  DsBreadcrumbItem,
  DsBreadcrumbLink,
  DsBreadcrumbList,
  DsBreadcrumbPage,
  DsBreadcrumbSeparator,
} from '../primitives'
import KmGlyph from './KmGlyph.vue'

export interface KmBreadcrumbItem {
  label: string
  to?: RouteLocationRaw
  onClick?: () => void
}

const props = withDefaults(
  defineProps<{
    items: KmBreadcrumbItem[]
    separatorIcon?: string
    separatorSize?: string
  }>(),
  {
    separatorIcon: 'chevron_right',
    separatorSize: '18px',
  },
)

const router = useRouter()

const segments = computed(() =>
  props.items.map((item, index) => ({
    ...item,
    isLast: index === props.items.length - 1,
  })),
)

function handleClick(item: KmBreadcrumbItem, event: MouseEvent) {
  if (item.onClick) {
    event.preventDefault()
    item.onClick()
    return
  }
  if (item.to) {
    event.preventDefault()
    router.push(item.to)
  }
}
</script>

<template>
  <DsBreadcrumb class="km-breadcrumb-nav">
    <DsBreadcrumbList class="km-breadcrumb-nav__list">
      <template v-for="(item, index) in segments" :key="`${index}-${item.label}`">
        <DsBreadcrumbItem class="km-breadcrumb-nav__item">
          <DsBreadcrumbPage v-if="item.isLast" class="km-breadcrumb-nav__current">
            {{ item.label }}
          </DsBreadcrumbPage>
          <DsBreadcrumbLink
            v-else
            class="km-breadcrumb-nav__link"
            :href="typeof item.to === 'string' ? item.to : '#'"
            @click="handleClick(item, $event)"
          >
            {{ item.label }}
          </DsBreadcrumbLink>
        </DsBreadcrumbItem>
        <DsBreadcrumbSeparator v-if="!item.isLast" class="km-breadcrumb-nav__sep">
          <KmGlyph :name="separatorIcon" :size="separatorSize" />
        </DsBreadcrumbSeparator>
      </template>
    </DsBreadcrumbList>
  </DsBreadcrumb>
</template>

<style>
.km-breadcrumb-nav {
  font-family: var(--ds-font-default);
  display: block;
  min-inline-size: 0;
  max-inline-size: 100%;
}
.km-breadcrumb-nav__list {
  flex-wrap: nowrap;
  gap: var(--ds-space-sm);
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-fg);
  min-inline-size: 0;
  max-inline-size: 100%;
}
/* Earlier crumbs: do not shrink, stay readable. */
.km-breadcrumb-nav__item {
  flex: 0 0 auto;
  min-inline-size: 0;
}
/* Last item (current page) absorbs the remaining width and ellipsis-truncates. */
.km-breadcrumb-nav__item:last-child {
  flex: 0 1 auto;
  min-inline-size: 0;
  overflow: hidden;
}
.km-breadcrumb-nav__link {
  color: var(--ds-color-primary);
  cursor: pointer;
  white-space: nowrap;
}
.km-breadcrumb-nav__link:hover {
  color: var(--ds-color-primary-700);
  text-decoration: underline;
}
.km-breadcrumb-nav__current {
  color: var(--ds-color-fg);
  font-weight: var(--ds-font-weight-regular);
  display: inline-block;
  max-inline-size: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.km-breadcrumb-nav__sep {
  color: var(--ds-color-fg-muted);
  flex: 0 0 auto;
}
</style>

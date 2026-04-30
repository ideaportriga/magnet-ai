<template>
  <DsDialog
    v-model:open="open"
    size="lg"
    visually-hidden-title
    hide-close
    class="global-search"
  >
    <template #title>{{ m.search_searchNavigation() }}</template>
    <div class="global-search__shell">
      <div class="global-search__input-row">
        <km-glyph name="search" size="20px" tone="subtle" />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          class="global-search__input"
          :placeholder="m.search_searchNavigation()"
          autofocus
          @keydown.down.prevent="moveDown"
          @keydown.up.prevent="moveUp"
          @keydown.enter.prevent="selectCurrent"
          @keydown.esc.prevent="open = false"
        >
      </div>

      <div class="global-search__list" role="listbox" :aria-label="m.search_searchNavigation()">
        <template v-if="loading">
          <div class="cluster p-xl" data-justify="center">
            <km-loader size="32px" />
          </div>
        </template>
        <template v-else-if="displayedItems.length === 0">
          <div class="stack global-search__empty" data-gap="sm" data-align="center">
            <km-glyph name="search" size="36px" />
            <div class="km-description text-secondary-text">
              {{ query ? m.search_noResultsFound() : m.search_startTyping() }}
            </div>
          </div>
        </template>
        <template v-else>
          <div v-if="!query" class="global-search__section-label">Recent</div>
          <button
            v-for="(item, index) in displayedItems"
            :key="`${item.entity_type}:${item.id}`"
            :ref="(el) => { if (index === activeIndex) activeEl = el as HTMLElement | null }"
            type="button"
            role="option"
            :aria-selected="index === activeIndex"
            class="global-search__item"
            :class="{ 'global-search__item--active': index === activeIndex }"
            @click="navigateTo(item)"
            @mouseenter="activeIndex = index"
          >
            <span class="global-search__icon">
              <km-glyph :name="entityIcon(item.entity_type)" size="16px" />
            </span>
            <span class="global-search__body">
              <span class="global-search__name">{{ item.name }}</span>
              <span v-if="item.description" class="global-search__desc">{{ item.description }}</span>
            </span>
            <span class="global-search__sysname">{{ item.system_name }}</span>
          </button>
        </template>
      </div>

      <div class="global-search__footer cluster" data-gap="lg">
        <span class="cluster" data-gap="2xs" data-align="center">
          <DsKbd>↵</DsKbd>
          <span class="km-description text-secondary-text">{{ m.search_select() }}</span>
        </span>
        <span class="cluster" data-gap="2xs" data-align="center">
          <DsKbd>↑</DsKbd>
          <DsKbd>↓</DsKbd>
          <span class="km-description text-secondary-text">{{ m.search_navigate() }}</span>
        </span>
        <span class="cluster" data-gap="2xs" data-align="center">
          <DsKbd>ESC</DsKbd>
          <span class="km-description text-secondary-text">{{ m.common_close() }}</span>
        </span>
      </div>
    </div>
  </DsDialog>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useCatalog, filterCatalog, type CatalogItem } from '@/queries/catalog'
import { useGlobalSearchRecents } from '@/composables/useGlobalSearchRecents'
import { DsDialog, DsKbd } from '@ds/primitives'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const MAX_VISIBLE = 10

const router = useRouter()
const { data: catalogData, isLoading: loading } = useCatalog()
const { recents, record } = useGlobalSearchRecents()

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)
const activeEl = ref<HTMLElement | null>(null)

const entityIconMap: Record<string, string> = {
  agents: 'robot',
  promptTemplates: 'chat',
  rag_tools: 'file-question',
  retrieval: 'file-question',
  ai_apps: 'magic',
  api_servers: 'swap',
  mcp_servers: 'server',
  collections: 'book',
  provider: 'graph',
  model: 'graph',
  evaluation_sets: 'table-list',
  assistant_tools: 'wrench',
  knowledge_graph: 'o_hub',
}

const entityRouteMap: Record<string, string> = {
  provider: '/model-providers',
  model: '/model',
  agents: '/agents',
  ai_apps: '/ai-apps',
  promptTemplates: '/prompt-templates',
  rag_tools: '/rag-tools',
  retrieval: '/retrieval',
  collections: '/knowledge-sources',
  evaluation_sets: '/evaluation-sets',
  assistant_tools: '/assistant-tools',
  api_servers: '/api-servers',
  mcp_servers: '/mcp',
  knowledge_graph: '/knowledge-graph',
}

function entityIcon(type: string): string {
  return entityIconMap[type] || 'file'
}

const allItems = computed<CatalogItem[]>(() => {
  if (!catalogData.value) return []
  return catalogData.value
})

const displayedItems = computed<CatalogItem[]>(() => {
  // No query → resolve recents against the live catalog so renames /
  // deletions don't show stale text. Cap to 10.
  if (!query.value.trim()) {
    if (!allItems.value.length || !recents.value.length) return []
    const byKey = new Map<string, CatalogItem>()
    for (const it of allItems.value) byKey.set(`${it.entity_type}:${it.id}`, it)
    const resolved: CatalogItem[] = []
    for (const r of recents.value) {
      const it = byKey.get(`${r.entity_type}:${r.id}`)
      if (it) resolved.push(it)
      if (resolved.length >= MAX_VISIBLE) break
    }
    return resolved
  }
  // With query → fuzzy match the full catalog (`filterCatalog` already
  // sorts by relevance), then cap to 10 visible rows.
  return filterCatalog(allItems.value, query.value).slice(0, MAX_VISIBLE)
})

function moveDown() {
  if (activeIndex.value < displayedItems.value.length - 1) {
    activeIndex.value++
    nextTick(() => activeEl.value?.scrollIntoView?.({ block: 'nearest' }))
  }
}

function moveUp() {
  if (activeIndex.value > 0) {
    activeIndex.value--
    nextTick(() => activeEl.value?.scrollIntoView?.({ block: 'nearest' }))
  }
}

function selectCurrent() {
  const item = displayedItems.value[activeIndex.value]
  if (item) navigateTo(item)
}

function navigateTo(item: CatalogItem) {
  const base = entityRouteMap[item.entity_type]
  if (!base) return
  record({ id: item.id, entity_type: item.entity_type })
  router.push(`${base}/${item.id}`)
  open.value = false
}

// Reset state every time the popup re-opens; focus the input.
watch(
  () => props.modelValue,
  (next) => {
    if (next) {
      query.value = ''
      activeIndex.value = 0
      nextTick(() => inputRef.value?.focus())
    }
  },
)

// Reset highlight whenever the visible list changes (new query, new recents).
watch(displayedItems, () => {
  activeIndex.value = 0
})
</script>

<style>
/* Dialog chrome — anchor near top of viewport so cmd+K lands in eye-line. */
.global-search.ds-dialog {
  padding: 0;
  gap: 0;
  inline-size: min(640px, calc(100vi - 2 * var(--ds-space-lg)));
  max-block-size: 540px;
  inset-block-start: 12vb;
  transform: translate(-50%, 0);
}
.global-search .ds-dialog__body {
  padding: 0;
}

.global-search__shell {
  display: flex;
  flex-direction: column;
  block-size: 100%;
  background: var(--ds-color-panel-main-bg);
  border-radius: var(--ds-dialog-radius);
  overflow: hidden;
}

/* 56px input row, large font, border-bottom acts as the divider so we
 * don't need a separate <km-separator>. */
.global-search__input-row {
  display: flex;
  align-items: center;
  gap: var(--ds-space-md);
  padding-inline: var(--ds-space-lg);
  block-size: 56px;
  flex: none;
  border-block-end: 1px solid var(--ds-color-border);
}
.global-search__input {
  flex: 1 1 auto;
  min-inline-size: 0;
  background: transparent;
  border: 0;
  outline: none;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-body-lg);
  color: var(--ds-color-black);
}
.global-search__input::placeholder {
  color: var(--ds-color-placeholder);
}

.global-search__list {
  flex: 1 1 auto;
  min-block-size: 0;
  overflow-block: auto;
  padding: var(--ds-space-2xs);
}

.global-search__section-label {
  padding: var(--ds-space-xs) var(--ds-space-md) var(--ds-space-2xs);
  font-size: var(--ds-font-size-xs);
  font-weight: var(--ds-font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ds-color-secondary);
}

.global-search__empty {
  padding-block: var(--ds-space-2xl);
  justify-content: center;
}

/* Each row is a card-like grid: leading icon chip, name+desc stack (~60%
 * of remaining width), trailing system_name (~40%). Both text columns use
 * `min-inline-size: 0` so the inner ellipsis rules can actually clip
 * (without it, grid auto-min-content would expand the column to fit the
 * longest unbroken word and prevent truncation). Whole row is one button
 * (single tab stop). */
.global-search__item {
  display: grid;
  grid-template-columns: auto minmax(0, 3fr) minmax(0, 2fr);
  gap: var(--ds-space-md);
  align-items: center;
  inline-size: 100%;
  padding: var(--ds-space-sm) var(--ds-space-md);
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  cursor: pointer;
  text-align: start;
  font: inherit;
  color: inherit;
}
.global-search__item--active {
  background: var(--ds-color-primary-bg);
}
.global-search__item--active .global-search__icon {
  background: var(--ds-color-primary-light);
  color: var(--ds-color-primary);
}
.global-search__item--active .global-search__name {
  color: var(--ds-color-primary);
}

.global-search__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  border-radius: var(--ds-radius-sm);
  background: var(--ds-color-light);
  color: var(--ds-color-secondary-text);
  flex: none;
  transition:
    background var(--ds-duration-fast) var(--ds-ease-out),
    color var(--ds-duration-fast) var(--ds-ease-out);
}

.global-search__body {
  display: flex;
  flex-direction: column;
  min-inline-size: 0;
  gap: 2px;
}
.global-search__name {
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-black);
  line-height: var(--ds-line-height-tight);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.global-search__desc {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  line-height: var(--ds-line-height-tight);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.global-search__sysname {
  font-family: var(--ds-font-mono);
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-text-grey);
  opacity: 0.7;
  text-align: end;
  min-inline-size: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-search__footer {
  flex-shrink: 0;
  border-block-start: 1px solid var(--ds-color-border);
  padding: var(--ds-space-sm) var(--ds-space-lg);
}
</style>

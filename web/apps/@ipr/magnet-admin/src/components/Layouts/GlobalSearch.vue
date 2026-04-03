<template lang="pug">
q-dialog(:modelValue='modelValue', @update:modelValue='emit("update:modelValue", $event)', position='top', transition-show='slide-down', transition-hide='slide-up')
  q-card.global-search-card
    //- Search input
    .row.items-center.q-px-lg.q-py-md.no-wrap
      q-icon(name='search', size='22px', color='secondary-text')
      input.global-search-input.col.q-ml-md(
        ref='inputRef',
        v-model='query',
        :placeholder='m.search_searchNavigation()',
        @keydown.down.prevent='moveDown',
        @keydown.up.prevent='moveUp',
        @keydown.enter.prevent='selectCurrent',
        @keydown.esc.prevent='close'
      )
      q-icon.cursor-pointer(name='close', size='20px', color='secondary-text', @click='close')

    q-separator

    //- Results
    .global-search-results
      template(v-if='loading')
        .row.justify-center.q-pa-xl
          q-spinner(size='32px', color='primary')

      template(v-else-if='flatResults.length === 0')
        .column.items-center.justify-center.q-pa-xl(style='min-height: 200px')
          q-icon(name='search', size='48px', color='grey-4')
          .text-secondary-text.km-description.q-mt-md {{ query ? m.search_noResultsFound() : m.search_startTyping() }}

      template(v-else)
        .global-search-list.q-pa-sm
          template(v-for='(item, index) in flatResults', :key='item.id')
            .global-search-card-item(
              :class='{ "global-search-card-item--active": index === activeIndex }',
              @click='navigateTo(item)',
              @mouseenter='activeIndex = index',
              :ref='(el) => { if (index === activeIndex) activeEl = el }'
            )
              .row.no-wrap.items-start.full-width
                //- Icon
                .global-search-card-icon
                  q-icon(:name='entityIcon(item.entity_type)', size='18px')
                //- Content
                .col.q-ml-sm(style='min-width: 0')
                  .global-search-card-name.ellipsis {{ item.name }}
                  .global-search-card-desc.ellipsis(v-if='item.description') {{ item.description }}
                //- System name
                .global-search-card-sysname.q-ml-md.ellipsis {{ item.system_name }}

    q-separator

    //- Footer hints
    .row.items-center.q-px-lg.q-py-sm.q-gap-lg
      .row.items-center.q-gap-xs
        .global-search-kbd ↵
        .km-description.text-secondary-text {{ m.search_select() }}
      .row.items-center.q-gap-xs
        .global-search-kbd ↑
        .global-search-kbd ↓
        .km-description.text-secondary-text {{ m.search_navigate() }}
      .row.items-center.q-gap-xs
        .global-search-kbd ESC
        .km-description.text-secondary-text {{ m.common_close() }}
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useCatalog, filterCatalog, type CatalogItem } from '@/queries/catalog'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const router = useRouter()
const { data: catalogData, isLoading: loading } = useCatalog()

const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)
const activeEl = ref<HTMLElement | null>(null)

const entityIconMap: Record<string, string> = {
  agents: 'fa fa-robot',
  promptTemplates: 'fa fa-comment-dots',
  rag_tools: 'fas fa-file-circle-question',
  retrieval: 'fas fa-file-circle-question',
  ai_apps: 'fas fa-wand-magic-sparkles',
  api_servers: 'fas fa-arrow-right-arrow-left',
  mcp_servers: 'fas fa-server',
  collections: 'fas fa-book',
  provider: 'fas fa-circle-nodes',
  model: 'fas fa-circle-nodes',
  evaluation_sets: 'fas fa-table-list',
  assistant_tools: 'fas fa-wrench',
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
  return entityIconMap[type] || 'fas fa-file'
}

const flatResults = computed(() => {
  if (!catalogData.value) return []
  return filterCatalog(catalogData.value, query.value)
})

function moveDown() {
  if (activeIndex.value < flatResults.value.length - 1) {
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
  const item = flatResults.value[activeIndex.value]
  if (item) navigateTo(item)
}

function navigateTo(item: CatalogItem) {
  const base = entityRouteMap[item.entity_type]
  if (base) {
    router.push(`${base}/${item.id}`)
    close()
  }
}

function close() {
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      query.value = ''
      activeIndex.value = 0
      nextTick(() => inputRef.value?.focus())
    }
  },
)

watch(query, () => {
  activeIndex.value = 0
})
</script>

<style lang="stylus" scoped>
.global-search-card
  width 680px
  max-width 90vw
  max-height 520px
  display flex
  flex-direction column
  border-radius 12px !important
  margin-top 80px

.global-search-input
  border none
  outline none
  background transparent
  font-size 16px
  line-height 24px
  width 100%
  color var(--q-primary-text)
  &::placeholder
    color var(--q-secondary-text)

.global-search-results
  flex 1
  overflow-y auto
  min-height 200px
  max-height 380px

.global-search-list
  display flex
  flex-direction column
  gap 2px

.global-search-card-item
  display flex
  align-items center
  padding 10px 14px
  border-radius 8px
  cursor pointer
  transition all 0.12s ease
  &:hover, &--active
    background var(--q-primary-bg, rgba(80, 47, 153, 0.07))
    .global-search-card-icon
      color var(--q-primary)
      background var(--q-primary-light, #E5E3F2)

.global-search-card-icon
  display flex
  align-items center
  justify-content center
  width 34px
  height 34px
  min-width 34px
  border-radius 8px
  background var(--q-background, #f5f5f5)
  color var(--q-secondary-text)
  transition all 0.12s ease

.global-search-card-name
  font-size 13px
  font-weight 500
  color var(--q-primary-text)
  line-height 1.3

.global-search-card-type
  flex-shrink 0
  font-size 10px !important
  background var(--q-primary-light, #E5E3F2) !important
  color var(--q-primary) !important
  padding 0 6px
  height 18px
  min-height 18px

.global-search-card-desc
  font-size 12px
  color var(--q-secondary-text)
  margin-top 2px
  line-height 1.3

.global-search-card-sysname
  max-width 30%
  font-size 11px
  font-family monospace
  color var(--q-secondary-text)
  opacity 0.7
  align-self center
  text-align right

.global-search-kbd
  display inline-flex
  align-items center
  justify-content center
  min-width 22px
  height 20px
  padding 0 5px
  border-radius 4px
  border 1px solid rgba(0, 0, 0, 0.15)
  font-size 11px
  color var(--q-secondary-text)
  background var(--q-background, #fafafa)
</style>

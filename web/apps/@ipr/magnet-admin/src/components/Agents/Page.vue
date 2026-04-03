<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(placeholder='Search', iconBefore='search', :modelValue='searchString', @input='searchString = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(label='New', @click='showNewDialog = true')
      .col.overflow-auto(style='min-height: 0')
        template(v-if='isLoading && !visibleRows.length')
          .flex.flex-center.full-height
            q-spinner(size='40px', color='primary')
        template(v-else-if='visibleRows.length')
          .row
            .q-pa-md.col-xs-12.col-sm-6.col-md-6.col-lg-6(v-for='row in visibleRows', :key='row.id', @click='openDetails(row)')
              q-card.card-hover(bordered, flat, style='min-width: 400px')
                q-card-section.q-pa-lg
                  .row
                    .col-auto
                      .km-heading-4 {{ row.name }}
                      .km-label {{ row.description }}
                    .col-auto.q-ml-auto
                      q-chip.km-button-text(text-color='primary', color='primary-light')
                        q-icon.q-mr-xs(name='fas fa-wand-magic-sparkles')
                        div {{ row?.variants?.find((v) => v?.variant == row?.active_variant)?.value?.topics?.length || 0 }} Topics
                  .row.q-mt-sm
                    km-chip-copy(:label='row?.system_name')
                q-separator
                .row.justify-between
                  q-item.q-pa-lg
                    q-item-section
                      q-item-label Created
                      q-item-label(caption) {{ formatDate(row.created_at) }}
                  q-item.q-pa-lg
                    q-item-section
                      q-item-label Updated
                      q-item-label(caption) {{ formatDate(row.updated_at) }}
        template(v-else)
          .flex.flex-center.full-height
            .km-description.text-grey-6 No agents found
      .row.items-center.q-px-md.q-py-sm.text-grey(style='flex-shrink: 0; border-top: 1px solid rgba(0,0,0,0.12)')
        .km-description {{ visibleRows.length }} records

    agents-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@shared/utils'
import { useEntityQueries } from '@/queries/entities'
import type { Agent } from '@/types'

const router = useRouter()
const queries = useEntityQueries()
const showNewDialog = ref(false)
const searchString = ref('')
const debouncedSearch = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchString, (val) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { debouncedSearch.value = val }, 300)
})

const queryParams = computed(() => {
  const params: Record<string, unknown> = {
    orderBy: 'updated_at',
    sortOrder: 'desc',
    currentPage: 1,
    pageSize: 50,
  }
  if (debouncedSearch.value) params.search = debouncedSearch.value
  return params
})

const { data, isLoading } = queries.agents.useList(queryParams)

const visibleRows = computed<Agent[]>(() => (data.value?.items ?? []) as Agent[])

const formatDate = (val?: string) => (val ? formatDateTime(val) : '-')

const openDetails = async (row: Agent) => {
  await router.push(`/agents/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;

.card-hover:hover
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
</style>

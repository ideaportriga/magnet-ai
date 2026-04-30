<template>
  <div class="stack full-height" data-gap="0">
    <div class="collection-container mx-auto full-width stack full-height px-md pt-lg" data-gap="0">
      <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
        <div class="cluster mb-md" data-justify="between">
          <div class="flex-none center-flex-y">
            <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
          </div>
          <div class="km-space" />
          <div class="flex-none center-flex-y">
            <km-btn class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
          </div>
        </div>
        <div class="flex-1 overflow-auto relative-position" style="min-block-size: 0">
          <km-inner-loading :showing="isLoading && rows.length === 0" />
          <template v-if="rows.length">
            <div class="agents-grid">
              <button
                v-for="row in rows"
                :key="row.original.id"
                type="button"
                class="agent-card"
                data-test="table-row"
                @click="openDetails(row.original)"
              >
                <div class="agent-card__header">
                  <div class="agent-card__title-block">
                    <div class="km-heading-3 agent-card__title">{{ row.original.name }}</div>
                    <div v-if="row.original.description" class="km-description text-secondary-text agent-card__desc">
                      {{ row.original.description }}
                    </div>
                  </div>
                  <km-chip
                    tone="brand"
                    class="agent-card__topics"
                    icon="magic"
                    icon-size="14px"
                    icon-margin-right="6px"
                    :label="`${topicCount(row.original)} ${m.agents_topics()}`"
                  />
                </div>

                <div class="agent-card__sysname" @click.stop>
                  <km-chip-copy :label="row.original.system_name" />
                </div>

                <km-separator class="my-0" />

                <div class="agent-card__footer cluster" data-gap="lg">
                  <span class="agent-card__meta">
                    <span class="agent-card__meta-label">{{ m.common_created() }}</span>
                    <span class="agent-card__meta-value">{{ formatDate(row.original.created_at) }}</span>
                  </span>
                  <span class="agent-card__meta">
                    <span class="agent-card__meta-label">{{ m.common_updated() }}</span>
                    <span class="agent-card__meta-value">{{ formatDate(row.original.updated_at) }}</span>
                  </span>
                </div>
              </button>
            </div>
          </template>
          <template v-else-if="!isLoading">
            <div class="flex flex-center full-height">
              <div class="km-description text-grey-6">{{ m.agents_noAgentsFound() }}</div>
            </div>
          </template>
        </div>
        <km-separator />
        <div class="cluster px-md py-sm text-grey" style="flex-shrink: 0">
          <div class="km-description">{{ totalRows }} {{ m.common_records() }}</div>
        </div>
      </div>
      <agents-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@shared/utils'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { Agent } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

// `useDataTable` owns the search-debounce + sort + pagination params and
// returns a TanStack `table` instance plus the live row models. We don't
// render columns visually (the page is a card grid), but the column
// definitions still drive server-side search and sort.
const columns = [
  textColumn<Agent>('name', m.common_name()),
  textColumn<Agent>('system_name', m.common_systemName()),
  dateColumn<Agent>('created_at', m.common_created()),
  dateColumn<Agent>('updated_at', m.common_lastUpdated()),
]

const { table, totalRows, isLoading, globalFilter } = useDataTable<Agent>('agents', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  defaultPageSize: 50,
})

const rows = computed(() => table.getRowModel().rows)

function topicCount(agent: Agent): number {
  const active = agent?.variants?.find?.((v: { variant?: string }) => v?.variant === agent?.active_variant)
  return (active as { value?: { topics?: unknown[] } } | undefined)?.value?.topics?.length ?? 0
}

function formatDate(val?: string | null): string {
  return val ? formatDateTime(val) : '-'
}

function openDetails(agent: Agent) {
  router.push(`/agents/${agent.id}`)
}
</script>


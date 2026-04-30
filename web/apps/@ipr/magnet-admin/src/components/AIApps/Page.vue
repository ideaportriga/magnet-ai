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
                :key="row.original.id ?? row.original.system_name"
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
                    :label="`${tabCount(row.original)} AI Tabs`"
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
            <div class="cluster p-lg text-grey" data-justify="center">
              <div class="km-description">{{ m.common_noResults() }}</div>
            </div>
          </template>
        </div>
        <km-separator />
        <div class="cluster px-md py-sm text-grey" style="flex-shrink: 0">
          <div class="km-description">{{ totalRows }} {{ m.common_records() }}</div>
        </div>
      </div>
      <ai-apps-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatDateTime } from '@shared/utils'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn } from '@/utils/columnHelpers'
import { beforeRouteEnter } from '@/guards'
import { m } from '@/paraglide/messages'
import type { AiApp } from '@/types'

defineOptions({ beforeRouteEnter })

const router = useRouter()
const showNewDialog = ref(false)

// Same card-grid pattern as Agents: TanStack-backed, columns drive server
// search/sort, rendering is custom card-grid via CSS Grid auto-fill.
const columns = [
  textColumn<AiApp>('name', m.common_name()),
  textColumn<AiApp>('system_name', m.common_systemName()),
  dateColumn<AiApp>('created_at', m.common_created()),
  dateColumn<AiApp>('updated_at', m.common_lastUpdated()),
]

const { table, totalRows, isLoading, globalFilter } = useDataTable<AiApp>('ai_apps', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  defaultPageSize: 50,
})

const rows = computed(() => table.getRowModel().rows)

function tabCount(app: AiApp): number {
  return (app as { tabs?: unknown[] })?.tabs?.length ?? 0
}

function formatDate(val?: string | null): string {
  return val ? formatDateTime(val) : '-'
}

function openDetails(app: AiApp) {
  router.push(`/ai-apps/${app.id}`)
}
</script>

<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(data-test='search-input', :placeholder='m.common_search()', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(data-test='new-btn', :label='m.common_new()', @click='openNewDetails')
      //-
        §E.3.2 — was a q-table with grid=true rendering cards via the
        item slot. q-table wasn't doing anything table-ish (no sort, no
        pagination), so migrated to a plain v-for over the rows. Search
        still drives the server-side useList(queryParams).
      .col.overflow-auto.relative-position(style='min-height: 0')
        km-inner-loading(:showing='loading')
        .row.q-col-gutter-md(v-if='(visibleRows ?? []).length > 0')
          .col-xs-12.col-sm-6.col-md-6.col-lg-6(
            data-test='table-row',
            v-for='row in visibleRows',
            :key='row.id ?? row.system_name'
          )
            q-card.card-hover.cursor-pointer(bordered, flat, style='min-width: 400px', @click='openDetails(row)')
              q-card-section.q-pa-lg
                .row
                  .col-auto
                    .km-heading-4 {{ row.name }}
                    .km-label {{ row.description }}
                  .col-auto.q-ml-auto
                    q-chip.km-button-text(text-color='primary', color='primary-light')
                      q-icon.q-mr-xs(name='fas fa-wand-magic-sparkles')
                      div {{ row?.tabs?.length || 0 }} AI Tabs
                .row.q-mt-sm
                  km-chip-copy(:label='row.system_name')
              q-separator
              .row.justify-between
                .col-auto(v-for='col in detailColumns', :key='col.name')
                  q-item.q-pa-lg
                    q-item-section
                      q-item-label {{ col.label }}
                      q-item-label(caption) {{ cellValue(col, row) }}
        .row.q-pa-lg.text-grey.justify-center.items-center(v-else-if='!loading')
          .km-description {{ m.common_noResults() }}
      .row.items-center.q-px-md.q-py-sm.text-grey(style='flex-shrink: 0; border-top: 1px solid rgba(0,0,0,0.12)')
        .km-description {{ (visibleRows ?? []).length }} records

    ai-apps-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
</template>

<script>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { beforeRouteEnter } from '@/guards'
import aiAppsControls from '@/config/ai_apps/ai_apps'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  beforeRouteEnter,
  setup() {
    const queries = useEntityQueries()
    const { draft: ragDraft } = useVariantEntityDetail('rag_tools')
    const { mutateAsync: createAiApp } = queries.ai_apps.useCreate()
    const { options: collectionsOptions } = useCatalogOptions('collections')

    const searchString = ref('')
    const debouncedSearch = ref('')
    // §B.5 — debounce + teardown on unmount.
    let searchTimer = null
    watch(searchString, (val) => {
      if (searchTimer) clearTimeout(searchTimer)
      searchTimer = setTimeout(() => { debouncedSearch.value = val }, 300)
    })
    onBeforeUnmount(() => {
      if (searchTimer) { clearTimeout(searchTimer); searchTimer = null }
    })

    const queryParams = computed(() => {
      const params = { orderBy: 'updated_at', sortOrder: 'desc', currentPage: 1, pageSize: 50 }
      if (debouncedSearch.value) params.search = debouncedSearch.value
      return params
    })

    const { data: aiAppsListData, isLoading } = queries.ai_apps.useList(queryParams)

    const selectedRow = ref(null)
    const pagination = ref({ page: 1, rowsPerPage: 0 })
    const columns = computed(() => Object.values(aiAppsControls).sort((a, b) => (a.columnNumber || 0) - (b.columnNumber || 0)))
    const visibleColumns = computed(() => columns.value.filter((c) => c.display).map((c) => c.name))
    const visibleRows = computed(() => aiAppsListData.value?.items ?? [])

    // §E.3.2 — column subset that appears in the card body (everything that
    // isn't the headline name/description). Hoisted out of the template so
    // the array identity is stable across row renders (C.4 pattern).
    const hiddenDetailCols = new Set(['desc', 'nameDescription', 'name', 'description', 'system_name', 'id', 'soureces'])
    const detailColumns = computed(() =>
      columns.value.filter((c) => c.display && !hiddenDetailCols.has(c.name)),
    )

    // Resolve a column's displayed value for a given row. Mirrors q-table's
    // internal field/format handling so we can drop q-table entirely.
    function cellValue(col, row) {
      const raw = typeof col.field === 'function' ? col.field(row) : row?.[col.field]
      if (raw === undefined || raw === null || raw === '') return '-'
      return typeof col.format === 'function' ? col.format(raw, row) : raw
    }

    return {
      ragDraft,
      aiAppsListData,
      loading: isLoading,
      searchString,
      selected: ref([]),
      pagination,
      visibleColumns,
      columns,
      detailColumns,
      cellValue,
      visibleRows,
      selectedRow,
      createAiApp,
      createNew: ref(false),
      loadingRefresh: ref(false),
      collectionsOptions,
      newRow: ref({
        retrieve: {
          similarity_score_threshold: 0.75,
          max_chunks_retrieved: 5,
          chunk_context_window_expansion_size: 1,
          collection_system_names: [],
        },
        generate: {
          prompt_template: 'QA_SYSTEM_PROMPT_TEMPLATE',
        },
        language: {
          detect_question_language: {
            enabled: false,
            prompt_template: 'M_DETECT_LANGUAGE',
          },
          multilanguage: {
            enabled: false,
            source_language: 'English',
            prompt_template_translation: 'M_TRANSLATE_TEXT',
          },
        },
        name: '',
        description: '',
        system_name: '',
      }),
      showNewDialog: ref(false),
      m,
    }
  },
  computed: {
    items() {
      return this.aiAppsListData?.items ?? []
    },
    collections() {
      return (this.collectionsOptions ?? []).map((item) => ({
        ...item,
        value: item.id,
        label: item.name,
      }))
    },
    currentRag() {
      return this.ragDraft
    },
    collectionSystemNames: {
      get() {
        return (this.collections || []).filter((el) => (this.newRow?.retrieve?.collection_system_names || []).includes(el?.id))
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.id
          }
        })
        this.newRow.retrieve.collection_system_names = value
      },
    },
  },
  watch: {
    newRow: {
      deep: true,
      immediate: true,
      handler(val, oldVal) {
        if (val?.name !== oldVal?.name) {
          this.newRow.system_name = val?.name
        }
      },
    },
  },
  mounted() {
    this.searchString = ''
  },
  methods: {
    async openNewDetails() {
      this.showNewDialog = true
    },
    validation(rag, showNotify = true) {
      const { name, description, system_name, retrieve } = rag
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        if (showNotify) {
          notify.error(`Name, Description, System name and Knowledge sources are required`)
        }
        return false
      }

      return true
    },

    async openDetails(row) {
      await this.$router.push(`/ai-apps/${row.id}`)
    },

    async refreshTable() {
      this.loadingRefresh = true
      // Data is automatically refreshed via TanStack Query
      this.loadingRefresh = false
    },
  },
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

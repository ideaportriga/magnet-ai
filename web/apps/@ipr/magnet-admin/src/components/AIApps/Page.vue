<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(data-test='new-btn', label='New', @click='openNewDetails')
      .col.overflow-auto(style='min-height: 0')
        q-table.full-width(
          grid,
          flat,
          :loading='loading',
          :selected='selectedRow ? [selectedRow] : []',
          :columns='columns',
          :rows='visibleRows ?? []',
          :visibleColumns='visibleColumns',
          :rows-per-page-options='[0]',
          :pagination='{ rowsPerPage: 0 }',
          ref='table',
          hide-bottom
        )
          template(v-slot:item='props')
            .q-pa-md.col-xs-12.col-sm-6.col-md-6.col-lg-6(@click='openDetails(props.row)')
              q-card.card-hover(bordered, flat, style='min-width: 400px')
                q-card-section.q-pa-lg
                  .row
                    .col-auto
                      .km-heading-4 {{ props.row.name }}
                      .km-label {{ props.row.description }}
                    .col-auto.q-ml-auto
                      q-chip.km-button-text(text-color='primary', color='primary-light')
                        q-icon.q-mr-xs(name='fas fa-wand-magic-sparkles')
                        div {{ props.row?.tabs?.length || 0 }} AI Tabs
                  .row.q-mt-sm
                    km-chip-copy(:label='props.row.system_name')
                q-separator
                .row.justify-between
                  q-item.q-pa-lg(
                    v-for='col in props.cols.filter((col) => col.name !== "desc" && col.name !== "nameDescription")',
                    :key='col.name'
                  )
                    q-item-section
                      q-item-label {{ col.label }}
                      q-item-label(caption) {{ col.value }}
      .row.items-center.q-px-md.q-py-sm.text-grey(style='flex-shrink: 0; border-top: 1px solid rgba(0,0,0,0.12)')
        .km-description {{ (visibleRows ?? []).length }} records

    ai-apps-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { beforeRouteEnter } from '@/guards'
import aiAppsControls from '@/config/ai_apps/ai_apps'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  beforeRouteEnter,
  setup() {
    const queries = useEntityQueries()
    const { draft: ragDraft } = useVariantEntityDetail('rag_tools')
    const { data: aiAppsListData, isLoading } = queries.ai_apps.useList()
    const { mutateAsync: createAiApp } = queries.ai_apps.useCreate()
    const { options: collectionsOptions } = useCatalogOptions('collections')

    const searchString = ref('')
    const selectedRow = ref(null)
    const pagination = ref({ page: 1, rowsPerPage: 0 })
    const columns = computed(() => Object.values(aiAppsControls).sort((a, b) => (a.columnNumber || 0) - (b.columnNumber || 0)))
    const visibleColumns = computed(() => columns.value.filter((c) => c.display).map((c) => c.name))
    const items = computed(() => aiAppsListData.value?.items ?? [])
    const visibleRows = computed(() => {
      const search = (searchString.value || '').toLowerCase()
      if (!search) return items.value
      return items.value.filter((el) =>
        Object.values(el).some((val) => typeof val === 'string' && val.toLowerCase().includes(search))
      )
    })

    return {
      ragDraft,
      aiAppsListData,
      loading: isLoading,
      searchString,
      selected: ref([]),
      pagination,
      visibleColumns,
      columns,
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
        return this.collections.filter((el) => (this.newRow?.retrieve?.collection_system_names || []).includes(el?.id))
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
    goToRow(id) {
      const row = this.items.find((item) => item.id === id)
      if (row) {
        const rows = this.$refs.table.filteredSortedRows
        const index = rows.findIndex((item) => item.id === id)
        const page = Math.floor(index / this.pagination.rowsPerPage) + 1
        this.$refs.table.setPagination({ page })
      }
    },
    async openNewDetails() {
      this.showNewDialog = true
    },
    validation(rag, notify = true) {
      const { name, description, system_name, retrieve } = rag
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        // Handle validation error

        if (notify) {
          this.$q.notify({
            color: 'red-9', textColor: 'white',
            icon: 'error',
            group: 'error',
            message: `Name, Description, System name and Knowledge sources are required`,
            timeout: 1000,
          })
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

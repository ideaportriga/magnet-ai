<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            q-tabs.bb-border.full-width.q-mb-lg(
              v-model='tab',
              narrow-indicator,
              dense,
              align='left',
              active-color='primary',
              indicator-color='primary',
              active-bg-color='white',
              no-caps,
              content-class='km-tabs'
            )
              template(v-for='t in tabs')
                q-tab(:name='t.name', :label='t.label')
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(label='New', @click='openNewDetails')
            .row
              km-table(
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :selected='selectedRow ? [selectedRow] : []',
                :columns='columsByType',
                :rows='visibleRowsByType ?? []',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                :pagination='pagination',
                binary-state-sort,
                ref='table'
              )
    model-config-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', :type='tab', v-if='showNewDialog')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { beforeRouteEnter } from '@/guards'

export default {
  beforeRouteEnter,
  setup() {
    const {
      items,
      controls,
      searchString,
      selected,
      create,
      pagination,
      config,
      visibleColumns,
      columns,
      visibleRows,
      selectedRow,
      ...useCollection
    } = useChroma('model')

    return {
      tab: ref('prompts'),
      tabs: ref([
        { name: 'prompts', label: 'Chat Completion Models' },
        { name: 'embeddings', label: 'Vector Embedding Models' },
        { name: 're-ranking', label: 'Reranking Models' },
      ]),
      items,
      controls,
      searchString,
      selected,
      pagination,
      config,
      visibleColumns,
      columns,
      visibleRows,
      selectedRow,
      useCollection,
      create,
      createNew: ref(false),
      loadingRefresh: ref(false),
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
    columsByType() {
      if (this.tab == 'prompts') {
        return this.columns.filter((item) =>
          ['providerLabel', 'model', 'display_name', 'json_mode', 'json_schema', 'tool_calling', 'reasoning', 'is_default'].includes(item.name)
        )
      }

      if (this.tab == 'embeddings') {
        return this.columns.filter((item) => ['providerLabel', 'model', 'display_name', 'price_embeddings', 'is_default'].includes(item.name))
      }

      if (this.tab == 're-ranking') {
        return this.columns.filter((item) => ['providerLabel', 'model', 'display_name', 'price_rerank', 'is_default'].includes(item.name))
      }
      return this.columns
    },
    visibleRowsByType() {
      return this.visibleRows.filter((item) => item.type === this.tab)
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
    async openDetails(row) {
      await this.$router.push(`/model/${row.id}`)
    },
    async refreshTable() {
      this.loadingRefresh = true
      this.useCollection.get()
      this.loadingRefresh = false
    },
    goToRow(id) {
      const row = this.items.find((item) => item.id === id)
      console.log('row', row)
      if (row) {
        this.tab = row.type
        this.$refs.table.goToRow(id)
      }
    },
  },
}
</script>

<style lang="stylus">
.collection-container {
  min-width: 450px;
  max-width: 1200px;
  width: 100%;
}
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>

<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(label='New', @click='openNewDetails')
            .row
              q-table(
                grid,
                :selected='selectedRow ? [selectedRow] : []',
                :columns='columns',
                :rows='visibleRows ?? []',
                :visibleColumns='visibleColumns',
                style='max-width: 1100px; min-width: 1100px',
                :pagination='pagination'
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
                              div {{ props.row?.variants?.find((variant) => variant?.variant == props.row?.active_variant)?.value?.topics?.length || 0 }} Topics
                        .row.q-mt-sm
                          //- km-chip-copy(:label="props.row.system_name" color="in-progress" text-color="text-gray")
                          km-chip-copy(:label='props.row?.system_name')
                      q-separator
                      .row.justify-between
                        q-item.q-pa-lg(
                          v-for='col in props.cols.filter((col) => col.name !== "desc" && col.name !== "nameDescription")',
                          :key='col.name'
                        )
                          q-item-section
                            q-item-label {{ col.label }}
                            q-item-label(caption) {{ col.value }}

    agents-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
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
    } = useChroma('agents')

    return {
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
    currentRag() {
      return this.$store.getters.rag
    },
  },
  watch: {
    newRow: {
      deep: true,
      immediate: true,
      handler(val, oldVal) {
        console.log(val, oldVal)
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
    async createRag() {
      if (this.validation(this.newRow)) {
        this.createNew = false
        const { inserted_id } = await this.create(JSON.stringify(this.newRow))
        await this.useCollection.selectRecord(inserted_id)
        this.$store.commit('setRag', this.newRow)
        this.$router.push(`/rag-tools/${inserted_id}`)
      }
    },
    validation(rag, notify = true) {
      const { name, description, system_name, retrieve } = rag
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        if (notify) {
          this.$q.notify({
            message: `Name, Description, System name and Knowledge sources are required`,
            color: 'error-text',
            position: 'top',
            timeout: 1000,
          })
        }
        return false
      }

      return true
    },

    async openDetails(row) {
      console.log(row)
      await this.$router.push(`/agents/${row.id}`)
    },

    async refreshTable() {
      this.loadingRefresh = true
      this.useCollection.get()
      this.loadingRefresh = false
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

.card-hover:hover
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
</style>

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
                :columns='columns',
                :rows='visibleRowsByType ?? []',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                :pagination='pagination',
                binary-state-sort,
                ref='table'
              )
    assistant-tools-create-new(:showNewDialog='showNewDialog && tab == "api"', @cancel='showNewDialog = false')
    assistant-tools-create-new-rag(:showNewDialog='showNewDialog && tab == "rag"', @cancel='showNewDialog = false')
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
    } = useChroma('assistant_tools')

    return {
      tab: ref('api'),
      tabs: ref([
        { name: 'api', label: 'API' },
        { name: 'rag', label: 'RAG' },
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
        name: '',
        description: '',
        system_name: '',
      }),
      showNewDialog: ref(false),
    }
  },
  computed: {
    visibleRowsByType() {
      return this.visibleRows.filter((row) => row.type === this.tab)
    },
    currentAssistantTool() {
      return this.$store.getters.retrieval
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
      this.tab = this.selectedRow?.type
      this.$refs.table.goToRow(id)
    },
    async openNewDetails() {
      this.showNewDialog = true
    },
    validation(retrieval, notify = true) {
      const { name, description, system_name, retrieve } = retrieval
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        // Handle validation error

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
      await this.$router.push(`/assistant-tools/${row.id}`)
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
</style>

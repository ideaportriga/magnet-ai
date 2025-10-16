<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-input(data-test="search-input" placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(data-test="new-btn" label='New', @click='openNewDetails')
            .row
              km-table(
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :selected='selectedRow ? [selectedRow] : []',
                :columns='columns',
                :rows='visibleRows ?? []',
                :visibleColumns='visibleColumns',
                style='min-width: 1100px',
                :pagination='pagination',
                binary-state-sort,
                ref='table'
              )
    prompts-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
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
    } = useChroma('promptTemplates')

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
        name: '',
        description: '',
        system_name: '',
      }),
      showNewDialog: ref(false),
    }
  },
  computed: {
    currentRaw() {
      return this.$store.getters.promptTemplate
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
  mounted() {
    this.searchString = ''
  },
  methods: {
    async openNewDetails() {
      this.showNewDialog = true
    },
    validation(row, notify = true) {
      const { name, description, system_name, category } = row

      if (!name || !description || !system_name || !category) {
        // Handle validation error

        if (notify) {
          this.$q.notify({
            message: `Name, Description, System name and Category are required`,
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
      await this.$router.push(`/prompt-templates/${row.id}`)
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

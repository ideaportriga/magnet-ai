<template lang="pug">
div
  template(v-if='true')
    .row.q-mb-12
      .col-auto.center-flex
        km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
      .col
      .col-auto
        km-btn(label='Delete all chunks', :loading='deleteLoading', @click='onDeleteAll')
      .col.q-mx-sm
    .row
      km-table(
        ref='tableRef',
        :loading='loadingItems',
        row-key='id',
        :columns='columns',
        :rows='visibleRows',
        selection='single',
        @selectRow='$emit("selectRow", $event)',
        :selected='selectedRow ? [selectedRow] : []',
        :visibleColumns='visibleColumns',
        @request='getPaginatedLocal',
        v-model:pagination='pagination',
        :filter='filterObject',
        binary-state-sort
      )
  template(v-else-if='loadingItems')
    .column.flex-center
      q-spinner.text-primary(size='40px')
  template(v-else)
    .column.flex-center
      .km-title.q-py-16.text-label Nothing in this knowledge sources yet!
    km-icon(name='empty-collection', width='250', height='250')

  km-popup-confirm(
    :visible='showDeleteConfirm',
    notificationIcon='fas fa-triangle-exclamation',
    confirmButtonLabel='Yes, delete all',
    cancelButtonLabel='Cancel',
    @confirm='confirmDelete',
    @cancel='cancelDelete'
  )
    .row.item-center.justify-center.km-heading-7.q-mb-md Delete Chunks Confirmation
    .row.text-center.justify-center Are you sure you want to delete all embedded chunks?
</template>
<script>
import { useChroma } from '@shared'
import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: ['selectedRow'],
  emits: ['selectRow'],
  setup() {
    const { items, searchString, pagination, visibleColumns, columns, getPaginated, visibleRows, ...useDocuments } = useChroma('documents')
    const { items: collections, selectedRow: selectedCollectionRow, get } = useChroma('collections')
    const loadingItems = ref(false)
    const showDeleteConfirm = ref(false)
    const tableRef = ref()

    return {
      items,
      searchString,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      loadingItems,
      showDeleteConfirm,
      useDocuments,
      collections,
      selectedCollectionRow,
      get,
      getPaginated,
      tableRef,
    }
  },
  computed: {
    deleteLoading() {
      return this.$store.getters?.knowledge?.deleteAllLoading
    },
    filterObject: {
      get() {
        if (this.searchString) {
          return {
            $or: [{ 'metadata.title': { $txt: this.searchString } }, { content: { $txt: this.searchString } }],
          }
        }
        return {}
      },
      set() {},
    },
  },

  mounted() {
    this.requestItems()
  },
  methods: {
    async getPaginatedLocal(input) {
      this.loadingItems = true
      console.log('getPaginatedLocal', input)
      input.collection_id = this.$route.params.id
      await this.getPaginated(input)
      this.loadingItems = false
    },
    async requestItems() {
      this.loadingItems = true

      this.tableRef.requestServerInteraction()
      this.loadingItems = false
    },
    onDeleteAll() {
      this.showDeleteConfirm = true
    },
    async confirmDelete() {
      this.showDeleteConfirm = false
      await this.$store.dispatch('deleteAllDocuments', this.$route.params.id)
      await this.requestItems()
      await this.get()
      // await this.$store.commit('setKnowledge', this.selectedCollectionRow)
    },
    cancelDelete() {
      this.showDeleteConfirm = false
    },
  },
})
</script>

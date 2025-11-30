<template lang="pug">
.column(style='width: 100%; overflow: hidden')
  .row
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable)
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(label='New', @click='showNewDialog = true')
  .row.q-mt-md
    .col-auto.center-flex-y
      km-filter-bar(v-model:config='filterConfig', v-model:filterObject='filterObject', outputFormat='sql')
    q-space
    .col-auto.center-flex-y
      km-btn.q-mr-12(
        v-if='selected.length > 0',
        icon='delete',
        label='Delete',
        @click='showDeleteDialog = true',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='16px',
        hoverBg='primary-bg'
      )
  .row.q-mt-md(style='overflow-x: auto; width: 100%')
    km-table-new(
      @selectRow='openDetails',
      selection='multiple',
      row-key='id',
      :active-record-id='modelConfig?.id',
      v-model:selected='selected',
      :columns='columns',
      :visibleColumns='visibleColumns',
      :rows='filteredRows',
      :pagination='pagination',
      binary-state-sort
    )
model-providers-new-model(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Models
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected models. Are you sure?` }}
</template>

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { categoryOptions, featureOptions } from '../../config/model/model.js'

export default {
  setup() {
    const { searchString, pagination, columns, visibleColumns, visibleRows, selectedRow, delete: deleteItem } = useChroma('model')

    const filterObject = ref({})

    const filterConfig = {
      type: {
        key: 'type',
        label: 'Type',
        multiple: true,
        options: categoryOptions,
      },
      features: {
        key: 'features',
        label: 'Features',
        multiple: true,
        options: featureOptions,
        customLogic: (selected) => ({ $or: selected.map((feature) => ({ [feature]: true })) }),
      },
    }

    return {
      searchString,
      pagination,
      columns,
      visibleColumns,
      visibleRows,
      selectedRow,
      showNewDialog: ref(false),
      selected: ref([]),
      showDeleteDialog: ref(false),
      filterObject,
      filterConfig,
      deleteItem,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    filteredRows() {
      let rows = this.visibleRows.filter((item) => item.provider_system_name === this.provider.system_name)

      // Apply type filter
      if (this.filterObject.typeIn && this.filterObject.typeIn.length > 0) {
        rows = rows.filter((item) => this.filterObject.typeIn.includes(item.type))
      }

      // Apply features filter
      if (this.filterObject.featuresIn && this.filterObject.featuresIn.length > 0) {
        rows = rows.filter((item) => {
          return this.filterObject.featuresIn.some((feature) => item[feature] === true)
        })
      }

      return rows
    },
    modelConfig() {
      return this.$store.getters['modelConfig/entity']
    },
  },
  methods: {
    openDetails(row) {
      this.$store.commit('modelConfig/setEntity', row)
    },
    async deleteSelected() {
      try {
        for (const item of this.selected) {
          await this.deleteItem(item)
        }
        this.selected = []
        this.showDeleteDialog = false
        this.$q.notify({
          position: 'top',
          message: 'Models deleted successfully.',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } catch (error) {
        console.error('Error deleting models:', error)
        this.$q.notify({
          position: 'top',
          message: 'Error deleting models.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      }
    },
  },
}
</script>

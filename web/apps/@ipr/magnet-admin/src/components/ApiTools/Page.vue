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
                km-btn.q-mr-12(label='New', @click='showNewDialog = true')
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
                ref='table'
              )
      api-tools-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>
<script>
import { ref } from 'vue'
import { useStore } from 'vuex'
import { useChroma } from '@shared'
import { beforeRouteEnter } from '@/guards'
export default {
  beforeRouteEnter,
  setup() {
    const searchString = ref('')
    const store = useStore()
    const showNewDialog = ref(false)
    const { columns, selectedRow, visibleRows, visibleColumns, pagination } = useChroma('api_tools')
    return {
      searchString,
      store,
      showNewDialog,
      columns,
      selectedRow,
      visibleRows,
      visibleColumns,
      pagination,
      previousRoute: ref(null),
    }
  },
  methods: {
    openDetails(row) {
      this.$router.push({
        path: `/api-tools/${row.id}`,
      })
    },
  },
}
</script>

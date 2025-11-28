<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                km-filter-bar(v-model:config='filterConfig', v-model:filterObject='filterObject', outputFormat='sql')
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(
                  icon='refresh',
                  label='Refresh list',
                  @click='refreshTable',
                  iconColor='icon',
                  hoverColor='primary',
                  labelClass='km-title',
                  flat,
                  iconSize='16px',
                  hoverBg='primary-bg'
                )
            .row
              km-table(
                ref='tableRef',
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :columns='columns',
                :visibleColumns='visibleColumns',
                :rows='visibleRows',
                style='min-width: 1100px',
                binary-state-sort,
                :loading='loading',
                dense,
                @request='getPaginated',
                v-model:pagination='pagination',
                :filter='filterObject'
              )
        q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'
import _ from 'lodash'
import { traceFilters } from '@/config/observability/traces'

export default {
  setup() {
    const { loading, pagination, visibleColumns, columns, visibleRows, get, getPaginated } = useChroma('observability_traces')
    const tableRef = ref()

    return {
      loading,
      searchString: ref(''),
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      get,
      tableRef,
      getPaginated,
      filterConfig: ref(traceFilters),
      filterObject: ref({}),
    }
  },
  computed: {
    paramId() {
      return this.$route.params.id
    },
  },
  async mounted() {
    this.searchString = this.paramId || ''

    await this.refreshTable()
  },
  methods: {
    debounceSearch: _.debounce(function (search) {
      this.searchString = search
    }, 500),

    async refreshTable() {
      this.tableRef.requestServerInteraction()
    },
    async openDetails(row) {
      await this.$router.push(`/observability-traces/${row.id}`)
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
.km-input:not(.q-field--readonly) .q-field__control::before {
  background: #fff !important;
}
</style>

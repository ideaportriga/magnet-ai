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
                km-btn(data-test='new-btn', label='New', @click='showNewDialog = true')
            .row
              km-table(
                ref='tableJobsRef',
                @selectRow='openDetails',
                selection='single',
                row-key='id',
                :selected='selectedJob ? [selectedJob] : []',
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
  jobs-create-new(:show-new-dialog='showNewDialog', @cancel='showNewDialog = false')
  jobs-drawer(:show-drawer='showDrawer', :job='selectedJob', @cancel='showDrawer = false')
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'
import _ from 'lodash'

export default {
  setup() {
    const { loading, pagination, visibleColumns, columns, visibleRows, get, getPaginated } = useChroma('jobs')
    const tableJobsRef = ref()

    return {
      loading,
      searchString: ref(''),
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      get,
      tableJobsRef,
      getPaginated,
      filterConfig: ref({
        'definition.job_type': {
          label: 'Job type',
          key: 'definition.job_type',
          options: [
            { label: 'One time immmidiate', value: 'one_time_immediate' },
            { label: 'Recurring', value: 'recurring' },
          ],
          default: ['recurring'],
          multiple: true,
        },
        status: {
          label: 'Status',
          key: 'status',
          options: [
            { label: 'Processing', value: 'Processing' },
            { label: 'Error', value: 'Error' },
            { label: 'Waiting', value: 'Waiting' },
            { label: 'Canceled', value: 'Canceled' },
          ],
          multiple: true,
        },
        type: {
          label: 'Type',
          key: 'type',
          options: [
            { label: 'Sync knowledge source', value: 'sync_collection' },
            { label: 'Custom', value: 'custom' },
          ],
        },
        created_at: {
          label: 'Created',
          key: 'created_at',
          type: 'timePeriod',
          default: 'P1D',
        },
        'definition.interval': {
          label: 'Interval',
          key: 'definition.interval',
          options: [
            { label: 'Hourly', value: 'hourly' },
            { label: 'Daily', value: 'daily' },
            { label: 'Weekly', value: 'weekly' },
          ],
          multiple: true,
        },
      }),
      filterObject: ref({}),
      selectedJob: ref(null),
      showDrawer: ref(false),
      showNewDialog: ref(false),
    }
  },
  computed: {},
  beforeMount() {
    if (this.$route.query.job_id) {
      const routeJobId = this.$route.query.job_id
      const newFilterConfig = {}
      // Убираем default у всех существующих полей
      for (let key in this.filterConfig) {
        newFilterConfig[key] = { ...this.filterConfig[key] }
        delete newFilterConfig[key].default
      }
      // Добавляем поле _id со значением из запроса
      newFilterConfig._id = {
        label: 'ID',
        key: '_id',
        options: [{ label: routeJobId, value: routeJobId }],
        default: routeJobId,
      }
      this.filterConfig = newFilterConfig
    }
  },
  async mounted() {
    this.tableJobsRef.requestServerInteraction()
  },
  methods: {
    debounceSearch: _.debounce(function (search) {
      this.searchString = search
    }, 500),

    async refreshTable() {
      this.tableJobsRef.requestServerInteraction()
    },
    async openDetails(row) {
      this.selectedJob = row
      this.showDrawer = true
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

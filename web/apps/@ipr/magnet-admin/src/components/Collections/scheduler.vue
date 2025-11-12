<template lang="pug">
div
  div(v-show='!loading')
    km-section(title='Scheduled job info', subTitle='Job that controls the scheduled sync for this Knowledge Source')
      template(v-if='!job')
        .row.items-center.justify-center
          .col-auto
            .km-heading-3 No job scheduled
        .row.items-center.justify-center
          .col-auto
            .km-label.q-mb-sm Create a job to schedule automatic syncing for this Knowledge Source
        .row.items-center.justify-center
          .col-auto
            km-btn(label='Create new job', @click='showNewDialog = true')
      template(v-else)
        .col.q-pt-8
          .km-input-label.q-pb-xs.q-pl-8 Scheduled job
          km-select(:disabled='true', :modelValue='jobName')
        .row.q-mt-sm
          .col-auto
            km-btn(flat, simple, :label='"Open Job"', iconSize='16px', icon='fas fa-comment-dots', @click='openJob')
    q-separator.q-my-lg
    template(v-if='job')
      km-section(title='Schedule settings and status', subTitle='Go to the Job details to edit settings or cancel scheduled sync.')
        .row.q-col-gutter-md
          .col-4
            .km-field Status
            .km-label {{ jobStatus }}
          .col-4
            .km-field Job interval
            .km-label {{ jobInterval }}
          .col-4
            .km-field Start On
            .km-label {{ startDate }}
        .row.q-col-gutter-md.q-mt-md
          .col-4
            .km-field Repeat at
            .km-label {{ repeatAt }}
          .col-4
            .km-field Last run
            .km-label {{ formattedLastRun }}
          .col-4
            .km-field Next run
            .km-label {{ formattedNextRun }}
    .q-my-lg
    .row
      .col-auto
        .km-heading-4.q-mb-sm Last sync runs
      .col
      .col-auto
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
    km-table(
      ref='tableRef',
      @selectRow='openDetails',
      selection='single',
      row-key='id',
      :columns='Object.values(traceKsControls)',
      :visibleColumns='visibleColumnsCalc',
      :rows='visibleRows',
      style='min-width: 500px',
      binary-state-sort,
      :loading='loadinTraces',
      dense,
      @request='getPaginated',
      v-model:pagination='pagination',
      :filter='filterObject'
    )
q-inner-loading(:showing='loading')
jobs-create-new(:show-new-dialog='showNewDialog', @cancel='showNewDialog = false', @finish='finish', :formDefault='formDefault')
</template>

<script>
import { ref, nextTick } from 'vue'
import { useChroma } from '@shared'
import { DateTime } from 'luxon'
import { formatDateTime } from '@shared/utils/dateTime'
import { traceKsControls } from '@/config/observability/traces'

export default {
  setup() {
    const { update, create } = useChroma('collections')
    const { getDetail } = useChroma('jobs')
    const { pagination, visibleColumns, columns, visibleRows, get, getPaginated, loading: loadinTraces } = useChroma('observability_traces')

    const tableRef = ref()
    return {
      loadinTraces,
      getDetail,
      loading: ref(false),
      formatDateTime,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      get,
      getPaginated,
      tableRef,
      showNewDialog: ref(false),
      update,
      create,
      traceKsControls,
    }
  },
  computed: {
    formDefault() {
      return {
        name: 'Job for Knowledge Source',
        jobType: 'sync_collection',
        executionType: 'recurring',
        system_name: this.currentRow?.system_name || '',
      }
    },
    currentRow() {
      return this.$store.getters.knowledge
    },
    filterObject: {
      get() {
        return { 'system_name_in': this.currentRow?.system_name }
      },
      set() {},
    },
    visibleColumnsCalc() {
      return ['status', 'start_time', 'latency', 'type']
    },
    jobId() {
      return this.$store.getters.knowledge?.job_id
    },
    jobName() {
      return this.job?.definition.name || this.jobId || 'N/A'
    },
    job() {
      return this.$store.getters['chroma/jobs'].items.find((j) => j.id === this.jobId)
    },
    jobStatus() {
      return this.job?.status || 'N/A'
    },
    jobInterval() {
      return this.job?.definition?.interval || 'N/A'
    },
    startDate() {
      if (!this.job?.definition?.scheduled_start_time) return 'N/A'
      return this.formatDateTime(this.job.definition.scheduled_start_time)
    },
    repeatAt() {
      if (!this.job?.definition?.cron) return 'N/A'
      const { hour, minute } = this.job.definition.cron

      if (!hour || !minute) return 'N/A'

      const jobTimezone = this.job?.definition?.timezone || 'UTC'

      const jobTime = DateTime.now()
        .setZone(jobTimezone)
        .set({
          hour: parseInt(hour),
          minute: parseInt(minute),
        })

      const localTime = jobTime.toLocal()

      return `${localTime.toFormat('HH:mm')} (${localTime.toFormat('ZZZZ')})`
    },
    formattedLastRun() {
      if (!this.job?.lastRun) return 'Not run yet'
      return this.formatDateTime(this.job.lastRun)
    },
    formattedNextRun() {
      if (!this.job?.next_run) return 'Not scheduled'
      return this.formatDateTime(this.job.next_run)
    },
  },
  async mounted() {
    this.loading = true
    try {
      if (this.jobId) {
        await this.getDetail({ id: this.jobId })
      }
      // Wait for the next tick to ensure the table is mounted
      await nextTick()
      await this.refreshTable()
    } catch (error) {
      console.error('Error in mounted:', error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    async save() {
      this.loading = true
      try {
        if (this.currentRow?.created) {
          const obj = { ...this.currentRow }
          delete obj._metadata
          delete obj.id
          console.log(obj)
          await this.update({ id: this.currentRow.id, data: obj })
        } else {
          await this.create(JSON.stringify(this.currentRow))
        }
      } catch (error) {
        console.error('Error saving:', error)
      } finally {
        this.loading = false
      }
    },
    setJobId(id) {
      this.$store.commit('updateKnowledge', { job_id: id })
    },
    async finish(job) {
      try {
        this.setJobId(job.job_id)
        await this.save()
        this.showNewDialog = false
        await this.getDetail({ id: this.jobId })
        await this.refreshTable()
      } catch (error) {
        console.error('Error in finish:', error)
      }
    },
    async refreshTable() {
      this.loading = true
      try {
        if (this.tableRef) {
          await this.tableRef.requestServerInteraction()
        } else {
          console.warn('Table reference is not available yet')
        }
      } catch (error) {
        console.error('Error refreshing table:', error)
      } finally {
        this.loading = false
      }
    },
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
    async openDetails(row) {
      await this.$router.push(`/observability-traces/${row.id}`)
    },
    openJob() {
      if (!this.jobId) return
      // Navigate to job details page
      this.$router.push({
        name: 'Jobs',
        query: { job_id: this.jobId },
      })
    },
    createJob() {
      // Logic to create a new job for this Knowledge Source
      this.$router.push({
        name: 'Jobs',
        query: {
          create: true,
          knowledge_source_id: this.$store.getters.knowledge?.id,
        },
      })
    },
  },
}
</script>

<style scoped>
.empty-state {
  min-height: 300px;
  padding: 2rem;
}
</style>

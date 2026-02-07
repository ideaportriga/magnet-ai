<template lang="pug">
.column.full-width
  //- Header: queue name, paused badge, controls
  .row.items-center.q-mb-16
    .row.items-center.q-gap-8
      .km-heading-4 {{ status?.queue || 'Queue' }}
      km-chip.text-capitalize(
        v-if='status',
        :label='status.is_paused ? "Paused" : "Running"',
        :color='status.is_paused ? "warning" : "positive"',
        round
      )
    q-space
    km-btn.q-mr-8(
      icon='refresh',
      label='Refresh',
      @click='fetchStatus',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='14px',
      hoverBg='primary-bg',
      :loading='loading'
    )
    q-toggle(
      v-model='autoRefresh',
      label='Auto-refresh (5s)',
      dense,
      size='sm',
      @update:model-value='toggleAutoRefresh'
    )

  //- Stats cards
  .row.q-gap-12.q-mb-16(v-if='status')
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='hourglass_top', size='16px', color='primary')
          .stat-label Waiting
        .stat-value.text-primary {{ statusCounts.waiting || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='play_circle', size='16px', color='positive')
          .stat-label Active
        .stat-value.text-positive {{ statusCounts.active || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='check_circle', size='16px', color='grey-6')
          .stat-label Completed
        .stat-value.text-grey-7 {{ statusCounts.completed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='error', size='16px', color='negative')
          .stat-label Failed
        .stat-value.text-negative {{ statusCounts.failed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='schedule', size='16px', color='warning')
          .stat-label Delayed
        .stat-value.text-warning {{ statusCounts.delayed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-4
          q-icon(name='memory', size='16px', color='info')
          .stat-label Workers
        .stat-value.text-info {{ workerCount }}

  //- Warning banners
  q-banner.bg-orange-1.text-orange-8.q-mb-12(v-if='status && !workers.length', rounded, dense)
    template(#avatar)
      q-icon(name='warning', color='orange')
    | No active workers detected. Jobs will not be processed.

  q-banner.bg-red-1.text-red-8.q-mb-12(v-if='stalledJobs.length', rounded, dense)
    template(#avatar)
      q-icon(name='report_problem', color='red')
    | {{ stalledJobs.length }} stalled job(s) detected — jobs running without a worker heartbeat for over 60 seconds.

  //- Section tabs
  q-tabs.bb-border.full-width.q-mb-md(
    v-model='section',
    narrow-indicator,
    dense,
    align='left',
    active-color='primary',
    indicator-color='primary',
    no-caps,
    content-class='km-tabs'
  )
    q-tab(name='workers', :label='`Workers (${workerCount})`')
    q-tab(name='repeatables', :label='`Repeatables (${repeatables.length})`')
    q-tab(name='jobs', :label='`Jobs (${allJobs.length})`')

  //- ═══════════════════════════════ WORKERS ═══════════════════════════════
  template(v-if='section === "workers"')
    template(v-if='workers.length')
      km-table(
        :rows='workers',
        row-key='id',
        :columns='workerColumns',
        dense,
        flat,
        hide-pagination,
        :rows-per-page-options='[0]'
      )
        template(#body-cell-status='props')
          q-td(:props='props')
            .row.items-center.no-wrap
              q-icon(name='fiber_manual_record', color='positive', size='10px')
              .q-ml-4.km-description Online
        template(#body-cell-id='props')
          q-td(:props='props')
            .km-description.text-mono {{ truncateId(props.value) }}
            q-tooltip {{ props.value }}
        template(#body-cell-heartbeat='props')
          q-td(:props='props')
            .column
              .km-description {{ formatEpoch(props.value) }}
              .km-tiny.text-secondary-text {{ relativeTime(props.value) }}
    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='dns', size='48px', color='grey-4')
        .q-mt-8.km-description No active workers

  //- ═══════════════════════════════ REPEATABLES ═══════════════════════════
  template(v-if='section === "repeatables"')
    template(v-if='repeatables.length')
      km-table(
        :rows='repeatables',
        row-key='_key',
        :columns='repeatableColumns',
        dense,
        flat,
        hide-pagination,
        :rows-per-page-options='[0]'
      )
        template(#body-cell-task='props')
          q-td(:props='props')
            .km-description.text-weight-medium {{ props.value || '—' }}
        template(#body-cell-status='props')
          q-td(:props='props')
            km-chip(
              :label='props.row.paused ? "Paused" : "Active"',
              :color='props.row.paused ? "warning" : "positive"',
              round
            )
        template(#body-cell-next_run='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
              .km-tiny.text-secondary-text {{ relativeTime(props.value) }}
            template(v-else)
              .km-description —
        template(#body-cell-kwargs='props')
          q-td(:props='props')
            .km-tiny.text-mono(v-if='props.value && Object.keys(props.value).length')
              | {{ summarizeObj(props.value, 60) }}
              q-tooltip(max-width='400px')
                pre.q-ma-none(style='font-size: 11px; white-space: pre-wrap') {{ JSON.stringify(props.value, null, 2) }}
            .km-description(v-else) —
    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='repeat', size='48px', color='grey-4')
        .q-mt-8.km-description No repeatable jobs configured

  //- ═══════════════════════════════ JOBS ═══════════════════════════════
  template(v-if='section === "jobs"')
    //- Filter by status
    .row.items-center.q-gap-8.q-mb-md
      km-chip(
        v-for='s in jobFilterOptions',
        :key='s.value',
        :label='`${s.label} (${s.count})`',
        :color='jobFilter === s.value ? "primary-light" : "light"',
        :class='{ "text-primary": jobFilter === s.value }',
        round,
        clickable,
        @click='jobFilter = s.value'
      )

    template(v-if='filteredJobs.length')
      km-table(
        :rows='filteredJobs',
        row-key='id',
        :columns='jobColumns',
        dense,
        flat,
        hide-pagination,
        :rows-per-page-options='[0]'
      )
        template(#body-cell-status='props')
          q-td(:props='props')
            km-chip(:label='props.value', :color='statusColor(props.value)', round)
        template(#body-cell-task='props')
          q-td(:props='props')
            .km-description.text-weight-medium {{ shortTask(props.value) }}
            q-tooltip(v-if='props.value && props.value.length > 40') {{ props.value }}
        template(#body-cell-id='props')
          q-td(:props='props')
            .km-description.text-mono {{ truncateId(props.value) }}
            q-tooltip {{ props.value }}
        template(#body-cell-created_at='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
            template(v-else)
              .km-description —
        template(#body-cell-last_attempt='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
              .km-tiny.text-secondary-text {{ relativeTime(props.value) }}
            template(v-else)
              .km-description —
        template(#body-cell-retries='props')
          q-td(:props='props')
            .km-description {{ props.row.retries }}/{{ props.row.max_retries }}
        template(#body-cell-details='props')
          q-td(:props='props')
            km-btn(
              icon='visibility',
              flat,
              iconColor='icon',
              hoverColor='primary',
              hoverBg='primary-bg',
              iconSize='14px',
              size='sm',
              round,
              @click='openJobDetail(props.row)'
            )

    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='hourglass_empty', size='48px', color='grey-4')
        .q-mt-8.km-description No {{ jobFilter === 'all' ? '' : jobFilter }} jobs

  //- Error banner
  q-banner.bg-red-1.text-red-8.q-mb-16.q-mt-md(v-if='error', rounded, dense)
    template(#avatar)
      q-icon(name='error', color='red')
    | {{ error }}

  //- Loading overlay
  q-inner-loading(:showing='loading && !status')

  //- Job detail dialog
  q-dialog(v-model='jobDetailOpen', position='right')
    q-card.job-detail-drawer
      q-card-section.row.items-center.bb-border.q-py-sm
        .km-heading-7 Job Details
        q-space
        q-btn(flat, round, dense, icon='close', @click='jobDetailOpen = false')

      q-card-section.q-pt-md(v-if='jobDetail')
        .column.q-gap-12
          //- Status
          .row.items-center.q-gap-8
            .km-label.text-secondary-text Status
            km-chip(:label='jobDetail.status', :color='statusColor(jobDetail.status)', round)

          //- Task
          .column.q-gap-2
            .km-label.text-secondary-text Task
            .km-description.text-mono {{ jobDetail.task }}

          //- Job ID
          .column.q-gap-2
            .km-label.text-secondary-text Job ID
            .km-description.text-mono {{ jobDetail.id }}

          //- Priority
          .column.q-gap-2
            .km-label.text-secondary-text Priority
            .km-description {{ jobDetail.priority ?? 0 }}

          //- Retries
          .column.q-gap-2
            .km-label.text-secondary-text Retries
            .km-description {{ jobDetail.retries ?? 0 }} / {{ jobDetail.max_retries ?? 0 }}

          //- Backoff
          .column.q-gap-2(v-if='jobDetail.backoff')
            .km-label.text-secondary-text Backoff
            .km-description {{ jobDetail.backoff }}s

          //- TTL
          .column.q-gap-2(v-if='jobDetail.ttl')
            .km-label.text-secondary-text TTL
            .km-description {{ jobDetail.ttl }}s

          //- Created
          .column.q-gap-2
            .km-label.text-secondary-text Created
            .km-description {{ formatEpoch(jobDetail.created_at) }}

          //- Last attempt
          .column.q-gap-2(v-if='jobDetail.last_attempt')
            .km-label.text-secondary-text Last Attempt
            .km-description {{ formatEpoch(jobDetail.last_attempt) }}
              span.text-secondary-text.q-ml-4 {{ relativeTime(jobDetail.last_attempt) }}

          //- Delay until
          .column.q-gap-2(v-if='jobDetail.delay_until')
            .km-label.text-secondary-text Delay Until
            .km-description {{ formatEpoch(jobDetail.delay_until) }}

          //- Depends on
          .column.q-gap-2(v-if='jobDetail.depends_on && jobDetail.depends_on.length')
            .km-label.text-secondary-text Dependencies
            .km-description.text-mono(v-for='dep in jobDetail.depends_on', :key='dep') {{ dep }}

          //- Repeat every
          .column.q-gap-2(v-if='jobDetail.repeat_every')
            .km-label.text-secondary-text Repeat Every
            .km-description {{ jobDetail.repeat_every }}s

          //- Args
          q-expansion-item.bg-grey-1.border-radius-8(
            v-if='jobDetail.args && jobDetail.args.length',
            dense,
            label='Arguments',
            icon='data_array'
          )
            q-card.q-mt-xs
              q-card-section.bg-grey-2
                pre.q-ma-none.text-mono(style='white-space: pre-wrap; word-wrap: break-word; font-size: 11px') {{ JSON.stringify(jobDetail.args, null, 2) }}

          //- Kwargs
          q-expansion-item.bg-grey-1.border-radius-8(
            v-if='jobDetail.kwargs && Object.keys(jobDetail.kwargs).length',
            dense,
            label='Keyword Arguments',
            icon='data_object'
          )
            q-card.q-mt-xs
              q-card-section.bg-grey-2
                pre.q-ma-none.text-mono(style='white-space: pre-wrap; word-wrap: break-word; font-size: 11px') {{ JSON.stringify(jobDetail.kwargs, null, 2) }}

          //- Result
          q-expansion-item.bg-grey-1.border-radius-8(
            v-if='jobDetail.result != null',
            dense,
            label='Result',
            icon='output'
          )
            q-card.q-mt-xs
              q-card-section.bg-grey-2
                pre.q-ma-none.text-mono(style='white-space: pre-wrap; word-wrap: break-word; font-size: 11px') {{ formatResult(jobDetail.result) }}
</template>

<script>
export default {
  data() {
    return {
      status: null,
      loading: false,
      error: null,
      autoRefresh: true,
      refreshInterval: null,
      section: 'workers',
      jobFilter: 'all',
      jobDetailOpen: false,
      jobDetail: null,
      workerColumns: [
        { name: 'id', field: 'id', label: 'Worker ID', align: 'left' },
        { name: 'status', field: 'id', label: 'Status', align: 'left', style: 'width: 80px' },
        { name: 'queue', field: 'queue', label: 'Queue', align: 'left' },
        { name: 'concurrency', field: 'concurrency', label: 'Concurrency', align: 'center', style: 'width: 100px' },
        { name: 'heartbeat', field: 'heartbeat', label: 'Last Heartbeat', align: 'left' },
      ],
      repeatableColumns: [
        { name: 'task', field: (row) => row.job_def?.task_id || row.job_def?.task || '—', label: 'Task', align: 'left' },
        { name: 'schedule', field: (row) => row.job_def?.cron || (row.job_def?.every ? `every ${row.job_def.every}s` : '—'), label: 'Schedule', align: 'left' },
        { name: 'job_id', field: (row) => row.job_def?.kwargs?.job_id || '—', label: 'Job ID', align: 'left' },
        { name: 'kwargs', field: (row) => row.job_def?.kwargs || {}, label: 'Kwargs', align: 'left' },
        { name: 'next_run', field: 'next_run', label: 'Next Run', align: 'left' },
        { name: 'status', field: 'paused', label: 'Status', align: 'center', style: 'width: 90px' },
      ],
      jobColumns: [
        { name: 'task', field: 'task', label: 'Task', align: 'left' },
        { name: 'id', field: 'id', label: 'Job ID', align: 'left', style: 'width: 120px' },
        { name: 'status', field: 'status', label: 'Status', align: 'center', style: 'width: 100px' },
        { name: 'retries', field: 'retries', label: 'Retries', align: 'center', style: 'width: 80px' },
        { name: 'created_at', field: 'created_at', label: 'Created', align: 'left' },
        { name: 'last_attempt', field: 'last_attempt', label: 'Last Attempt', align: 'left' },
        { name: 'details', field: 'id', label: '', align: 'center', style: 'width: 48px' },
      ],
    }
  },
  computed: {
    workers() {
      return this.status?.workers || []
    },
    workerCount() {
      return this.workers.length
    },
    repeatables() {
      return (this.status?.repeatables || []).map((r, i) => ({
        ...r,
        _key: r.job_def?.task_id || r.job_def?.task || `rep-${i}`,
      }))
    },
    allJobs() {
      return this.status?.jobs || []
    },
    stalledJobs() {
      return this.status?.stalled_jobs || []
    },
    statusCounts() {
      return this.status?.status_counts || {}
    },
    jobFilterOptions() {
      const counts = this.statusCounts
      const total = this.allJobs.length
      return [
        { value: 'all', label: 'All', count: total },
        { value: 'waiting', label: 'Waiting', count: counts.waiting || 0 },
        { value: 'active', label: 'Active', count: counts.active || 0 },
        { value: 'completed', label: 'Completed', count: counts.completed || 0 },
        { value: 'failed', label: 'Failed', count: counts.failed || 0 },
        { value: 'delayed', label: 'Delayed', count: counts.delayed || 0 },
      ]
    },
    filteredJobs() {
      if (this.jobFilter === 'all') return this.allJobs
      return this.allJobs.filter((j) => j.status === this.jobFilter)
    },
  },
  mounted() {
    this.fetchStatus()
    if (this.autoRefresh) {
      this.startAutoRefresh()
    }
  },
  beforeUnmount() {
    this.stopAutoRefresh()
  },
  methods: {
    async fetchStatus() {
      this.loading = true
      this.error = null
      try {
        this.status = await this.$store.dispatch('getQueueStatus')
      } catch (e) {
        this.error = 'Failed to fetch queue status'
        console.error('Queue status error:', e)
      } finally {
        this.loading = false
      }
    },
    toggleAutoRefresh(val) {
      if (val) this.startAutoRefresh()
      else this.stopAutoRefresh()
    },
    startAutoRefresh() {
      this.stopAutoRefresh()
      this.refreshInterval = setInterval(() => this.fetchStatus(), 5000)
    },
    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },
    openJobDetail(job) {
      this.jobDetail = job
      this.jobDetailOpen = true
    },
    formatEpoch(epoch) {
      if (!epoch) return '—'
      try {
        return new Date(epoch * 1000).toLocaleString()
      } catch {
        return '—'
      }
    },
    relativeTime(epoch) {
      if (!epoch) return ''
      try {
        const diff = Math.round(Date.now() / 1000 - epoch)
        if (diff < 0) {
          const abs = Math.abs(diff)
          if (abs < 60) return `in ${abs}s`
          if (abs < 3600) return `in ${Math.round(abs / 60)}m`
          if (abs < 86400) return `in ${Math.round(abs / 3600)}h`
          return `in ${Math.round(abs / 86400)}d`
        }
        if (diff < 5) return 'just now'
        if (diff < 60) return `${diff}s ago`
        if (diff < 3600) return `${Math.round(diff / 60)}m ago`
        if (diff < 86400) return `${Math.round(diff / 3600)}h ago`
        return `${Math.round(diff / 86400)}d ago`
      } catch {
        return ''
      }
    },
    truncateId(id) {
      if (!id) return '—'
      return id.length > 12 ? id.slice(0, 8) + '…' : id
    },
    shortTask(task) {
      if (!task) return '—'
      return task.length > 40 ? '…' + task.slice(-38) : task
    },
    summarizeObj(obj, maxLen) {
      if (!obj) return '—'
      const str = JSON.stringify(obj)
      return str.length > maxLen ? str.slice(0, maxLen) + '…' : str
    },
    formatResult(result) {
      if (result === null || result === undefined) return '—'
      if (typeof result === 'string') return result
      return JSON.stringify(result, null, 2)
    },
    statusColor(status) {
      const colors = {
        active: 'positive',
        waiting: 'primary-light',
        completed: 'light',
        failed: 'negative',
        delayed: 'warning',
        cancelled: 'negative',
        expired: 'negative',
      }
      return colors[status] || 'light'
    },
  },
}
</script>

<style lang="stylus" scoped>
.stat-card
  padding 12px 16px
  background #f8f9fa
  border-radius 8px
  border 1px solid #eee

.stat-value
  font-size 22px
  font-weight 600
  line-height 1.4
  margin-top 4px

.stat-label
  font-size 12px
  color #666

.text-mono
  font-family 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace

.job-detail-drawer
  width 420px
  max-width 90vw
  height 100vh
  max-height 100vh
  border-radius 0

  pre
    font-family 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace
</style>

<template lang="pug">
.column.full-width.no-wrap
  //- ═══════════════════════ HEADER ═══════════════════════════════
  .row.items-center.q-mb-16
    .row.items-center.q-gap-8
      .km-heading-4 Queue Dashboard
      km-select(
        v-model='selectedQueue',
        :options='queueOptions',
        emit-value,
        map-options,
        placeholder='All Queues',
        @update:model-value='onQueueChange'
      )
      .status-dot(:class='overview && overview.is_paused ? "paused" : "online"', v-if='overview')
        km-tooltip(:label='overview.is_paused ? "Queue paused" : "Queue running"')
    q-space
    .row.items-center.q-gap-8
      //- Queue control
      km-btn(
        v-if='overview && !overview.is_paused && selectedQueue',
        icon='pause',
        label='Pause',
        flat,
        iconColor='warning',
        hoverColor='warning',
        labelClass='km-title',
        iconSize='14px',
        hoverBg='warning-bg',
        @click='handlePauseQueue'
      )
      km-btn(
        v-if='overview && overview.is_paused && selectedQueue',
        icon='play_arrow',
        label='Resume',
        flat,
        iconColor='positive',
        hoverColor='positive',
        labelClass='km-title',
        iconSize='14px',
        hoverBg='positive-bg',
        @click='handleResumeQueue'
      )
      km-btn(
        icon='refresh',
        label='Refresh',
        @click='refreshAll',
        iconColor='icon',
        hoverColor='primary',
        labelClass='km-title',
        flat,
        iconSize='14px',
        hoverBg='primary-bg',
        :loading='loading'
      )
      .row.items-center.no-wrap.q-gap-4
        .km-title Auto-refresh (5s)
        km-toggle(v-model='autoRefresh', @update:model-value='toggleAutoRefresh')

  //- ═══════════════════════ OVERVIEW CARDS ═══════════════════════
  .row.q-gap-16.q-mb-20(v-if='overview')
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='hourglass_top', size='20px', color='primary')
          .stat-label Waiting
        .stat-value.text-primary {{ statusCounts.waiting || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='play_circle', size='20px', color='positive')
          .stat-label Active
        .stat-value.text-positive {{ statusCounts.active || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='check_circle', size='20px', color='grey-6')
          .stat-label Completed
        .stat-value.text-grey-7 {{ statusCounts.completed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='error', size='20px', color='negative')
          .stat-label Failed
        .stat-value.text-negative {{ statusCounts.failed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='schedule', size='20px', color='warning')
          .stat-label Delayed
        .stat-value.text-warning {{ statusCounts.delayed || 0 }}
    .col
      .stat-card
        .row.items-center.q-gap-6
          q-icon(name='repeat', size='20px', color='info')
          .stat-label Repeatables
        .stat-value.text-info {{ overview.total_repeatables || 0 }}

  //- ═══════════════ PER-QUEUE BREAKDOWN (All Queues) ═════════════
  template(v-if='!selectedQueue && overview && overview.queues && overview.queues.length')
    .km-description.text-secondary-text.text-weight-medium.q-mb-12 Per-Queue Breakdown
    .row.q-gap-16.q-mb-20
      .col(v-for='q in overview.queues', :key='q.queue')
        .queue-breakdown-card
          .row.items-center.q-gap-8.q-mb-12
            .status-dot.status-dot--sm(:class='q.is_paused ? "paused" : "online"')
            .km-title.text-capitalize {{ q.queue }}
          .row.q-gap-16
            .column.items-center.col
              .breakdown-count.text-primary {{ q.status_counts?.waiting || 0 }}
              .breakdown-label Waiting
            .column.items-center.col
              .breakdown-count.text-positive {{ q.status_counts?.active || 0 }}
              .breakdown-label Active
            .column.items-center.col
              .breakdown-count.text-negative {{ q.status_counts?.failed || 0 }}
              .breakdown-label Failed
            .column.items-center.col
              .breakdown-count.text-info {{ q.total_repeatables || 0 }}
              .breakdown-label Repeatables

  //- ═══════════════════════ METRICS BAR ═══════════════════════════
  .row.q-gap-16.q-my-md(v-if='metrics')
    .col
      .metrics-card
        .row.items-center.q-gap-6
          q-icon(name='trending_up', size='18px', color='positive')
          .metrics-label Throughput
        .metrics-value {{ metrics.throughput ?? 0 }} completed
    .col
      .metrics-card
        .row.items-center.q-gap-6
          q-icon(name='warning_amber', size='18px', color='negative')
          .metrics-label Failures
        .metrics-value {{ metrics.failures ?? 0 }} failed
    .col
      .metrics-card
        .row.items-center.q-gap-6
          q-icon(name='replay', size='18px', color='warning')
          .metrics-label Total Retries
        .metrics-value {{ metrics.retries ?? 0 }}
    .col
      .metrics-card
        .row.items-center.q-gap-6
          q-icon(name='timer', size='18px', color='info')
          .metrics-label Avg Duration
        .metrics-value {{ metrics.avg_duration != null ? metrics.avg_duration + 's' : '—' }}

  //- ═══════════════════════ SECTION TABS ═════════════════════════
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
    q-tab(name='jobs', :label='`Jobs (${jobsData.total || 0})`')
    q-tab(name='repeatables', :label='`Repeatables (${repeatablesData.total || 0})`')
    q-tab(name='dlq', :label='`DLQ (${dlqData.total || 0})`')

  //- ═══════════════════════ JOBS TAB ═════════════════════════════
  template(v-if='section === "jobs"')
    //- State filter chips
    .row.items-center.q-gap-8.q-mb-md
      km-chip(
        v-for='s in jobFilterOptions',
        :key='s.value',
        :label='`${s.label} (${s.count})`',
        :color='jobFilter === s.value ? "primary-light" : "light"',
        :class='{ "text-primary": jobFilter === s.value }',
        round,
        clickable,
        @click='changeJobFilter(s.value)'
      )
      q-space
      //- Clean completed
      km-btn(
        icon='cleaning_services',
        label='Clean completed',
        flat,
        iconColor='grey-6',
        hoverColor='primary',
        labelClass='km-title',
        iconSize='14px',
        hoverBg='primary-bg',
        size='sm',
        @click='handleCleanCompleted'
      )

    template(v-if='jobsData.jobs && jobsData.jobs.length')
      km-table(
        :rows='jobsData.jobs',
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
        template(#body-cell-queue='props')
          q-td(:props='props')
            km-chip.text-capitalize(v-if='props.value', :label='props.value', color='light', round)
            .km-description(v-else) —
        template(#body-cell-task='props')
          q-td(:props='props')
            .km-description.text-weight-medium {{ shortTask(props.value) }}
            km-tooltip(v-if='props.value && props.value.length > 40', :label='props.value')
        template(#body-cell-id='props')
          q-td(:props='props')
            .km-description.text-mono {{ truncateId(props.value) }}
            km-tooltip(:label='props.value')
        template(#body-cell-created_at='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
            template(v-else)
              .km-description &mdash;
        template(#body-cell-last_attempt='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
              .km-tiny.text-secondary-text {{ relativeTime(props.value) }}
            template(v-else)
              .km-description &mdash;
        template(#body-cell-retries='props')
          q-td(:props='props')
            .km-description {{ props.row.retries }}/{{ props.row.max_retries }}
        template(#body-cell-actions='props')
          q-td(:props='props')
            .row.items-center.no-wrap.q-gap-4
              km-btn(
                icon='visibility',
                flat,
                iconColor='icon',
                hoverColor='primary',
                hoverBg='primary-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Details',
                @click='openJobDetail(props.row)'
              )
              km-btn(
                v-if='props.row.status === "failed"',
                icon='replay',
                flat,
                iconColor='warning',
                hoverColor='warning',
                hoverBg='warning-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Retry',
                @click='handleRetryJob(props.row.id, props.row.queue)',
                :loading='actionLoading === props.row.id'
              )
              km-btn(
                v-if='props.row.status === "waiting" || props.row.status === "delayed"',
                icon='cancel',
                flat,
                iconColor='negative',
                hoverColor='negative',
                hoverBg='negative-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Cancel',
                @click='handleCancelJob(props.row.id, props.row.queue)',
                :loading='actionLoading === props.row.id'
              )
              km-btn(
                v-if='props.row.status === "completed" || props.row.status === "failed"',
                icon='delete_outline',
                flat,
                iconColor='grey-6',
                hoverColor='negative',
                hoverBg='negative-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Remove',
                @click='handleRemoveJob(props.row.id, props.row.queue)',
                :loading='actionLoading === props.row.id'
              )

      //- Pagination
      .row.items-center.justify-center.q-mt-md(v-if='jobsData.total_pages > 1')
        q-pagination(
          v-model='jobPage',
          :max='jobsData.total_pages',
          :max-pages='7',
          direction-links,
          boundary-links,
          flat,
          color='primary',
          active-color='primary',
          @update:model-value='fetchJobs'
        )

    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='hourglass_empty', size='48px', color='grey-4')
        .q-mt-8.km-description No {{ jobFilter === 'all' ? '' : jobFilter }} jobs

  //- ═══════════════════════ REPEATABLES TAB ══════════════════════
  template(v-if='section === "repeatables"')
    template(v-if='repeatablesData.repeatables && repeatablesData.repeatables.length')
      km-table(
        :rows='repeatablesData.repeatables',
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
              .km-description &mdash;
        template(#body-cell-kwargs='props')
          q-td(:props='props')
            .km-tiny.text-mono(v-if='props.value && Object.keys(props.value).length')
              | {{ summarizeObj(props.value, 60) }}
              q-tooltip(max-width='400px')
                pre.q-ma-none(style='font-size: 11px; white-space: pre-wrap') {{ JSON.stringify(props.value, null, 2) }}
            .km-description(v-else) &mdash;
    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='repeat', size='48px', color='grey-4')
        .q-mt-8.km-description No repeatable jobs configured

  //- ═══════════════════════ DLQ TAB ═════════════════════════════
  template(v-if='section === "dlq"')
    template(v-if='dlqData.jobs && dlqData.jobs.length')
      km-table(
        :rows='dlqData.jobs',
        row-key='id',
        :columns='dlqColumns',
        dense,
        flat,
        hide-pagination,
        :rows-per-page-options='[0]'
      )
        template(#body-cell-task='props')
          q-td(:props='props')
            .km-description.text-weight-medium {{ shortTask(props.value) }}
            km-tooltip(v-if='props.value && props.value.length > 40', :label='props.value')
        template(#body-cell-queue='props')
          q-td(:props='props')
            km-chip.text-capitalize(v-if='props.value', :label='props.value', color='light', round)
            .km-description(v-else) —
        template(#body-cell-id='props')
          q-td(:props='props')
            .km-description.text-mono {{ truncateId(props.value) }}
            km-tooltip(:label='props.value')
        template(#body-cell-created_at='props')
          q-td(:props='props')
            template(v-if='props.value')
              .km-description {{ formatEpoch(props.value) }}
            template(v-else)
              .km-description &mdash;
        template(#body-cell-retries='props')
          q-td(:props='props')
            .km-description {{ props.row.retries }}/{{ props.row.max_retries }}
        template(#body-cell-actions='props')
          q-td(:props='props')
            .row.items-center.no-wrap.q-gap-4
              km-btn(
                icon='replay',
                flat,
                iconColor='warning',
                hoverColor='warning',
                hoverBg='warning-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Retry',
                @click='handleRetryJob(props.row.id, props.row.queue)',
                :loading='actionLoading === props.row.id'
              )
              km-btn(
                icon='delete_outline',
                flat,
                iconColor='negative',
                hoverColor='negative',
                hoverBg='negative-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Remove',
                @click='handleRemoveJob(props.row.id, props.row.queue)',
                :loading='actionLoading === props.row.id'
              )
              km-btn(
                icon='visibility',
                flat,
                iconColor='icon',
                hoverColor='primary',
                hoverBg='primary-bg',
                iconSize='14px',
                size='sm',
                round,
                tooltip='Details',
                @click='openJobDetail(props.row)'
              )

      //- DLQ Pagination
      .row.items-center.justify-center.q-mt-md(v-if='dlqData.total_pages > 1')
        q-pagination(
          v-model='dlqPage',
          :max='dlqData.total_pages',
          :max-pages='7',
          direction-links,
          boundary-links,
          flat,
          color='primary',
          active-color='primary',
          @update:model-value='fetchDLQ'
        )

    template(v-else)
      .text-center.q-pa-xl.text-secondary-text
        q-icon(name='delete_sweep', size='48px', color='grey-4')
        .q-mt-8.km-description No failed jobs in the dead letter queue

  //- ═══════════════════════ ERROR ════════════════════════════════
  q-banner.bg-red-1.text-red-8.q-mb-16.q-mt-md(v-if='error', rounded, dense)
    template(#avatar)
      q-icon(name='error', color='red')
    | {{ error }}

  //- Loading overlay
  km-inner-loading(:showing='loading && !overview')

  //- ═══════════════════════ JOB DETAIL DIALOG ═══════════════════
  q-dialog(v-model='jobDetailOpen', position='right')
    q-card.job-detail-drawer
      q-card-section.row.items-center.bb-border.q-py-sm
        .km-heading-7 Job Details
        q-space
        //- Action buttons in drawer header
        .row.q-gap-4(v-if='jobDetail')
          km-btn(
            v-if='jobDetail.status === "failed"',
            icon='replay',
            label='Retry',
            flat,
            iconColor='warning',
            hoverColor='warning',
            labelClass='km-title',
            iconSize='14px',
            size='sm',
            hoverBg='warning-bg',
            @click='handleRetryJob(jobDetail.id, jobDetail.queue); jobDetailOpen = false',
            :loading='actionLoading === jobDetail.id'
          )
          km-btn(
            v-if='jobDetail.status === "waiting" || jobDetail.status === "delayed"',
            icon='cancel',
            label='Cancel',
            flat,
            iconColor='negative',
            hoverColor='negative',
            labelClass='km-title',
            iconSize='14px',
            size='sm',
            hoverBg='negative-bg',
            @click='handleCancelJob(jobDetail.id, jobDetail.queue); jobDetailOpen = false',
            :loading='actionLoading === jobDetail.id'
          )
          km-btn(
            v-if='jobDetail.status === "completed" || jobDetail.status === "failed"',
            icon='delete_outline',
            label='Remove',
            flat,
            iconColor='grey-6',
            hoverColor='negative',
            labelClass='km-title',
            iconSize='14px',
            size='sm',
            hoverBg='negative-bg',
            @click='handleRemoveJob(jobDetail.id, jobDetail.queue); jobDetailOpen = false',
            :loading='actionLoading === jobDetail.id'
          )
        km-btn.q-ml-8(icon='close', flat, round, iconSize='14px', iconColor='icon', hoverColor='primary', hoverBg='primary-bg', @click='jobDetailOpen = false')

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

          //- Queue
          .column.q-gap-2(v-if='jobDetail.queue')
            .km-label.text-secondary-text Queue
            km-chip.text-capitalize(:label='jobDetail.queue', color='light', round)

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

  //- ═══════════════════════ CLEAN DIALOG ═════════════════════════
  km-popup-confirm(
    :visible='cleanDialogOpen',
    title='Clean Queue',
    confirmButtonLabel='Clean',
    cancelButtonLabel='Cancel',
    :loading='cleanLoading',
    @confirm='confirmClean',
    @cancel='cleanDialogOpen = false'
  )
    .km-description.q-mb-sm Clean completed jobs older than:
    km-select(
      v-model='cleanHours',
      :options='cleanHoursOptions',
      emit-value,
      map-options
    )
</template>

<script>
const QUEUE_OPTIONS = [
  { label: 'All Queues', value: null },
  { label: 'default', value: 'default' },
  { label: 'sync', value: 'sync' },
  { label: 'evaluation', value: 'evaluation' },
  { label: 'maintenance', value: 'maintenance' },
]

export default {
  data() {
    return {
      // Queue selector
      selectedQueue: null, // null = all queues
      queueOptions: QUEUE_OPTIONS,

      // Data from endpoints
      overview: null,
      metrics: null,
      jobsData: { jobs: [], total: 0, total_pages: 1 },
      repeatablesData: { repeatables: [], total: 0 },
      dlqData: { jobs: [], total: 0, total_pages: 1 },

      // UI state
      loading: false,
      error: null,
      autoRefresh: true,
      refreshInterval: null,
      section: 'jobs',
      jobFilter: 'all',
      jobPage: 1,
      dlqPage: 1,
      jobDetailOpen: false,
      jobDetail: null,
      actionLoading: null,

      // Clean dialog state
      cleanDialogOpen: false,
      cleanLoading: false,
      cleanHours: 24,
      cleanHoursOptions: [
        { label: '1 hour', value: 1 },
        { label: '6 hours', value: 6 },
        { label: '12 hours', value: 12 },
        { label: '24 hours', value: 24 },
        { label: '48 hours', value: 48 },
        { label: '7 days', value: 168 },
      ],

      // Column definitions
      repeatableColumns: [
        { name: 'task', field: (row) => row.job_def?.task_id || row.job_def?.task || '—', label: 'Task', align: 'left' },
        { name: 'queue', field: 'queue', label: 'Queue', align: 'left', style: 'width: 100px' },
        { name: 'schedule', field: (row) => row.job_def?.cron || (row.job_def?.every ? `every ${row.job_def.every}s` : '—'), label: 'Schedule', align: 'left' },
        { name: 'job_id', field: (row) => row.job_def?.kwargs?.job_id || '—', label: 'Job ID', align: 'left' },
        { name: 'kwargs', field: (row) => row.job_def?.kwargs || {}, label: 'Kwargs', align: 'left' },
        { name: 'next_run', field: 'next_run', label: 'Next Run', align: 'left' },
        { name: 'status', field: 'paused', label: 'Status', align: 'center', style: 'width: 90px' },
      ],
      jobColumns: [
        { name: 'task', field: 'task', label: 'Task', align: 'left' },
        { name: 'id', field: 'id', label: 'Job ID', align: 'left', style: 'width: 120px' },
        { name: 'queue', field: 'queue', label: 'Queue', align: 'left', style: 'width: 100px' },
        { name: 'status', field: 'status', label: 'Status', align: 'center', style: 'width: 100px' },
        { name: 'retries', field: 'retries', label: 'Retries', align: 'center', style: 'width: 80px' },
        { name: 'created_at', field: 'created_at', label: 'Created', align: 'left' },
        { name: 'last_attempt', field: 'last_attempt', label: 'Last Attempt', align: 'left' },
        { name: 'actions', field: 'id', label: '', align: 'center', style: 'width: 120px' },
      ],
      dlqColumns: [
        { name: 'task', field: 'task', label: 'Task', align: 'left' },
        { name: 'id', field: 'id', label: 'Job ID', align: 'left', style: 'width: 120px' },
        { name: 'queue', field: 'queue', label: 'Queue', align: 'left', style: 'width: 100px' },
        { name: 'retries', field: 'retries', label: 'Retries', align: 'center', style: 'width: 80px' },
        { name: 'created_at', field: 'created_at', label: 'Created', align: 'left' },
        { name: 'last_attempt', field: 'last_attempt', label: 'Last Attempt', align: 'left' },
        { name: 'actions', field: 'id', label: '', align: 'center', style: 'width: 120px' },
      ],
    }
  },
  computed: {
    statusCounts() {
      return this.overview?.status_counts || {}
    },
    jobFilterOptions() {
      const counts = this.statusCounts
      const total = this.jobsData?.total || 0
      return [
        { value: 'all', label: 'All', count: this.jobFilter === 'all' ? total : '…' },
        { value: 'waiting', label: 'Waiting', count: counts.waiting || 0 },
        { value: 'active', label: 'Active', count: counts.active || 0 },
        { value: 'completed', label: 'Completed', count: counts.completed || 0 },
        { value: 'failed', label: 'Failed', count: counts.failed || 0 },
        { value: 'delayed', label: 'Delayed', count: counts.delayed || 0 },
      ]
    },
  },
  mounted() {
    this.refreshAll()
    if (this.autoRefresh) {
      this.startAutoRefresh()
    }
  },
  beforeUnmount() {
    this.stopAutoRefresh()
  },
  methods: {
    // ── Queue switch ────────────────────────────────────────────
    onQueueChange() {
      this.jobPage = 1
      this.dlqPage = 1
      this.refreshAll()
    },

    // ── Fetchers ────────────────────────────────────────────────
    async refreshAll() {
      this.loading = true
      this.error = null
      try {
        await Promise.all([
          this.fetchOverview(),
          this.fetchMetrics(),
          this.fetchJobs(),
          this.fetchRepeatables(),
          this.fetchDLQ(),
        ])
      } catch (e) {
        this.error = 'Failed to fetch queue dashboard data'
        console.error('Queue dashboard error:', e)
      } finally {
        this.loading = false
      }
    },

    async fetchOverview() {
      try {
        this.overview = await this.$store.dispatch('getDashboardOverview', { queue: this.selectedQueue })
      } catch (e) {
        console.error('Overview fetch error:', e)
      }
    },

    async fetchMetrics() {
      try {
        this.metrics = await this.$store.dispatch('getDashboardMetrics', { queue: this.selectedQueue })
      } catch (e) {
        console.error('Metrics fetch error:', e)
      }
    },

    async fetchJobs() {
      try {
        this.jobsData = await this.$store.dispatch('getDashboardJobs', {
          queue: this.selectedQueue,
          state: this.jobFilter,
          page: this.jobPage,
          size: 50,
        })
      } catch (e) {
        console.error('Jobs fetch error:', e)
      }
    },

    async fetchRepeatables() {
      try {
        const data = await this.$store.dispatch('getDashboardRepeatables', { queue: this.selectedQueue })
        this.repeatablesData = {
          ...data,
          repeatables: (data.repeatables || []).map((r, i) => ({
            ...r,
            _key: r.job_def?.task_id || r.job_def?.task || `rep-${i}`,
          })),
        }
      } catch (e) {
        console.error('Repeatables fetch error:', e)
      }
    },

    async fetchDLQ() {
      try {
        this.dlqData = await this.$store.dispatch('getDashboardDLQ', {
          queue: this.selectedQueue,
          page: this.dlqPage,
          size: 50,
        })
      } catch (e) {
        console.error('DLQ fetch error:', e)
      }
    },

    // ── Job actions ─────────────────────────────────────────────
    async handleRetryJob(jobId, queue) {
      const jobQueue = queue || this.selectedQueue || 'default'
      this.actionLoading = jobId
      try {
        const res = await this.$store.dispatch('retryJob', { jobId, queue: jobQueue })
        if (res?.ok) {
          this.$q?.notify?.({ type: 'positive', message: 'Job queued for retry' })
          await this.refreshAll()
        } else {
          this.$q?.notify?.({ type: 'negative', message: res?.error || 'Retry failed' })
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Retry failed' })
      } finally {
        this.actionLoading = null
      }
    },

    async handleRemoveJob(jobId, queue) {
      const jobQueue = queue || this.selectedQueue || 'default'
      this.actionLoading = jobId
      try {
        const res = await this.$store.dispatch('removeJob', { jobId, queue: jobQueue })
        if (res?.ok) {
          this.$q?.notify?.({ type: 'positive', message: 'Job removed' })
          await this.refreshAll()
        } else {
          this.$q?.notify?.({ type: 'negative', message: res?.error || 'Remove failed' })
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Remove failed' })
      } finally {
        this.actionLoading = null
      }
    },

    async handleCancelJob(jobId, queue) {
      const jobQueue = queue || this.selectedQueue || 'default'
      this.actionLoading = jobId
      try {
        const res = await this.$store.dispatch('cancelQueueJob', { jobId, queue: jobQueue })
        if (res?.ok) {
          this.$q?.notify?.({ type: 'positive', message: 'Job cancelled' })
          await this.refreshAll()
        } else {
          this.$q?.notify?.({ type: 'negative', message: res?.error || 'Cancel failed' })
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Cancel failed' })
      } finally {
        this.actionLoading = null
      }
    },

    // ── Queue control ───────────────────────────────────────────
    async handlePauseQueue() {
      if (!this.selectedQueue) return
      try {
        const res = await this.$store.dispatch('pauseQueue', this.selectedQueue)
        if (res?.ok) {
          this.$q?.notify?.({ type: 'warning', message: 'Queue paused' })
          await this.fetchOverview()
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Failed to pause queue' })
      }
    },

    async handleResumeQueue() {
      if (!this.selectedQueue) return
      try {
        const res = await this.$store.dispatch('resumeQueue', this.selectedQueue)
        if (res?.ok) {
          this.$q?.notify?.({ type: 'positive', message: 'Queue resumed' })
          await this.fetchOverview()
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Failed to resume queue' })
      }
    },

    handleCleanCompleted() {
      this.cleanDialogOpen = true
    },

    async confirmClean() {
      this.cleanLoading = true
      try {
        const res = await this.$store.dispatch('cleanQueue', {
          queue: this.selectedQueue || 'default',
          state: 'completed',
          older_than_hours: this.cleanHours,
        })
        if (res?.ok) {
          this.$q?.notify?.({ type: 'positive', message: `Cleaned completed jobs older than ${this.cleanHours}h` })
          this.cleanDialogOpen = false
          await this.refreshAll()
        }
      } catch (e) {
        this.$q?.notify?.({ type: 'negative', message: 'Clean failed' })
      } finally {
        this.cleanLoading = false
      }
    },

    // ── Filter & pagination ─────────────────────────────────────
    changeJobFilter(filter) {
      this.jobFilter = filter
      this.jobPage = 1
      this.fetchJobs()
    },

    // ── Auto-refresh ────────────────────────────────────────────
    toggleAutoRefresh(val) {
      if (val) this.startAutoRefresh()
      else this.stopAutoRefresh()
    },
    startAutoRefresh() {
      this.stopAutoRefresh()
      this.refreshInterval = setInterval(() => this.refreshAll(), 5000)
    },
    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
    },

    // ── Detail drawer ───────────────────────────────────────────
    openJobDetail(job) {
      this.jobDetail = job
      this.jobDetailOpen = true
    },

    // ── Formatters ──────────────────────────────────────────────
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
// ── Status dot ────────────────────────────────────────────
.status-dot
  width 12px
  height 12px
  border-radius 50%
  flex-shrink 0

  &.online
    background #22c55e
    box-shadow 0 0 6px 2px rgba(34, 197, 94, 0.45)

  &.paused
    background #f59e0b
    box-shadow 0 0 6px 2px rgba(245, 158, 11, 0.40)

  &.status-dot--sm
    width 8px
    height 8px

// ── Overview stat cards ───────────────────────────────────
.stat-card
  padding 16px 20px
  background var(--km-bg-secondary, #f8f9fa)
  border-radius 12px
  border 1px solid var(--km-border, #eee)

.stat-value
  font-size 28px
  font-weight 700
  line-height 1.3
  margin-top 6px

.stat-label
  font-size 13px
  font-weight 500
  color var(--km-text-secondary, #666)

// ── Per-Queue breakdown cards ─────────────────────────────
.queue-breakdown-card
  padding 16px 20px
  background var(--km-bg-secondary, #f8f9fa)
  border-radius 12px
  border 1px solid var(--km-border, #eee)

.breakdown-count
  font-size 20px
  font-weight 700
  line-height 1.3

.breakdown-label
  font-size 11px
  font-weight 500
  color var(--km-text-secondary, #888)
  margin-top 2px

// ── Metrics cards ─────────────────────────────────────────
.metrics-card
  padding 14px 18px
  background var(--km-bg-secondary, #f0f4ff)
  border-radius 12px
  border 1px solid var(--km-border, #e0e7ff)

.metrics-value
  font-size 17px
  font-weight 600
  line-height 1.4
  margin-top 4px
  color var(--km-text-primary, #333)

.metrics-label
  font-size 12px
  font-weight 500
  color var(--km-text-secondary, #888)

// ── Misc ──────────────────────────────────────────────────
.text-mono
  font-family 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace

.job-detail-drawer
  width 480px
  max-width 90vw
  height 100vh
  max-height 100vh
  border-radius 0

  pre
    font-family 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace
</style>

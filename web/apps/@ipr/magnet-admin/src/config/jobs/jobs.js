import { formatDateTime } from '@shared'
import StatusBadge from './components/StatusBadge.vue'
import NameDescription from './components/NameDescription.vue'

import { markRaw } from 'vue'

export const jobTypeOptions = [
  {
    value: 'custom',
    label: 'Custom',
  },
  {
    value: 'sync_collection',
    label: 'Knowledge sync',
  },
  {
    value: 'post_processing_conversations',
    label: 'Post processing conversations',
  },
  {
    value: 'sync_knowledge_graph_source',
    label: 'Knowledge graph source sync',
  }
]

export const jobIntervalOptions = [
  {
    value: 'every_5_minutes',
    label: 'Every 5 minutes',
  },
  {
    value: 'hourly',
    label: 'Hourly',
  },
  {
    value: 'daily',
    label: 'Daily',
  },
  {
    value: 'weekly',
    label: 'Weekly',
  },
  {
    value: 'monthly',
    label: 'Monthly',
  },
  {
    value: 'custom',
    label: 'Custom',
  },
]

export const jobRunTypeOptions = [
  {
    value: 'one_time_immediate',
    label: 'One time immediate',
  },
  {
    value: 'one_time_scheduled',
    label: 'One time scheduled',
  },
  {
    value: 'recurring',
    label: 'Recurring',
  },
]

const jobsControls = {
  last_run: {
    name: 'last_run',
    label: 'Last run',
    field: 'last_run',
    // type: 'Date',
    format: (val) => formatDateTime(val),
    align: 'left',
  },
  nameDescription: {
    name: 'nameDescription',
    label: 'Name',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
    sort: (a, b, rowA, rowB) => {
      return rowA.name.localeCompare(rowB.name)
    },
  },
  type: {
    name: 'type',
    label: 'Type',
    // field: (row) => row?.definition?.run_configuration?.type,
    field: (row) => jobTypeOptions?.find((el) => el.value === row?.definition?.run_configuration?.type)?.label,
    align: 'left',
  },
  next_run: {
    name: 'next_run',
    label: 'Next run',
    field: 'next_run',
    // type: 'Date',
    format: (val) => formatDateTime(val),
    align: 'left',
  },
  status: {
    name: 'status',
    label: 'Status',
    field: 'status',
    type: 'component',
    component: markRaw(StatusBadge),
  },
  job_interval: {
    name: 'job_interval',
    label: 'Job interval',
    // field: (row) => row?.definition?.interval,
    field: (row) => jobIntervalOptions?.find((el) => el.value === row?.definition?.interval)?.label,
    align: 'left',
  },
  job_type: {
    name: 'job_type',
    label: 'Job type',
    field: (row) => jobRunTypeOptions?.find((el) => el.value === row?.definition?.job_type)?.label,
    align: 'left',
  },
}

export default jobsControls

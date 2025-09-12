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
              .col-auto.center-flex-y.q-ml-md(v-if='groupBy !== "flat"')
                .text-secondary-text.q-mr-sm Group by:
                km-select(
                  :options='groups',
                  v-model='groupBy',
                  bg-color='background',
                  height='30px',
                  map-options,
                  emit-value,
                  option-value='value',
                  option-label='label'
                )
              .col-auto.center-flex-y.q-ml-md
                template(v-if='filterObject?.tool || filterObject?.job')
                  .text-secondary-text.q-mr-sm {{ filterObject?.tool ? 'Tool:' : 'Job:' }}
                  q-chip.q-my-none(text-color='primary', color='primary-light', square, size='12px') 
                    .row.fit.items-center
                      .col.text-center {{ filterObject?.tool ? filterObject?.tool : filterObject?.job }}
                      .col-auto.q-ml-xs
                        q-icon.q-my-auto.cursor-pointer(name='fa fa-times', @click.stop.prevent='removeFilter')
              q-space
              .col-auto.center-flex-y
                km-btn.q-mr-12(
                  v-if='groupBy == "flat"',
                  icon='fas fa-download',
                  label='Report',
                  @click='getEvalutionReport',
                  iconColor='icon',
                  hoverColor='primary',
                  labelClass='km-title',
                  flat,
                  iconSize='16px',
                  hoverBg='primary-bg',
                  :disable='selected.length < 2',
                  :tooltip='selected.length < 2 ? "Select at least 2 records" : ""'
                )
              .col-auto.center-flex-y
                km-btn.q-mr-12(
                  v-if='groupBy == "flat"',
                  icon='compare',
                  label='Compare',
                  @click='compare(false)',
                  iconColor='icon',
                  hoverColor='primary',
                  labelClass='km-title',
                  flat,
                  iconSize='16px',
                  hoverBg='primary-bg',
                  :disable='selected.length < 2',
                  :tooltip='selected.length < 2 ? "Select at least 2 records" : ""'
                )
              .col-auto.center-flex-y
                km-btn.q-mr-12(
                  v-if='groupBy == "flat"',
                  icon='delete',
                  label='Delete',
                  @click='showDeleteDialog = true',
                  iconColor='icon',
                  hoverColor='primary',
                  labelClass='km-title',
                  flat,
                  iconSize='16px',
                  hoverBg='primary-bg',
                  :disable='selected.length < 1',
                  :tooltip='selected.length < 1 ? "Select at least 1 records" : ""'
                )
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
              .col-auto.center-flex-y
                km-btn.q-mr-12(v-if='!filterObject?.row', label='New', @click='openNewDetails')
              .col-auto.center-flex-y
            q-separator.q-my-sm
            .row.q-mb-sm.items-center(v-if='filterObject?.row')
              .col-auto
                .column
                  .col(v-if='filterObject?.job')
                    .row.q-gap-12.no-wrap.items-baseline
                      .col-auto
                        .km-field.text-secondary-text Job start:
                      .col-auto
                        .km-heading-3.q-mr-sm {{ filterObjectStartData }}
                  .col
                    .row.q-gap-12.no-wrap.items-baseline
                      .col-auto
                        .km-field.text-secondary-text Evaluated tool:
                      .col-auto
                        .km-heading-3.q-mr-sm {{ filterObject?.row?.tool?.name }}
                  .col(v-if='filterObject?.job')
                    .row.q-gap-12.no-wrap.items-baseline
                      .col-auto
                        .km-field.text-secondary-text Test set:
                      .col-auto
                        .km-heading-3.q-mr-sm {{ filterObject?.row?.test_sets?.[0] }}
              .col.q-ml-md
                q-chip.km-small-chip(
                  color='in-progress',
                  text-color='text-gray',
                  :label='filterObject.row?.type === "prompt_eval" ? "Prompt Template" : "RAG"'
                )
              //- .col-auto.q-ml-md
              //-   km-btn.width-100(
              //-       iconColor='icon',
              //-       hoverColor='primary',
              //-       labelClass='km-title',
              //-       icon='fas fa-scale-unbalanced-flip',
              //-       label='Comparison mode',
              //-       flat,
              //-       iconSize='14px',
              //-       hoverBg='primary-bg'
              //-       @click="compare(true)"
              //-     )
            q-separator.q-my-sm(v-if='filterObject?.row')
            .row
              template(v-if='filterObject?.row')
                km-table-new(
                  row-key='id',
                  v-model:selected='selected',
                  :columns='columnsCalc ?? []',
                  :rows='recordsCalc ?? []',
                  :visibleColumns='visibleColumnsCalc',
                  style='min-width: 1100px',
                  selection='multiple',
                  :pagination='pagination',
                  binary-state-sort,
                  :loading='loading',
                  @selectRow='selectRecord',
                  :rowKey='groupBy == "flat" ? "_id" : "groupId"',
                  :group='groupBy !== "flat"',
                  :subheader='(columnsCalc || []).find((col) => col.name === "subheader")'
                )
              template(v-else)
                km-table(
                  row-key='id',
                  :columns='columnsCalc ?? []',
                  :rows='recordsCalc ?? []',
                  :visibleColumns='visibleColumnsCalc',
                  style='min-width: 1100px',
                  selection='multiple',
                  :pagination='pagination',
                  binary-state-sort,
                  :loading='loading',
                  @selectRow='selectRecord',
                  :rowKey='groupBy == "flat" ? "_id" : "groupId"',
                  :group='groupBy !== "flat"',
                  :subheader='(columnsCalc || []).find((col) => col.name === "subheader")'
                )
        q-inner-loading(:showing='loading')
    evaluation-jobs-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Evaluation
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected Evaluation. Are you sure?` }}

km-popup-confirm(
  :visible='showRerunDialog',
  confirmButtonLabel='Run',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='rerunSelected',
  @cancel='showRerunDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Rerun Evaluation
  .row.text-center.justify-center {{ `You are going to rerun ${selected?.length} selected Evaluation. Are you sure?` }}
</template>

<script>
import { ref } from 'vue'
import _ from 'lodash'
import { useChroma } from '@shared'
import columnsByJob from '@/config/evaluation_jobs/evaluation_jobs_group_by_job'
import columnsByTool from '@/config/evaluation_jobs/evaluation_jobs_group_by_tool'

export default {
  setup() {
    const { loading, searchString, create, pagination, visibleColumns, columns, visibleRows, selectedRow, ...useCollection } =
      useChroma('evaluation_jobs')

    return {
      searchString,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      selectedRow,
      useCollection,
      create,
      createNew: ref(false),
      loading,
      selected: ref([]),
      showDeleteDialog: ref(false),
      showNewDialog: ref(false),
      showRerunDialog: ref(false),
      groupBy: ref('job'),
      groups: ref([
        { label: 'Evaluation job', value: 'job' },
        { label: 'Evaluated tool', value: 'tool' },
      ]),
      columnsByJob,
      columnsByTool,
      filterObject: ref({
        tool: '',
        job: '',
      }),
    }
  },
  computed: {
    filterObjectStartData() {
      // formatted date
      const data = this.filterObject?.row?.started_at
      const date = new Date(data)
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')

      return `${day}.${month}.${year} ${hours}:${minutes}`
    },
    formattedDate() {
      const date = new Date(this.groupedByRow?.started_at)
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')

      return `${day}.${month}.${year} ${hours}:${minutes}`
    },
    groupedByRow() {
      return this.filterObject?.row
    },
    averageScore() {
      return this.groupedByRow?.average_score
    },
    averageLatency() {
      const result = this.groupedByRow?.average_latency || 0
      return new Intl.NumberFormat(undefined, {
        style: 'unit',
        unit: 'millisecond',
        unitDisplay: 'short',
        maximumFractionDigits: 0,
      }).format(result)
    },
    recordsRated() {
      return `${this.groupedByRow?.results_with_score} of ${this.groupedByRow?.records_count}`
    },
    visibleColumnsFiltered() {
      return this.visibleColumns
    },
    groupByJobId() {
      return this.groupRecordsByKey(this.visibleRowsByType, 'job_id')
    },
    groupByJobTool() {
      return this.groupRecordsByKey(this.visibleRowsByType, 'tool.system_name')
    },
    columnsCalc() {
      if (this.groupBy == 'job') {
        return Object.values(this.columnsByJob).sort((a, b) => a.columnNumber - b.columnNumber)
      } else if (this.groupBy == 'tool') {
        return Object.values(this.columnsByTool).sort((a, b) => a.columnNumber - b.columnNumber)
      } else {
        return this.columns
      }
    },
    visibleColumnsCalc() {
      if (this.groupBy == 'job') {
        return Object.values(this.columnsByJob)
          .sort((a, b) => a.columnNumber - b.columnNumber)
          .filter(({ display }) => display)
          .map(({ name }) => name)
      } else if (this.groupBy == 'tool') {
        return Object.values(this.columnsByTool)
          .sort((a, b) => a.columnNumber - b.columnNumber)
          .filter(({ display }) => display)
          .map(({ name }) => name)
      } else {
        return this.visibleColumns
      }
    },
    recordsCalc() {
      let records = []
      if (this.groupBy == 'job') {
        records = this.groupByJobId
      } else if (this.groupBy == 'tool') {
        records = this.groupByJobTool
      } else {
        records = this.visibleRowsByType
      }

      records = records.filter((record) => {
        if (this.filterObject.tool) {
          return record.tool.system_name == this.filterObject.tool
        }

        if (this.filterObject.job) {
          return record.job_id == this.filterObject.job
        }

        return true
      })

      return records
    },

    routerQuery() {
      return this.$route.query
    },
    paramId() {
      return this.$route.params.id
    },
    visibleRowsByType() {
      return this.visibleRows
    },
  },

  mounted() {
    if (!this.routerQuery?.job_id) return

    this.groupBy = this.routerQuery?.job_id ? 'flat' : 'job'

    this.filterObject = {
      job: this.routerQuery?.job_id || '',
      row: this.recordsCalc.find((record) => record.groupId == this.routerQuery?.job_id),
    }
  },
  methods: {
    async getEvalutionReport() {
      let ids = this.selected.map((obj) => obj._id)
      await this.$store.dispatch('generateEvaluationReport', { ids })
    },
    compare(all = false) {
      const ids = all ? this.recordsCalc?.map((obj) => obj._id) : this.selected.map((obj) => obj._id)
      this.$router.push({
        name: 'EvaluationCompare',
        query: { ids: ids.join(',') },
      })
    },
    groupRecordsByKey(data, key) {
      return _.chain(data)
        .groupBy(key)
        .map((records, groupKeyId) => {
          return {
            groupId: groupKeyId,
            groupKey: key,
            average_cached_tokens: _.mean(records.map((record) => record.average_cached_tokens)),
            average_completion_tokens: _.mean(records.map((record) => record.average_completion_tokens)),
            average_latency: _.mean(records.map((record) => record.average_latency)),
            average_prompt_tokens: _.mean(records.map((record) => record.average_prompt_tokens)),
            average_score: _.mean(records.map((record) => record.average_score).filter((score) => score > 0)),
            records_count: _.sum(records.map((record) => record.records_count)),
            results_with_score: _.sum(records.map((record) => record.results_with_score)),
            started_at: _.min(records.map((record) => new Date(record.started_at))),
            type: _.first(records).type,
            tool: _.first(records).tool,
            tools: _.uniqBy(
              records.map((record) => record.tool),
              'variant_name'
            ),
            test_sets: _.uniq(_.flatten(records.map((record) => record.test_sets))),
            max_score_tool: _.maxBy(records, 'average_score'),
            records: records,
          }
        })
        .value()
    },

    async deleteSelected() {
      await Promise.all(
        this.selected.map(async (obj) => {
          await this.useCollection.delete({ id: obj._id })
        })
      )

      this.selected = []
      await this.useCollection.get()
      this.showDeleteDialog = false
    },

    rerunSelected() {
      this.selected.forEach(async (obj) => {
        if (!obj?.evaluation_set?.system_name || (obj?.evaluated_tools?.length || 0) == 0) return

        const evaluation_set = obj.evaluation_set.system_name
        const iteration_count = Math.max(obj.result_items.map((item) => item.iteration)) || 1
        const evaluation_target_tools = obj.evaluated_tools.map((tool) => tool?.system_name || tool?.system_name)

        const params = {
          evaluation_set,
          iteration_count,
          evaluation_target_tools,
        }
        await this.create(JSON.stringify(params))
      })

      this.get()

      this.selected = []
      this.showRerunDialog = false
    },

    openNewDetails() {
      this.showNewDialog = true
    },

    removeFilter() {
      if (this.filterObject.tool) {
        this.groupBy = 'tool'
      }

      if (this.filterObject.job) {
        this.groupBy = 'job'
      }
      this.filterObject = {
        tool: '',
        job: '',
        row: null,
      }
    },
    selectRecord(row) {
      if (this.groupBy == 'flat') {
        this.openDetails(row)
      }
      if (this.groupBy == 'job') {
        this.groupBy = 'flat'
        this.filterObject.job = row.groupId
        this.filterObject.row = row
      }

      if (this.groupBy == 'tool') {
        this.groupBy = 'flat'
        this.filterObject.tool = row?.tool?.system_name
        this.filterObject.row = row
      }
    },
    async openDetails(row) {
      await this.$router.push(`/evaluation-jobs/${row._id}`)
    },
    validation(rag, notify = true) {
      const { name, description, system_name, retrieve } = rag
      const { collection_system_names } = retrieve

      if (!name || !description || !system_name || !collection_system_names.length) {
        // Handle validation error

        if (notify) {
          this.$q.notify({
            message: `Name, Description, System name and Knowledge sources are required`,
            color: 'error-text',
            position: 'top',
            timeout: 1000,
          })
        }
        return false
      }

      return true
    },
    async refreshTable() {
      this.useCollection.get()
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

<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
      km-input-flat.col.km-description.text-black.full-width(
        placeholder='Enter system system_name',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#header-actions)
    km-btn(label='Record info', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Modified:
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created by:
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text Modified by:
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='evalSetStore.revert()', v-if='evalSetStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !evalSetStore.isChanged')
    km-btn(label='Run evaluation', flat, iconSize='16px', @click='runEvaluationDialog = true')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 Clone
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 Delete
    km-popup-confirm(
      :visible='showDeleteDialog',
      confirmButtonLabel='Delete Evaluation Set',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Evaluation Set
      .row.text-center.justify-center This action will permanently delete the Evaluation Set.
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.full-height.full-width.q-my-md(style='min-height: 0')
      template(v-if='tab == "records"')
        .col(style='min-height: 0')
          evaluation-sets-records(@record:update='evaluationSetRecord')
      template(v-if='tab == "settings"')
        .col.overflow-auto
          evaluation-sets-settings
      template(v-if='tab == "postProcess"')
  template(#drawer)
    evaluation-sets-drawer(v-if='openDrawer', :open='openDrawer')
evaluation-sets-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
evaluation-jobs-create-new(
  :showNewDialog='runEvaluationDialog',
  @create='createEvaluation',
  @cancel='runEvaluationDialog = false',
  v-if='runEvaluationDialog',
  :evaluationSetCode='evaluationSetCode'
)
km-popup-confirm(
  :visible='showEvaluationCreateDialog',
  confirmButtonLabel='View Evaluation',
  notificationIcon='far fa-circle-check',
  cancelButtonLabel='Cancel',
  @cancel='showEvaluationCreateDialog = false',
  @confirm='navigateToEval'
)
  .row.item-center.justify-center.km-heading-7 Evaluation has started!
  .row.text-center.justify-center It may take some time for the Evaluation to finish.
  .row.text-center.justify-center You'll be able to view run results on the Evaluation screen.
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { useEvaluationSetDetailStore, useEvaluationSetRecordStore } from '@/stores/entityDetailStores'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const evalSetStore = useEvaluationSetDetailStore()
    const evalSetRecordStore = useEvaluationSetRecordStore()
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.evaluation_sets.useDetail(id)
    const removeMutation = queries.evaluation_sets.useRemove()
    const { mutateAsync: updateEntity } = queries.evaluation_sets.useUpdate()
    const { mutateAsync: createEntity } = queries.evaluation_sets.useCreate()

    return {
      tab: ref('records'),
      tabs: ref([
        { name: 'records', label: 'Test Set Items' },
        { name: 'settings', label: 'Settings' },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      runEvaluationDialog: ref(false),
      showEvaluationCreateDialog: ref(false),
      activeEvaluationSet: ref({}),
      prompt: ref(null),
      showInfo: ref(false),
      id,
      selectedRow,
      removeMutation,
      updateEntity,
      createEntity,
      evaluationSetRecord: ref({}),
      validSystemName,
      evalSetStore,
      evalSetRecordStore,
    }
  },
  computed: {
    openDrawer() {
      return this.tab === 'records' && Object.keys(this.evalSetRecordStore.record).length > 0
    },
    name: {
      get() {
        return this.evalSetStore.entity?.name || ''
      },
      set(value) {
        this.evalSetStore.updateProperty({ key: 'name', value })
      },
    },
    description: {
      get() {
        return this.evalSetStore.entity?.description || ''
      },
      set(value) {
        this.evalSetStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.evalSetStore.entity?.system_name || ''
      },
      set(value) {
        this.evalSetStore.updateProperty({ key: 'system_name', value })
      },
    },
    evaluationSetCode() {
      return this.evalSetStore.entity?.system_name
    },
    isEvaluationSetChanged() {
      return this.evalSetStore.isChanged
    },
    activeEvaluationSetId() {
      return this.$route.params.id
    },
    activeEvaluationSetName() {
      return this.items?.find((item) => item.id == this.activeEvaluationSetId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    loading() {
      return !this.evalSetStore.entity?.id
    },
    entity() {
      return this.evalSetStore.entity
    },
    created_at() {
      return this.entity?.created_at ? this.formatDate(this.entity.created_at) : ''
    },
    modified_at() {
      return this.entity?.updated_at ? this.formatDate(this.entity.updated_at) : ''
    },
    created_by() {
      return this.entity?.created_by || 'Unknown'
    },
    updated_by() {
      return this.entity?.updated_by || 'Unknown'
    },
  },
  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.evalSetStore.setEntity(newVal)
        this.tab = 'records'
      }
    },
  },
  mounted() {
    if (this.activeEvaluationSetId != this.evalSetStore.entity?.id) {
      this.evalSetStore.setEntity(this.selectedRow)
      this.tab = 'records'
    }
  },
  activated() {
    this.id = this.$route.params.id
    // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.activeEvaluationSetId != this.evalSetStore.entity?.id) {
      this.evalSetStore.setEntity(this.selectedRow)
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    createEvaluation(obj) {
      this.evaluationId = obj?.job_id || obj?.id
      this.showNewDialog = false
      if (this.evaluationId) this.showEvaluationCreateDialog = true
    },
    navigateToEval() {
      const query = {
        job_id: this.evaluationId,
      }
      const path = '/evaluation-jobs'
      this.$router.push({ path, query })
    },
    async save() {
      const systemNameValidation = validSystemName()(this.entity?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
        return
      }
      this.saving = true
      try {
        if (this.entity?.created_at) {
          const data = this.evalSetStore.buildPayload()
          await this.updateEntity({ id: this.entity.id, data })
        } else {
          await this.createEntity(this.entity)
        }
        this.evalSetStore.setInit()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeMutation.mutateAsync(this.$route.params.id)
      this.$emit('update:closeDrawer', null)
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Evaluation Set has been deleted.', timeout: 1000 })
      this.navigate('/evaluation-sets')
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
    },
  },
}
</script>

<style lang="stylus">

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}
</style>

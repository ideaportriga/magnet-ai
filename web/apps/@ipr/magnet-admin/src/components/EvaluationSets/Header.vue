<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRagName }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
  q-tooltip.bg-white.block-shadow
    .q-pa-sm
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created:
        .text-secondary-text.km-description {{ created_at }}
      div
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ modified_at }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')
.col-auto.text-white.q-mx-md
  km-btn(label='Run evaluation', color='primary', bg='background', iconSize='16px', @click='runEvaluationDialog = true') 
.col-auto.text-white.q-mr-md
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
  confirmButtonLabel='Delete Test Set',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteRag',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Test Set
  .row.text-center.justify-center This action will permanently delete the Test Set.

evaluation-sets-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
//- evaluation-jobs-create-new(v-if="runEvaluationDialog" :showNewDialog="runEvaluationDialog" @cancel="runEvaluationDialog = false", :evaluationSetCode="evaluationSetCode")
evaluation-jobs-create-new(
  :showNewDialog='runEvaluationDialog',
  @create='createEvaluation',
  @cancel='runEvaluationDialog = false',
  v-if='runEvaluationDialog',
  :evaluationSetCode='evaluationSetCode'
)
//- TODO: Add a new component for this (same as in Configuration/Drawer.vue)
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
  .row.text-center.justify-center You’ll be able to view run results on the Evaluation screen.
q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'

export default {
  props: ['activeRagTool'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('evaluation_sets')

    return {
      items,
      update,
      create,
      selectedRow,
      useCollection,
      loading: ref(false),
      showNewDialog: ref(false),
      runEvaluationDialog: ref(false),
      showDeleteDialog: ref(false),
    }
  },

  computed: {
    evaluationSetCode() {
      return this.$store.getters.evaluation_set?.system_name
    },
    created_at() {
      if (!this.activeRagDB.created_at) return ''
      return `${this.formatDate(this.activeRagDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRagDB.updated_at) return ''
      return `${this.formatDate(this.activeRagDB.updated_at)}`
    },
    currentRag() {
      return this.$store.getters.evaluation_set
    },
    route() {
      return this.$route
    },
    activeRagId() {
      return this.$route.params.id
    },
    activeRagDB() {
      return this.items.find((item) => item.id == this.activeRagId)
    },
    activeRagName: {
      get() {
        return this.activeRagDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.name, value: item }))
    },
  },
  methods: {
    createEvaluation(obj) {
      console.log('obj', obj)
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
    deleteRag() {
      this.loadingDelelete = true
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Evaluatuin set has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/evaluation-sets')
    },
    async openDetails(row) {
      await this.$router.push(`/evaluation-sets/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      this.loading = true
      if (this.currentRag?.created_at) {
        const obj = { ...this.currentRag }
        delete obj.created_at
        delete obj.id
        await this.update({ id: this.currentRag.id, data: obj })
      } else {
        await this.create(this.currentRag)
      }
      this.$store.commit('setInitEvaluationSet')
      this.loading = false
    },

    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
}
</script>

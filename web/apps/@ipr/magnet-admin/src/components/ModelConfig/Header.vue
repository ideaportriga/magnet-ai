<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRetrievalName }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
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
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save', :loading='loading', :disable='loading')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete

model-config-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy, :type='type')

km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Model',
  notificationIcon='fas fa-circle-info',
  cancelButtonLabel='Cancel',
  @cancel='showDeleteDialog = false',
  @confirm='deleteRecord'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Model
  .row.text-center.justify-center If any of your Prompt Templates are using this model, please
  .row.text-center.justify-center change it to another one, otherwise affected Prompt Templates
  .row.text-center.justify-center will stop working.

q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { validSystemName } from '@shared/utils/validationRules'
import { ref } from 'vue'

export default {
  props: ['activeRetrievalTool'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('model')

    return {
      items,
      update,
      create,
      selectedRow,
      useCollection,
      loading: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
    }
  },
  computed: {
    created_at() {
      if (!this.activeRetrievalDB?.created_at) return ''
      return `${this.formatDate(this.activeRetrievalDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRetrievalDB?.updated_at) return ''
      return `${this.formatDate(this.activeRetrievalDB.updated_at)}`
    },
    created_by() {
      if (!this.activeRetrievalDB?.created_by) return 'Unknown'
      return `${this.activeRetrievalDB?.created_by}`
    },
    updated_by() {
      if (!this.activeRetrievalDB?.updated_by) return 'Unknown'
      return `${this.activeRetrievalDB?.updated_by}`
    },
    currentModel() {
      return this.$store.getters['modelConfig/entity']
    },
    route() {
      return this.$route
    },
    activeRetrievalId() {
      return this.$route.params.id
    },
    activeRetrievalDB() {
      return this.items.find((item) => item.id == this.activeRetrievalId)
    },
    type() {
      return this.activeRetrievalDB?.type
    },
    activeRetrievalName: {
      get() {
        return this.activeRetrievalDB?.display_name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.display_name, value: item }))
    },
  },
  watch: {},
  created() {},

  methods: {
    deleteRecord() {
      this.loading = true
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Model has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/model')
      this.showDeleteDialog = false
    },
    async openDetails(row) {
      await this.$router.push(`/model/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentModel?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: systemNameValidation,
          timeout: 3000,
        })
        return
      }

      this.loading = true
      try {
        if (this.currentModel?.created_at) {
          const obj = { ...this.currentModel }

          // Удаляем метаданные и audit поля - они управляются на бэкенде
          delete obj._metadata
          delete obj.created_at
          delete obj.updated_at
          delete obj.created_by
          delete obj.updated_by

          // Удаляем лишние поля
          delete obj.name
          delete obj.category

          await this.update({ id: this.currentModel.id, data: JSON.stringify(obj) })
        } else {
          const obj = { ...this.currentModel }
          delete obj.id
          delete obj._metadata
          delete obj.created_at
          delete obj.updated_at
          delete obj.created_by
          delete obj.updated_by
          delete obj.name
          delete obj.category

          await this.create(JSON.stringify(obj))
        }
        this.$store.commit('modelConfig/setInitEntity')
        this.$q.notify({
          position: 'top',
          color: 'positive',
          message: 'Saved successfully',
          timeout: 2000,
        })
      } catch (error) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: error.message || 'Failed to save',
          timeout: 3000,
        })
      } finally {
        this.loading = false
      }
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

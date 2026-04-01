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
        placeholder='Enter system name',
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='modelConfigStore.revert()', v-if='modelConfigStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !modelConfigStore.isChanged')
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
  template(#content)
    .column.full-height(style='min-height: 0')
      km-tabs(v-model='tab')
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
      .col.overflow-auto.q-mt-lg.q-pr-16(style='min-height: 0')
        template(v-if='tab == "model"')
          model-config-model
        template(v-if='tab == "pricing"')
          model-config-pricing
model-config-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy, :type='type')
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { useModelConfigDetailStore } from '@/stores/entityDetailStores'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const modelConfigStore = useModelConfigDetailStore()
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.model.useDetail(id)
    const { data: listData } = queries.model.useList()
    const { mutateAsync: updateEntity } = queries.model.useUpdate()
    const { mutateAsync: createEntity } = queries.model.useCreate()
    const { mutateAsync: removeEntity } = queries.model.useRemove()
    const items = computed(() => listData.value?.items ?? [])

    return {
      modelConfigStore,
      tab: ref('model'),
      tabs: ref([
        { name: 'model', label: 'Settings' },
        { name: 'pricing', label: 'Pricing' },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeEntity: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      id,
      selectedRow,
      items,
      updateEntity,
      createEntity,
      removeEntity,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.modelConfigStore.entity?.display_name || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'display_name', value })
      },
    },
    description: {
      get() {
        return this.modelConfigStore.entity?.description || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.modelConfigStore.entity?.system_name || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'system_name', value })
      },
    },
    currentModel() {
      return this.modelConfigStore.entity
    },
    activeEntityId() {
      return this.$route.params?.id
    },
    activeRetrievalDB() {
      return this.items.find((item) => item.id == this.activeEntityId)
    },
    type() {
      return this.activeRetrievalDB?.type
    },
    loading() {
      return !this.modelConfigStore.entity?.id
    },
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
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.modelConfigStore.setEntity(newVal)
        this.tab = 'model'
      }
    },
  },
  mounted() {
    if (this.activeEntityId != this.modelConfigStore.entity?.id) {
      this.modelConfigStore.setEntity(this.selectedRow)
      this.tab = 'model'
    }
  },
  activated() {
    this.id = this.$route.params.id
    // Re-sync store state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.activeEntityId != this.modelConfigStore.entity?.id) {
      this.modelConfigStore.setEntity(this.selectedRow)
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async deleteRecord() {
      this.saving = true
      await this.removeEntity(this.$route.params.id)
      this.$emit('update:closeDrawer', null)
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Model has been deleted.', timeout: 1000 })
      this.navigate('/model')
      this.showDeleteDialog = false
      this.saving = false
    },
    async save() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentModel?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
        return
      }

      this.saving = true
      try {
        if (this.currentModel?.created_at) {
          const data = this.modelConfigStore.buildPayload()
          // Remove extra fields specific to model config
          delete data._metadata
          delete data.name
          delete data.category

          await this.updateEntity({ id: this.currentModel.id, data })
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

          await this.createEntity(obj)
        }
        this.modelConfigStore.setInit()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
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

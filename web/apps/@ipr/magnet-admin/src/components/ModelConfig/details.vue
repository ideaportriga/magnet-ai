<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(:placeholder='m.common_description()', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.text-black.full-width(
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='saveEntity', :loading='saving', :disable='saving || !isDirty')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_model() })',
      notificationIcon='fas fa-circle-info',
      :cancelButtonLabel='m.common_cancel()',
      @cancel='showDeleteDialog = false',
      @confirm='deleteRecord'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_model() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_modelBody() }}
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
model-config-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy, :copyData='draft', :type='type')
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, updateFields, save, revert, refetch, remove, buildPayload } = useEntityDetail('model')
    const { data: listData } = queries.model.useList()
    const { mutateAsync: removeEntity } = queries.model.useRemove()
    const items = computed(() => listData.value?.items ?? [])

    return {
      draft,
      isLoading,
      isDirty,
      updateField,
      updateFields,
      save,
      revert,
      refetch,
      buildPayload,
      m,
      tab: ref('model'),
      tabs: ref([
        { name: 'model', label: m.common_settings() },
        { name: 'pricing', label: m.common_pricing() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeEntity: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      items,
      removeEntity,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.draft?.display_name || ''
      },
      set(value) {
        this.updateField('display_name', value)
      },
    },
    description: {
      get() {
        return this.draft?.description || ''
      },
      set(value) {
        this.updateField('description', value)
      },
    },
    system_name: {
      get() {
        return this.draft?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    currentModel() {
      return this.draft
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
      return !this.draft?.id
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
    async saveEntity() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentModel?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
        return
      }

      this.saving = true
      try {
        await this.save()
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

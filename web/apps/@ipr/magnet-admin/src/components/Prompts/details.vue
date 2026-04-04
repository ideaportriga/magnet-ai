<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(:placeholder='m.common_description()', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.full-width.text-black(
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
    q-separator.q-mt-8
    .row.items-center.q-pt-8.q-gap-4
      .km-input-label.q-pl-6.text-secondary-text {{ m.common_category() }}
      km-select-flat(:placeholder='m.label_apiProvider()', :options='categoryOptions', v-model='category', showLabel)
  template(#subheader)
    prompts-sub-header
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
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='composableRevert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !isDirty')
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
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_promptTemplate() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_promptTemplate() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_promptTemplate() }) }}
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.items-center.full-height.full-width.q-gap-16.overflow-auto
            template(v-if='true')
              .col-auto.full-width
                template(v-if='tab == "promptTemplate"')
                  prompts-prompttemplate
                template(v-if='tab == "advancedSettings"')
                  prompts-advancedsettings
                template(v-if='tab == "responseFormat"')
                  prompts-responseformat
                template(v-if='tab == "sapmles"')
                  prompts-sampleinput
                template(v-if='tab == "testSets"')
                  prompts-test-sets
  template(#drawer)
    prompts-drawer(v-model:open='openTest')
prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { categoryOptions } from '@/config/prompts/prompts'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { ref } from 'vue'
import { validSystemName } from '@/utils/validationRules'
import { m } from '@/paraglide/messages'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, setSelectedVariant,
            save, revert, remove, refetch, buildPayload } = useVariantEntityDetail('promptTemplates')
    const removeMutation = queries.promptTemplates.useRemove()
    return {
      draft,
      isLoading,
      isDirty,
      updateField,
      setSelectedVariant,
      composableSave: save,
      composableRevert: revert,
      composableRemove: remove,
      refetch,
      buildPayload,
      m,
      tab: ref('promptTemplate'),
      tabs: ref([
        { name: 'promptTemplate', label: m.common_promptTemplate() },
        { name: 'advancedSettings', label: m.common_modelSettings() },
        { name: 'responseFormat', label: m.common_responseFormat() },
        { name: 'sapmles', label: m.common_notes() },
        { name: 'testSets', label: m.common_testSets() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      openTest: ref(true),
      showInfo: ref(false),
      removeMutation,
      categoryOptions,
      validSystemName,
    }
  },
  computed: {
    category: {
      get() {
        return this.draft?.category || ''
      },
      set(value) {
        this.updateField('category', value.value)
      },
    },
    name: {
      get() {
        return this.draft?.name || ''
      },
      set(value) {
        this.updateField('name', value)
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
    activePromptTemplateId() {
      return this.$route.params.id
    },
    loading() {
      return !this.draft?.id
    },
    entity() {
      return this.draft
    },
    created_at() {
      return this.entity?.created_at ? this.formatDate(this.entity.created_at) : ''
    },
    modified_at() {
      return this.entity?.updated_at ? this.formatDate(this.entity.updated_at) : ''
    },
    created_by() {
      return this.entity?.created_by || m.common_unknown()
    },
    updated_by() {
      return this.entity?.updated_by || m.common_unknown()
    },
  },

  mounted() {
    if (this.$route.query?.variant) {
      this.setSelectedVariant(this.$route.query?.variant)
    }
  },
  activated() {
    // refetch handles re-sync on KeepAlive reactivation
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      const systemNameValidation = validSystemName()(this.entity?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
        return
      }
      this.saving = true
      try {
        await this.composableSave()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: m.notify_savedSuccessfully(), timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || m.notify_failedToSave(), timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeMutation.mutateAsync(this.$route.params.id)
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        color: 'green-9',
        textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: m.notify_entityDeleted({ entity: m.entity_promptTemplate() }),
        timeout: 1000,
      })
      this.navigate('/prompt-templates')
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

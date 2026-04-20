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
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
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
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_assistantTool() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_assistantTool() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_assistantTool() }) }}
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
                template(v-if='tab == "general" && type == "api"')
                  assistant-tools-general-api
                template(v-else-if='tab == "general" && type == "rag"')
                  assistant-tools-general-rag
  template(#drawer)
    assistant-tools-drawer(v-model:open='openTest')
assistant-tools-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, save, revert, remove } = useEntityDetail('assistant_tools')
    const { data: listData } = queries.assistant_tools.useList()
    const items = computed(() => listData.value?.items ?? [])

    return {
      m,
      isLoading,
      tab: ref('general'),
      tabs: ref([{ name: 'general', label: m.common_general() }]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeAssistantTool: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      items,
      validSystemName,
      draft,
      isDirty,
      updateField,
      save,
      revert,
      remove,
    }
  },
  computed: {
    type() {
      return this.draft?.type || ''
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
    currentAssistantTool() {
      return this.draft
    },
    activeAssistantToolId() {
      return this.$route.params.id
    },
    activeAssistantToolDB() {
      return this.items.find((item) => item.id == this.activeAssistantToolId)
    },
    activeAssistantToolName() {
      return this.items?.find((item) => item.id == this.activeAssistantToolId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
    created_at() {
      if (!this.activeAssistantToolDB?.created_at) return ''
      return `${this.formatDate(this.activeAssistantToolDB.created_at)}`
    },
    modified_at() {
      if (!this.activeAssistantToolDB?.updated_at) return ''
      return `${this.formatDate(this.activeAssistantToolDB.updated_at)}`
    },
    created_by() {
      if (!this.activeAssistantToolDB?.created_by) return 'Unknown'
      return `${this.activeAssistantToolDB?.created_by}`
    },
    updated_by() {
      if (!this.activeAssistantToolDB?.updated_by) return 'Unknown'
      return `${this.activeAssistantToolDB?.updated_by}`
    },
  },

  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async confirmDelete() {
      await this.remove()
      this.$emit('update:closeDrawer', null)
      notify.success('Assistant Tool has been deleted.')
      this.navigate('/assistant-tools')
    },
    async handleSave() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentAssistantTool?.system_name)
      if (systemNameValidation !== true) {
        notify.error(systemNameValidation)
        return
      }

      this.saving = true
      try {
        const result = await this.save()
        if (result.success) {
          notify.success('Saved successfully')
        } else if (result.error) {
          throw result.error
        }
      } catch (error) {
        notify.error(error.message || 'Failed to save')
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

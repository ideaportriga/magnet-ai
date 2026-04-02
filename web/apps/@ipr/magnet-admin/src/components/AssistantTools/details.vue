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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
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
      confirmButtonLabel='Delete Assistant Tool',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Assistant Tool
      .row.text-center.justify-center This action will permanently delete the Assistant Tool and disable it in all tools that are using it.
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
import { validSystemName } from '@shared/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isDirty, updateField, save, revert, remove } = useEntityDetail('assistant_tools')
    const { data: listData } = queries.assistant_tools.useList()
    const items = computed(() => listData.value?.items ?? [])

    return {
      tab: ref('general'),
      tabs: ref([{ name: 'general', label: 'General' }]),
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
      return !this.draft?.id
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
      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'Assistant Tool has been deleted.',
        timeout: 1000,
      })
      this.navigate('/assistant-tools')
    },
    async handleSave() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentAssistantTool?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: systemNameValidation,
          timeout: 3000,
        })
        return
      }

      this.saving = true
      try {
        const result = await this.save()
        if (result.success) {
          this.$q.notify({
            color: 'green-9', textColor: 'white',
            icon: 'check_circle',
            group: 'success',
            message: 'Saved successfully',
            timeout: 2000,
          })
        } else if (result.error) {
          throw result.error
        }
      } catch (error) {
        this.$q.notify({
          color: 'red-9', textColor: 'white',
          icon: 'error',
          group: 'error',
          message: error.message || 'Failed to save',
          timeout: 3000,
        })
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

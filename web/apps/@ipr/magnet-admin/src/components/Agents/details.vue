<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading', :noHeader='$route?.name !== "AgentDetail"', :noContentWrapper='$route?.name !== "AgentDetail"')
  template(#header)
    template(v-if='$route?.name === "AgentDetail"')
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
  template(#subheader)
    agents-sub-header
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
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_agent() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_agent() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_agentBody() }}
  template(#content)
    //- Child routes (topic/action) render their own content
    router-view(v-if='$route?.name !== "AgentDetail"')
    //- Agent detail tabs (only on AgentDetail route)
    template(v-if='$route?.name === "AgentDetail"')
      km-tabs(v-model='tab')
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
      .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
        .row.q-gap-16.full-height.full-width
          .col.full-height.full-width
            .column.items-center.full-height.full-width.q-gap-16.overflow-auto
              template(v-if='true')
                .col-auto.full-width
                  template(v-if='tab == "topics"')
                    agents-topics
                  template(v-if='tab == "post-processing"')
                    agents-post-processing
                  template(v-if='tab == "settings"')
                    agents-settings
                  template(v-if='tab == "conversations"')
                    agents-conversations
                  template(v-if='tab == "notes"')
                    agents-notes
                  template(v-if='tab == "testSets"')
                    agents-test-sets
                  template(v-if='tab == "channels"')
                    agents-channels
  template(#drawer)
    agents-drawer
agents-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { validSystemName } from '@shared/utils/validationRules'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const { draft, isLoading, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            activeTopic, conversationId,
            updateHighLevelNestedProperty, updateNestedListItemBySystemName,
            save: saveEntity, revert, remove: removeEntity, refetch, buildPayload, testSetItem } = useAgentEntityDetail()

    return {
      m,
      draft,
      isDirty,
      updateField,
      saveEntity,
      revert,
      removeEntity,
      setSelectedVariant,
      tab: ref('topics'),
      tabs: ref([
        // { name: 'overview', label: 'Overview' },
        { name: 'topics', label: m.common_topics() },
        { name: 'post-processing', label: m.common_postProcessing() },
        // { name: 'prompts', label: 'Prompt Templates' },
        // { name: 'actions', label: 'Actions' },
        { name: 'settings', label: m.common_settings() },
        { name: 'channels', label: m.common_channels() },
        { name: 'conversations', label: m.common_conversations() },
        { name: 'notes', label: m.common_notes() },
        { name: 'testSets', label: m.common_testSets() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      showInfo: ref(false),
      validSystemName,
    }
  },
  computed: {
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
    loading() {
      return !this.draft?.system_name
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
      return this.entity?.created_by || 'Unknown'
    },
    updated_by() {
      return this.entity?.updated_by || 'Unknown'
    },
  },

  mounted() {
    if (this.$route.query?.variant) {
      this.setSelectedVariant(this.$route.query?.variant)
    }
  },
  methods: {
    changeTab(tab) {
      this.tab = tab
    },
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
        await this.saveEntity()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeEntity()
      this.$emit('update:closeDrawer', null)
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Agent deleted successfully', timeout: 1000 })
      this.navigate('/agents')
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

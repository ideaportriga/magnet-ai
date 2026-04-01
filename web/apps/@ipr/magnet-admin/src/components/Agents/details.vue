<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading', :noHeader='$route?.name !== "AgentDetail"', :noContentWrapper='$route?.name !== "AgentDetail"')
  template(#header)
    template(v-if='$route?.name === "AgentDetail"')
      km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
      km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
        km-input-flat.col.km-description.full-width.text-black(
          placeholder='Enter system name',
          :modelValue='system_name',
          @change='system_name = $event',
          @focus='showInfo = true',
          @blur='showInfo = false',
          :rules='[validSystemName()]'
        )
        .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#subheader)
    agents-sub-header
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='agentStore.revert()', v-if='agentStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !agentStore.isChanged')
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
      confirmButtonLabel='Delete Agent',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Agent
      .row.text-center.justify-center Deleting the Agent will also permanently delete its Topics with their interactions.
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
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { useAgentDetailStore } from '@/stores/agentDetailStore'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    // Stable ref: does NOT reactively track the global route — only updated in activated()
    // so keep-alive cached instances don't fire requests when another tab is opened.
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.agents.useDetail(id)
    const { data: listData } = queries.agents.useList()
    const removeMutation = queries.agents.useRemove()
    const { mutateAsync: updateAgent } = queries.agents.useUpdate()
    const { mutateAsync: createAgent } = queries.agents.useCreate()
    const items = computed(() => listData.value?.items ?? [])
    const agentStore = useAgentDetailStore()
    return {
      agentStore,
      tab: ref('topics'),
      tabs: ref([
        // { name: 'overview', label: 'Overview' },
        { name: 'topics', label: 'Topics' },
        { name: 'post-processing', label: 'Post-processing' },
        // { name: 'prompts', label: 'Prompt Templates' },
        // { name: 'actions', label: 'Actions' },
        { name: 'settings', label: 'Settings' },
        { name: 'channels', label: 'Channels' },
        { name: 'conversations', label: 'Conversations' },
        { name: 'notes', label: 'Notes' },
        { name: 'testSets', label: 'Test sets' },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      showInfo: ref(false),
      items,
      selectedRow,
      removeMutation,
      updateAgent,
      createAgent,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.agentStore.entity?.name || ''
      },
      set(value) {
        this.agentStore.updateProperty({ key: 'name', value })
      },
    },
    description: {
      get() {
        return this.agentStore.entity?.description || ''
      },
      set(value) {
        this.agentStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.agentStore.entity?.system_name || ''
      },
      set(value) {
        this.agentStore.updateProperty({ key: 'system_name', value })
      },
    },
    activeAgentDetailId() {
      return this.$route.params.id
    },
    loading() {
      return !this.agentStore.entity?.system_name
    },
    entity() {
      return this.agentStore.entity
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
        this.agentStore.setEntity(newVal)
        this.tab = 'topics'
      }
    },
  },
  mounted() {
    if (this.activeAgentDetailId != this.agentStore.entity?.id) {
      this.agentStore.setEntity(this.selectedRow)
      this.tab = 'topics'
    }
    if (this.$route.query?.variant) {
      this.agentStore.setSelectedVariant(this.$route.query?.variant)
    }
  },
  activated() {
    // Sync stable id ref to current route — triggers refetch only for THIS component.
    this.id = this.$route.params.id
    // Re-sync store if the entity changed (e.g., navigated back to this tab after a different one).
    if (this.selectedRow && this.activeAgentDetailId !== this.agentStore.entity?.id) {
      this.agentStore.setEntity(this.selectedRow)
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
        if (this.entity?.created_at) {
          const data = this.agentStore.buildPayload()
          await this.updateAgent({ id: this.entity.id, data })
        } else {
          await this.createAgent(this.entity)
        }
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

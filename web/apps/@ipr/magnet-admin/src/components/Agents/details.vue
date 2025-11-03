<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      router-view 
      .full-height.q-pb-md.relative-position.q-px-md(v-if='$route?.name === "AgentDetail"')
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
            .row.items-center
              km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
            .row.items-center.q-pl-6
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input-flat.col.km-description.full-width.text-black(
                placeholder='Enter system name',
                :modelValue='system_name',
                @change='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
              .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
            agents-sub-header
        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          q-tabs.bb-border.full-width(
            v-model='tab',
            narrow-indicator,
            dense,
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs'
          )
            template(v-for='t in tabs')
              q-tab(:name='t.name', :label='t.label')

          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 360px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  template(v-if='true')
                    .col-auto.full-width
                      //- template(v-if='tab == "overview"')
                      //-   agents-overview(@changeTab='changeTab')
                      template(v-if='tab == "topics"')
                        agents-topics
                      template(v-if='tab == "post-processing"')
                        agents-post-processing
                      //- template(v-if='tab == "prompts"')
                      //-   agents-prompts
                      //- template(v-if='tab == "actions"')
                      //-   agents-actions
                      template(v-if='tab == "settings"')
                        agents-settings
                      template(v-if='tab == "conversations"')
                        agents-conversations
                      template(v-if='tab == "notes"')
                        agents-notes
                      template(v-if='tab == "testSets"')
                        agents-test-sets
                      template(v-if='tab == "agents"')
                        agents-agents-credentials
                      template(v-if='tab == "channels"')
                        agents-channels
                      

  .col-auto
    agents-drawer
  actions-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { selected, visibleRows, selectedRow, ...useCollection } = useChroma('agents')
    return {
      tab: ref('channels'),
      tabs: ref([
        // { name: 'overview', label: 'Overview' },
        { name: 'topics', label: 'Topics' },
        { name: 'post-processing', label: 'Post-processing' },
        // { name: 'prompts', label: 'Prompt Templates' },
        // { name: 'actions', label: 'Actions' },
        { name: 'settings', label: 'Settings' },
        { name: 'channels', label: 'Channels'},
        { name: 'conversations', label: 'Conversations' },
        { name: 'notes', label: 'Notes' },
        { name: 'testSets', label: 'Test sets' },
        { name: 'agents', label: 'Agents Credentials' },
      ]),
      showNewDialog: ref(false),
      activeAgentDetail: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      visibleRows,
      selectedRow,
      selected,
      useCollection,
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters.agent_detail?.name || ''
      },
      set(value) {
        this.$store.commit('updateAgentDetailProperty', { key: 'name', value })
      },
    },
    description: {
      get() {
        return this.$store.getters.agent_detail?.description || ''
      },
      set(value) {
        this.$store.commit('updateAgentDetailProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters.agent_detail?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateAgentDetailProperty', { key: 'system_name', value })
      },
    },
    activeAgentDetailId() {
      return this.$route.params.id
    },
    activeAgentDetailName() {
      return this.items?.find((item) => item.id == this.activeAgentDetailId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    loading() {
      return !this.$store?.getters?.agent_detail?.system_name
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAgentDetail', newVal)
        this.tab = 'topics'
      }
    },
  },
  mounted() {
    console.log('this.queryParam?.variant', this.queryParam?.variant)
    if (this.activeAgentDetailId != this.$store.getters.agent_detail?.id) {
      this.$store.commit('setAgentDetail', this.selectedRow)
      this.tab = 'topics'
    }
    if (this.$route.query?.variant) {
      this.$store.commit('setSelectedAgentDetailVariant', this.$route.query?.variant)
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
    deleteAgentDetail() {
      this.$q.notify({
        message: `Are you sure you want to delete ${this.selectedRow?.name}?`,
        color: 'error-text',
        position: 'top',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              this.loadingDelelete = true
              this.useCollection.delete({ id: this.selectedRow?.id })
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                position: 'top',
                message: 'Prompt has been deleted.',
                color: 'positive',
                textColor: 'black',
                timeout: 1000,
              })
              this.navigate('/prompt-templates')
            },
          },
        ],
      })
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

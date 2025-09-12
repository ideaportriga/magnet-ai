<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg
          q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
            template(v-slot:separator)
              q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize App
                .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/ai-apps/${$route.params?.id}`)') {{ selectedRow?.name }}
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Tab
                .km-chip.text-grey-8.text-capitalize {{ name }}
          //- km-btn(dense flat @click='navigate(`/ai-apps/${parentAIAppId}`)')
          //-   .row.items-center.q-gap-12.no-wrap.full-width
          //-     q-icon.col-auto(name="fas fa-chevron-left", color="text-secondary") 
          //-     .col Back to AI Tabs

        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
            .row.items-center
              km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
            .row.items-center.q-pl-6
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input-flat.col.km-description.text-black.full-width(
                placeholder='Enter system name',
                :modelValue='system_name',
                @change='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.

        .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-my-md(style='max-height: calc(100vh - 360px) !important')
          .row.q-gap-16.full-height.full-width
            .col.full-height.full-width
              template(v-if='true')
              .ba-border.bg-white.border-radius-12.q-pa-lg(style='min-width: 300px')
                .col-auto.full-width
                  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Tab type
                    |
                    .full-width.column
                      q-radio.q-my-sm(name='tab_type', dense, label='RAG Tool', val='RAG', v-model='tab_type')
                      q-radio.q-mb-sm(name='tab_type', dense, label='Retrieval Tool', val='Retrieval', v-model='tab_type')
                      q-radio.q-mb-sm(name='tab_type', dense, label='Custom', val='Custom', v-model='tab_type')
                      q-radio.q-mb-sm(name='tab_type', dense, label='Agent', val='Agent', v-model='tab_type')
                      //- .row 
                      //-   q-radio(name="tab_type" dense disable label="Agents" val="Agents" v-model="tab_type")
                      //-   q-chip.km-small-chip(
                      //-         flat
                      //-         color="primary-light"
                      //-         text-color="primary"
                      //-         label="Upcoming feature")
                  template(v-if='tab_type === "RAG"')
                    .km-field.text-secondary-text.q-pb-xs.q-pl-8 RAG Tool
                      km-select(
                        height='30px',
                        placeholder='Prompt template',
                        :options='ragToolsOptions',
                        v-model='ragToolCode',
                        hasDropdownSearch,
                        option-value='value'
                      )
                  template(v-if='tab_type === "Retrieval"')
                    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Retrieval Tool
                      km-select(
                        height='30px',
                        placeholder='Retrieval Tool',
                        :options='retrievalToolsOptions',
                        v-model='retrievalToolCode',
                        hasDropdownSearch,
                        option-value='value'
                      )
                  template(v-if='tab_type === "Custom"')
                    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Custom code
                      km-codemirror(v-model='config.jsonString', style='max-height: 600px')
                      .km-description.text-secondary-text.q-pb-4 Enter your custom code in JSON format
                  template(v-if='tab_type === "Agent"')
                    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Agent
                      km-select(
                        height='30px',
                        placeholder='Agent',
                        :options='agentsOptions',
                        v-model='agentsCode',
                        hasDropdownSearch,
                        option-value='value'
                      ) 

  .col-auto(style='width: 500px')
    ai-apps-drawer(v-model:open='openTest')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  setup() {
    const { items } = useChroma('rag_tools')
    const { selectedRow } = useChroma('ai_apps')
    const { items: agentItems } = useChroma('agents')
    const { items: retrievalItems } = useChroma('retrieval')

    return {
      retrievalItems,
      items,
      agentItems,
      activeKnowledge: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      selectedRow,
    }
  },
  computed: {
    currentTab() {
      return this.$store.getters.getTabBySystemName(this.activeAIAppTabSystemName)
    },
    name: {
      get() {
        return this.currentTab?.name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppTabProperty', { system_name: this.activeAIAppTabSystemName, newProperties: { name: value } })
      },
    },
    description: {
      get() {
        return this.currentTab?.description || ''
      },
      set(value) {
        this.$store.commit('updateAIAppTabProperty', { system_name: this.activeAIAppTabSystemName, newProperties: { description: value } })
      },
    },
    system_name: {
      get() {
        return this.currentTab?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppTabProperty', { system_name: this.activeAIAppTabSystemName, newProperties: { system_name: value } })
      },
    },
    tab_type: {
      get() {
        return this.currentTab?.tab_type || ''
      },
      set(value) {
        this.$store.commit('updateAIAppTabProperty', { system_name: this.activeAIAppTabSystemName, newProperties: { tab_type: value } })
      },
    },
    config: {
      get() {
        return this.currentTab?.config || ''
      },
      set(value) {
        this.$store.commit('updateAIAppTabProperty', { system_name: this.activeAIAppTabSystemName, newProperties: { config: value } })
      },
    },
    agentsOptions() {
      return this.agentItems.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?._metadata?.modified_at,
      }))
    },
    agentsCode: {
      get() {
        return this.agentItems.find((el) => el.system_name == this.config.agent)?.name
      },
      set(val) {
        this.config.agent = val?.value
      },
    },
    retrievalToolsOptions() {
      return this.retrievalItems.map((item) => ({
        label: item.name,
        value: item.system_name,
        modified_at: item?._metadata?.modified_at,
      }))
    },
    retrievalToolCode: {
      get() {
        return this.retrievalItems.find((el) => el.system_name == this.config.retrieval_tool)?.name
      },
      set(val) {
        this.config.retrieval_tool = val?.value
      },
    },

    activeAIAppTabSystemName() {
      return this.$route.params?.tab
    },
    parentAIAppId() {
      return this.$route.params?.id
    },
    ragToolsOptions() {
      return this.items.map((item) => ({
        label: item.name,
        value: item.system_name,
      }))
    },
    ragToolCode: {
      get() {
        return this.items.find((el) => el.system_name == this.config.rag_tool)?.name
      },
      set(val) {
        this.config.rag_tool = val?.value
      },
    },

    loading() {
      return !this.$store?.getters?.ai_app_tab?.id
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAIApp', newVal)
      }
    },
  },
  mounted() {
    this.$store.commit('setAIApp', this.selectedRow)
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
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

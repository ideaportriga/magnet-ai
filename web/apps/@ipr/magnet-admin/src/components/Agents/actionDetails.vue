<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else)
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .q-mt-lg
          q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
            template(v-slot:separator)
              q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Agent
                .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/agents/${routeParams?.id}`)') {{ agentName }}
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Topic
                .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/agents/${routeParams?.id}/topics/${routeParams.topicId}`)') {{ topicName }}
            q-breadcrumbs-el
              .column
                .km-small-chip.text-grey.text-capitalize Action
                .km-chip.text-grey-8.text-capitalize {{ name }}
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
            .row.items-center
              km-input-flat.km-description.full-width.text-black(
                placeholder='Description',
                :modelValue='description',
                @change='description = $event'
              )

        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          q-tabs.bb-border.full-width(
            v-if='tabs.length > 1',
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

          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 300px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  template(v-if='true')
                    .col-auto.full-width
                      template(v-if='tab == "general-settings"')
                        agents-action-details-general-settings
                      template(v-if='tab == "parameters"')
                        agents-action-details-parameters
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { visibleRows, selectedRow } = useChroma('agents')
    return {
      tab: ref('general-settings'),
      activeAgentDetail: ref({}),
      visibleRows,
      selectedRow,
    }
  },
  computed: {
    tabs() {
      const tabs = [{ name: 'general-settings', label: 'General Settings' }]
      if (this.action?.type == 'api') {
        tabs.push({ name: 'parameters', label: 'Parameters' })
      }
      return tabs
    },
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.routeParams?.actionId)
    },
    topicName() {
      return this.topic?.name
    },
    agentName() {
      return this.$store.getters.agent_detail?.name
    },
    agentId() {
      return this.$store.getters.agent_detail?.id
    },
    name: {
      get() {
        return this.action?.name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            name: value,
          },
        })
      },
    },
    description: {
      get() {
        return this.action?.description || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            description: value,
          },
        })
      },
    },
    system_name: {
      get() {
        return this.action?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
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
      return !this.$store?.getters?.agent_detail?.id
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAgentDetail', newVal)
        this.tab = 'general-settings'
      }
    },
  },
  mounted() {
    if (this.activeAgentDetailId != this.agentId) {
      this.$store.commit('setAgentDetail', this.selectedRow)
      this.tab = 'general-settings'
    }
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

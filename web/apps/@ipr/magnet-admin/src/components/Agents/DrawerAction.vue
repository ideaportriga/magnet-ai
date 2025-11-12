<template lang="pug">
.no-wrap.full-height(style='max-width: 500px; min-width: 500px !important')
  .row.full-height
    .col.full-height
      .column.full-height.q-pa-16.bg-white.bl-border
        .row
          km-btn(
            flat,
            simple,
            :label='`Back to Agent Preview`',
            iconSize='16px',
            icon='fas fa-arrow-left',
            @click='activeTopic = null',
            color='secondary-text'
          )
        q-separator.q-mb-sm
        .row
          q-tabs.bb-border(
            v-if='tabs.length > 1',
            v-model='tab',
            narrow-indicator,
            dense,
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs-dense'
          )
            template(v-for='t in tabs')
              q-tab(:name='t.name', :label='t.label')

        .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 220px) !important')
          .row.q-gap-16.full-height.full-width
            .col.full-height.full-width
              .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                .col-auto.full-width
                  template(v-if='tab == "general-settings"')
                    agents-action-details-general-settings-drawer
                  template(v-if='tab == "advanced-settings"')
                    agents-action-details-advanced-settings-drawer(:action='action')
                  template(v-if='tab == "parameters"')
                    agents-action-details-parameters-drawer
</template>

<script>
import { ref } from 'vue'

export default {
  setup() {
    const tab = ref('general-settings')
    return { tab }
  },
  computed: {
    activeTopic: {
      get() {
        return this.$store.getters.activeTopic
      },
      set(value) {
        this.$store.commit('setActiveTopic', value)
      },
    },
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || []).find((topic) => topic?.system_name === this.routeParams.topicId)
    },
    action() {
      return this.topic?.actions?.find((act) => act?.system_name === this.activeTopic?.action)
    },
    tabs() {
      const tabs = [
        { name: 'general-settings', label: 'General Settings' },
        { name: 'advanced-settings', label: 'Advanced Settings' },
      ]
      if (this.action?.type === 'api' || this.action?.type === 'mcp_tool') {
        tabs.push({ name: 'parameters', label: 'Parameters' })
      }
      return tabs
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

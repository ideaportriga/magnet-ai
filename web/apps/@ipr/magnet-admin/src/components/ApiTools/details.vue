<template lang="pug">
layouts-details-layout
  template(#breadcrumbs)
    .row.q-pb-md.relative-position.q-px-md
      q-breadcrumbs.text-grey(active-color='text-grey', gutter='lg')
        template(v-slot:separator)
          q-icon(size='12px', name='fas fa-chevron-right', color='text-grey')
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize API Server
            .km-chip.text-grey-8.text-capitalize.breadcrumb-link(@click='navigate(`/api-servers/${apiServer.id}`)') {{ apiServer.name }}
        q-breadcrumbs-el
          .column
            .km-small-chip.text-grey.text-capitalize API Tool
            .km-chip.text-grey-8.text-capitalize.breadcrumb-link {{ apiTool.name }}
  template(#header)
    layouts-details-header(v-model:name='name', v-model:description='description', v-model:systemName='system_name')
    //- q-separator.q-mt-8
    //- .row.items-end.q-pt-8.q-gap-4
    //-   .km-input-label.q-pl-6.text-secondary-text.q-pb-4(style='line-height: 16px') API Provider
      //- km-select-flat(placeholder='API Provider', :options='apiProviderOptions', v-model='apiProvider')

  template(#content)
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
    .column.q-gap-16.overflow-auto.q-pt-lg.q-pb-lg
      api-tools-tabs-information(v-if='tab == "information"', :apiTool='apiTool')
      api-tools-tabs-parameters(v-if='tab == "parameters"', :apiTool='apiTool', @select='selectedRow = $event', :selectedRow='selectedRow')

  template(#drawer)
    api-tools-drawer(v-model:open='openPropDetails', :selectedRow='selectedRow', ref='drawer')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { useStore } from 'vuex'
import _ from 'lodash'
export default {
  setup() {
    const { items } = useChroma('api_servers')
    const store = useStore()

    return {
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'information', label: 'API Information' },
      ]),
      items,
      openPropDetails: ref(false),
      selectedRow: ref(null),
      store,
    }
  },
  computed: {
    apiServer() {
      return this.items.find((item) => item.id === this.$route.params.id) ?? {}
    },
    apiTool() {
      return this.$store.getters.toolByName(this.$route.params.name)
    },

    name: {
      get() {
        return this.apiTool?.name || ''
      },
      set(value) {
        this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: 'name', value })
      },
    },
    description: {
      get() {
        return this.apiTool?.description || ''
      },
      set(value) {
        this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.apiTool?.system_name || ''
      },
      set(value) {
        // this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: 'system_name', value })
      },
    },
  },
  watch: {
    apiServer: {
      handler(newVal) {
        if (newVal !== this.$store.getters.api_server) {
          console.log('newVal', newVal)
          this.$store.commit('setApiServer', _.cloneDeep(newVal))
        }
      },
      deep: true,
      immediate: true,
    },
    selectedRow: {
      handler() {
        this.$refs.drawer.setTab('details')
      },
      deep: true,
    },
    tab: {
      handler(newVal) {
        this.$refs.drawer?.regulateTabs(newVal)
      },
      immediate: true,
    },
  },
  mounted() {
    // this.$store.commit('setApiServer', _.cloneDeep(this.apiTool))
    // this.$store.commit('setApiTool', _.cloneDeep(this.apiTool))
  },
  methods: {
    navigate(path) {
      this.$router.push(path)
    },
  },
}
</script>

<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
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
            .row.items-center.q-pl-6
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input-flat.col.km-description.text-black.full-width.text-black(
                placeholder='Enter system name',
                :modelValue='system_name',
                @change='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.

        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          q-tabs.bb-border.full-width(
            v-model='folderTab',
            narrow-indicator,
            dense,
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs'
          )
            template(v-for='t in folderTabs')
              q-tab(:name='t.name', :label='t.label')
          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-my-md(style='max-height: calc(100vh - 360px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  .col-auto.full-width
                    template(v-if='folderTab == "records"')
                      ai-apps-records
                    template(v-if='folderTab == "settings"')
                      ai-apps-settings

  .col-auto(style='width: 520px', v-if='tabs.length > 0')
    ai-apps-drawer(v-model:open='openTest')
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { VueDraggable } from 'vue-draggable-plus'

export default {
  components: {
    VueDraggable,
  },
  setup() {
    const { selected, visibleRows, selectedRow, ...useCollection } = useChroma('ai_apps')

    return {
      activeAIApp: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      openCreateDialog: ref(true),
      showInfo: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      visibleRows,
      selectedRow,
      selected,
      useCollection,
      searchString: ref(''),
      hovered: ref({}),
      isMoving: ref(false),
      clickedRow: ref({}),
      folderTab: ref('records'),
      folderTabs: ref([
        { name: 'records', label: 'AI Tabs' },
        { name: 'settings', label: 'Settings' },
      ]),
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters.ai_app?.name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'name', value })
      },
    },
    description: {
      get() {
        return this.$store.getters.ai_app?.description || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters.ai_app?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'system_name', value })
      },
    },
    tabs: {
      get() {
        return this.$store.getters.ai_app?.tabs || []
      },
      set(value) {
        this.$store.commit('updateAIAppProperty', { key: 'tabs', value })
      },
    },
    searchedTabs: {
      get() {
        return this.tabs.filter((tab) => tab.name.toLowerCase().includes(this.searchString.toLowerCase()))
      },
      set(value) {
        this.tabs = value
      },
    },
    activeAIAppId() {
      return this.$route.params?.id
    },
    loading() {
      return !this.$store?.getters?.ai_app?.id
    },
  },
  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setAIApp', newVal)
        this.tab = 'retrieve'
        this.$store.commit('clearSemanticSeacrhAnswers')
      }
    },
  },
  mounted() {
    if (this.activeAIAppId != this.$store.getters.ai_app?.id) {
      this.$store.commit('setAIApp', this.selectedRow)
      this.$store.commit('clearSemanticSeacrhAnswers')
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openTabDetails(row) {
      console.log(row)
      this.$store.commit('setAIAppTab', row)
      this.navigate(`${this.$route.path}/items/${row.system_name}`)
    },
  },
}
</script>

<style lang="stylus">
.gradient {
  background: linear-gradient(121.5deg, #6840C2 9.69%, #E30052 101.29%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}

.card-hover:hover  {
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
}
</style>

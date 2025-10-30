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
              km-input-flat.col.km-description.text-black.full-width(
                placeholder='Enter system name',
                :modelValue='system_name',
                @change='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
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
          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='max-height: calc(100vh - 300px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.full-height.full-width.q-gap-16.overflow-auto.no-wrap
                  collections-generalinfo(v-if='tab == "settings"')
                  collections-metadata-page(v-if='tab == "metadata"')
                  collections-chunks(v-if='tab == "chunks"', :selectedRow='selectedChunk', @selectRow='selectedChunk = $event')
                  collections-scheduler(v-if='tab == "scheduler"')

  .col-auto
    collections-metadata-drawer(v-if='tab == "metadata" && activeMetadataConfig')
    collection-items-drawer(v-else-if='tab == "chunks" && selectedChunk', :selectedRow='selectedChunk', @close='selectedChunk = null')
    collections-drawer(v-else)
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  setup() {
    const { selected, visibleRows, selectedRow, ...useCollection } = useChroma('collections')
    const { ...useDocuments } = useChroma('documents')
    const tabs = ref([
    { name: 'chunks', label: 'Chunks' },  
    { name: 'metadata', label: 'Metadata' },
    { name: 'settings', label: 'Settings' },
      { name: 'scheduler', label: 'Schedule & Runs' },
    ])
    const tab = ref('chunks')
    return {
      activeKnowledge: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      visibleRows,
      selectedRow,
      selected,
      useCollection,
      tabs,
      tab,
      useDocuments,
      selectedChunk: ref(null),
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters.knowledge?.name || ''
      },
      set(value) {
        this.$store.commit('updateKnowledge', { name: value })
      },
    },
    description: {
      get() {
        return this.$store.getters.knowledge?.description || ''
      },
      set(value) {
        this.$store.commit('updateKnowledge', { description: value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters.knowledge?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateKnowledge', { system_name: value })
      },
    },

    activeKnowledgeId() {
      return this.$route.params?.id
    },
    activeKnowledgeName() {
      return this.items?.find((item) => item?.id == this.activeKnowledgeId)?.name
    },
    activeMetadataConfig() {
      return this.$store.getters.activeMetadataConfig
    },
    options() {
      return this.items?.map((item) => item?.name)
    },
    loading() {
      return !this.$store?.getters?.knowledge?.id
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('setKnowledge', newVal)
        this.$store.commit('clearSemanticSeacrhAnswers')
      }
    },
  },
  mounted() {
    if (this.activeKnowledgeId != this.$store.getters.knowledge?.id) {
      this.$store.commit('setKnowledge', this.selectedRow)
      this.$store.commit('clearSemanticSeacrhAnswers')
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

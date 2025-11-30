<template lang="pug">
.row.no-wrap.overflow-hidden.full-height(v-if='loading', style='min-width: 1200px')
  q-inner-loading(:showing='loading')
    q-spinner-gears(size='50px', color='primary')
.row.no-wrap.overflow-hidden.full-height(v-else, style='min-width: 1200px')
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
          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg.q-pr-16(style='max-height: calc(100vh - 300px) !important')
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  .col-auto.full-width
                    template(v-if='tab == "model"')
                      model-config-model
                    template(v-if='tab == "pricing"')
                      model-config-pricing

  model-config-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { selectedRow, ...useCollection } = useChroma('model')
    return {
      tab: ref('model'),
      tabs: ref([
        { name: 'model', label: 'Settings' },
        { name: 'pricing', label: 'Pricing' },
      ]),
      showNewDialog: ref(false),
      activeEntity: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      selectedRow,
      useCollection,
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters['modelConfig/entity']?.display_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'display_name', value })
      },
    },
    description: {
      get() {
        return this.$store.getters['modelConfig/entity']?.description || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.$store.getters['modelConfig/entity']?.system_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'system_name', value })
      },
    },
    activeEntityId() {
      return this.$route.params?.id
    },
    loading() {
      return !this.$store?.getters['modelConfig/entity']?.id
    },
  },

  watch: {
    selectedRow(newVal, oldVal) {
      if (newVal?.id !== oldVal?.id) {
        this.$store.commit('modelConfig/setEntity', newVal)
        this.tab = 'model'
      }
    },
  },
  mounted() {
    if (this.activeEntityId != this.$store.getters['modelConfig/entity']?.id) {
      this.$store.commit('modelConfig/setEntity', this.selectedRow)
      this.tab = 'model'
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    deleteEntity() {
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
                message: 'Item has been deleted.',
                color: 'positive',
                textColor: 'black',
                timeout: 1000,
              })
              this.navigate('/modelConfig')
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

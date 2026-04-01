<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(placeholder='Description', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
      km-input-flat.col.km-description.full-width(
        placeholder='Enter system name',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
  template(#subheader)
    retrieval-sub-header
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='retrievalStore.revert()', v-if='retrievalStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !retrievalStore.isChanged')
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
      confirmButtonLabel='Delete Retrieval Tool',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Retrieval Tool
      .row.text-center.justify-center This action will permanently delete the Retrieval Tool and disable it in all tools that are using it.
  template(#content)
    km-tabs(v-model='tab')
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
    .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-mb-md.q-mt-lg(style='min-height: 0')
      .row.q-gap-16.full-height.full-width
        .col.full-height.full-width
          .column.items-center.full-height.full-width.q-gap-16.overflow-auto
            template(v-if='true')
              .col-auto.full-width
                template(v-if='tab == "retrieve"')
                  retrieval-retrieve
                template(v-if='tab == "uiSettings"')
                  retrieval-uisettings
                template(v-if='tab == "languages"')
                  retrieval-languages
                template(v-if='tab == "testSets"')
                  retrieval-test-sets
  template(#drawer)
    retrieval-drawer(v-model:open='openTest')
retrieval-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { useRetrievalDetailStore } from '@/stores/entityDetailStores'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const retrievalStore = useRetrievalDetailStore()
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.retrieval.useDetail(id)
    const { data: listData } = queries.retrieval.useList()
    const removeMutation = queries.retrieval.useRemove()
    const { mutateAsync: updateEntity } = queries.retrieval.useUpdate()
    const { mutateAsync: createEntity } = queries.retrieval.useCreate()

    return {
      retrievalStore,
      tab: ref('retrieve'),
      tabs: ref([
        { name: 'retrieve', label: 'Retrieve' },
        { name: 'languages', label: 'Language' },
        { name: 'uiSettings', label: 'UI Settings' },
        { name: 'testSets', label: 'Test sets' },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeRetrieval: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      showInfo: ref(false),
      id,
      selectedRow,
      listData,
      removeMutation,
      updateEntity,
      createEntity,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.retrievalStore.entity?.name || ''
      },
      set(value) {
        this.retrievalStore.updateProperty({ key: 'name', value })
      },
    },
    description: {
      get() {
        return this.retrievalStore.entity?.description || ''
      },
      set(value) {
        this.retrievalStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.retrievalStore.entity?.system_name || ''
      },
      set(value) {
        this.retrievalStore.updateProperty({ key: 'system_name', value })
      },
    },
    activeRetrievalId() {
      return this.$route.params.id
    },
    activeRetrievalName() {
      return this.listData?.items?.find((item) => item.id == this.activeRetrievalId)?.name
    },
    options() {
      return this.listData?.items?.map((item) => item.name)
    },
    loading() {
      return !this.retrievalStore.entity?.id
    },
    entity() {
      return this.retrievalStore.entity
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
        this.retrievalStore.setEntity(newVal)
        this.tab = 'retrieve'
      }
    },
  },
  mounted() {
    if (this.activeRetrievalId != this.retrievalStore.entity?.id) {
      this.retrievalStore.setEntity(this.selectedRow)
      this.tab = 'retrieve'
    }

    if (this.$route.query?.variant) {
      this.retrievalStore.setSelectedVariant(this.$route.query?.variant)
    }
  },
  activated() {
    this.id = this.$route.params.id
    // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.activeRetrievalId != this.retrievalStore.entity?.id) {
      this.retrievalStore.setEntity(this.selectedRow)
    }
  },
  methods: {
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
          const data = this.retrievalStore.buildPayload()
          await this.updateEntity({ id: this.entity.id, data })
        } else {
          await this.createEntity(this.entity)
        }
        this.retrievalStore.setInit()
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
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Retrieval Tool has been deleted.', timeout: 1000 })
      this.navigate('/retrieval')
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

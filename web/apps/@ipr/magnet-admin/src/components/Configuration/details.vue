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
    configuration-sub-header
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='ragStore.revert()', v-if='ragStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !ragStore.isChanged')
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
      confirmButtonLabel='Delete RAG Tool',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the RAG Tool
      .row.text-center.justify-center This action will permanently delete the RAG Tool and disable it in all tools that are using it.
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
                  configuration-retrieve
                template(v-if='tab == "generate"')
                  configuration-generate
                template(v-if='tab == "postProcess"')
                  configuration-postprocess
                template(v-if='tab == "uiSettings"')
                  configuration-uisettings
                template(v-if='tab == "languages"')
                  configuration-languages
                template(v-if='tab == "testSets"')
                  configuration-test-sets
  template(#drawer)
    configuration-drawer(v-model:open='openTest')
configuration-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@shared/utils/validationRules'
import { useRagDetailStore } from '@/stores/entityDetailStores'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const ragStore = useRagDetailStore()
    // Stable ref: does NOT reactively track the global route — only updated in activated()
    // so keep-alive cached instances don't fire requests when another tab is opened.
    const id = ref(route.params.id)
    const { data: selectedRow } = queries.rag_tools.useDetail(id)
    const { data: listData } = queries.rag_tools.useList()
    const removeMutation = queries.rag_tools.useRemove()
    const { mutateAsync: updateEntity } = queries.rag_tools.useUpdate()
    const { mutateAsync: createEntity } = queries.rag_tools.useCreate()

    return {
      ragStore,
      tab: ref('retrieve'),
      tabs: ref([
        { name: 'retrieve', label: 'Retrieve' },
        { name: 'generate', label: 'Generate' },
        { name: 'languages', label: 'Language' },
        { name: 'postProcess', label: 'Post-process' },
        { name: 'uiSettings', label: 'UI Settings' },
        { name: 'testSets', label: 'Test sets' },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeRag: ref({}),
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
        return this.ragStore.entity?.name || ''
      },
      set(value) {
        this.ragStore.updateProperty({ key: 'name', value })
      },
    },
    description: {
      get() {
        return this.ragStore.entity?.description || ''
      },
      set(value) {
        this.ragStore.updateProperty({ key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.ragStore.entity?.system_name || ''
      },
      set(value) {
        this.ragStore.updateProperty({ key: 'system_name', value })
      },
    },
    activeRagId() {
      return this.$route.params.id
    },
    items() {
      return this.listData?.items ?? []
    },
    activeRagName() {
      return this.items?.find((item) => item.id == this.activeRagId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
    },
    loading() {
      return !this.ragStore.entity?.id
    },
    entity() {
      return this.ragStore.entity
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
        this.ragStore.setEntity(newVal)
        this.tab = 'retrieve'
      }
    },
  },
  mounted() {
    if (this.activeRagId != this.ragStore.entity?.id) {
      this.ragStore.setEntity(this.selectedRow)
      this.tab = 'retrieve'
    }

    if (this.$route.query?.variant) {
      this.ragStore.setSelectedVariant(this.$route.query?.variant)
    }
  },
  activated() {
    // Sync stable id ref to current route — triggers refetch only for THIS component.
    this.id = this.$route.params.id
    // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.activeRagId != this.ragStore.entity?.id) {
      this.ragStore.setEntity(this.selectedRow)
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
          const data = this.ragStore.buildPayload()
          await this.updateEntity({ id: this.entity.id, data })
        } else {
          await this.createEntity(this.entity)
        }
        this.ragStore.setInit()
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
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'RAG Tool has been deleted.', timeout: 1000 })
      this.navigate('/rag-tools')
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

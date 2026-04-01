<template lang="pug">
km-inner-loading(:showing='!selectedRow')
layouts-details-layout(v-if='selectedRow', :contentContainerStyle='{ maxWidth: "1200px", margin: "0 auto" }')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
        km-input-flat.col.km-description.text-black.full-width(
          placeholder='Enter system name',
          :model-value='system_name',
          @change='system_name = $event',
          @focus='showInfo = true',
          @blur='showInfo = false'
        )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
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
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='providerStore.revert()', v-if='providerStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !providerStore.isChanged')
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
      confirmButtonLabel='Delete Knowledge Provider',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the Knowledge Provider
      .row.text-center.justify-center This action will permanently delete the Knowledge Provider and disable it in all tools that are using it.
  template(#content)
    .column.full-height(style='min-height: 0')
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
      .col(style='min-height: 0; padding-top: 16px; padding-bottom: 16px')
        knowledge-providers-knowledge-sources(v-if='tab == "knowledge-sources"')
        knowledge-providers-settings(v-if='tab == "settings"')
</template>

<script>
import { ref, computed, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { beforeRouteEnter } from '@/guards'
import { useProviderDetailStore } from '@/stores/entityDetailStores'

export default {
  beforeRouteEnter,
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const providerStore = useProviderDetailStore()
    // Stable ref: prevent keep-alive cached instance from refetching when another route's ID changes
    const id = ref(route.params.id)
    onActivated(() => { id.value = route.params.id })
    const { data: selectedRow } = queries.provider.useDetail(id)

    const { mutateAsync: updateEntity } = queries.provider.useUpdate()
    const { mutateAsync: createEntity } = queries.provider.useCreate()
    const removeMutation = queries.provider.useRemove()

    return {
      providerStore,
      updateEntity,
      createEntity,
      removeMutation,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showNewDialog: ref(false),
      tab: ref('knowledge-sources'),
      tabs: ref([
        { name: 'knowledge-sources', label: 'Knowledge Sources' },
        { name: 'settings', label: 'Settings' },
      ]),
      showInfo: ref(false),
      selectedRow,
    }
  },
  computed: {
    provider() {
      return this.providerStore.entity
    },
    name: {
      get() {
        return this.provider?.name || ''
      },
      set(value) {
        this.providerStore.updateProperty({ key: 'name', value })
      },
    },
    system_name: {
      get() {
        return this.provider?.system_name || ''
      },
      set(value) {
        this.providerStore.updateProperty({ key: 'system_name', value })
      },
    },
    created_at() {
      return this.provider?.created_at ? this.formatDate(this.provider.created_at) : ''
    },
    modified_at() {
      return this.provider?.updated_at ? this.formatDate(this.provider.updated_at) : ''
    },
    created_by() {
      return this.provider?.created_by || 'Unknown'
    },
    updated_by() {
      return this.provider?.updated_by || 'Unknown'
    },
  },
  watch: {
    selectedRow: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.providerStore.setEntity(newVal)
        }
      },
    },
  },
  activated() {
    // Re-sync store state when KeepAlive reactivates this component (multi-tab support)
    if (this.selectedRow && this.selectedRow.id !== this.providerStore.entity?.id) {
      this.providerStore.setEntity(this.selectedRow)
    }
  },
  methods: {
    async save() {
      this.saving = true
      try {
        if (this.provider?.created_at) {
          const data = this.providerStore.buildPayload()
          await this.updateEntity({ id: this.provider.id, data })
        } else {
          await this.createEntity(this.provider)
        }
        this.providerStore.setInit()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeMutation.mutateAsync(this.$route.params.id)
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Knowledge Provider has been deleted.', timeout: 1000 })
      this.$router.push('/knowledge-providers')
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
    },
  },
}
</script>

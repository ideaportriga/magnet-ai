<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="activeRetrievalDB?.created_at" :updated-at="activeRetrievalDB?.updated_at" :created-by="activeRetrievalDB?.created_by" :updated-by="activeRetrievalDB?.updated_by" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="saveEntity" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="model-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_model() })" notification-icon="info" :cancel-button-label="m.common_cancel()" @cancel="showDeleteDialog = false" @confirm="deleteRecord">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_model() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_modelBody() }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <div class="stack full-height" data-gap="0" style="min-block-size: 0">
        <km-tabs v-model="tab" :items="tabs" />
        <div :inert="recordReadonly" :class="recordReadonly ? 'model-readonly-zone' : null" class="flex-1 overflow-auto mt-lg pr-lg" style="min-block-size: 0">
          <template v-if="tab == &quot;model&quot;">
            <model-config-model />
          </template>
          <template v-if="tab == &quot;pricing&quot;">
            <model-config-pricing />
          </template>
        </div>
      </div>
    </template>
  </layouts-details-layout>
  <model-config-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy :copy-data="draft" :type="type" @cancel="showNewDialog = false" />
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@/utils/validationRules'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEntityAccess } from '@/composables/useEntityAccess'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, updateFields, save, revert, refetch, remove, buildPayload } = useEntityDetail('model')
    const { canCreate, canDelete, recordReadonly, provideReadonly } = useEntityAccess('model', draft)
    provideReadonly()
    const { data: listData } = queries.model.useList()
    const { mutateAsync: removeEntity } = queries.model.useRemove()
    const items = computed(() => listData.value?.items ?? [])

    return {
      draft,
      isLoading,
      isDirty,
      updateField,
      updateFields,
      save,
      revert,
      refetch,
      buildPayload,
      m,
      tab: ref('model'),
      tabs: ref([
        { value: 'model', label: m.common_settings() },
        { value: 'pricing', label: m.common_pricing() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeEntity: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      items,
      removeEntity,
      canCreate,
      canDelete,
      recordReadonly,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.draft?.display_name || ''
      },
      set(value) {
        this.updateField('display_name', value)
      },
    },
    description: {
      get() {
        return this.draft?.description || ''
      },
      set(value) {
        this.updateField('description', value)
      },
    },
    system_name: {
      get() {
        return this.draft?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    currentModel() {
      return this.draft
    },
    activeEntityId() {
      return this.$route.params?.id
    },
    activeRetrievalDB() {
      return this.items.find((item) => item.id == this.activeEntityId)
    },
    type() {
      return this.activeRetrievalDB?.type
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async deleteRecord() {
      this.saving = true
      await this.removeEntity(this.$route.params.id)
      this.$emit('update:closeDrawer', null)
      notify.success('Model has been deleted.')
      this.navigate('/model')
      this.showDeleteDialog = false
      this.saving = false
    },
    async saveEntity() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentModel?.system_name)
      if (systemNameValidation !== true) {
        notify.error(systemNameValidation)
        return
      }

      this.saving = true
      try {
        await this.save()
        notify.success('Saved successfully')
      } catch (error) {
        notify.error(error.message || 'Failed to save')
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
</style>

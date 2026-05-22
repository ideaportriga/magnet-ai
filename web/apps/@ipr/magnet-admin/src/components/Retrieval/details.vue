<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" :created-by="entity?.created_by" :updated-by="entity?.updated_by" show-record-info :readonly="recordReadonly" :field-classes="headerFieldClasses" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #subheader>
      <retrieval-sub-header />
    </template>
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="retrieval-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item v-if="!recordReadonly && entity?.id" data-test="ai-edit-btn" @select="showAiEdit = true">{{ m.aiEdit_action() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <template v-if="!recordReadonly">
            <ds-dropdown-menu-separator />
            <access-control-menu :visibility="draft?.visibility" :department-id="draft?.department_id" @update:visibility="updateField('visibility', $event)" @update:department-id="updateField('department_id', $event)" />
          </template>
          <ds-dropdown-menu-separator v-if="canDelete" />
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_retrievalTool() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_retrievalTool() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_retrievalTool() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabsWithDirty" />
      <div :inert="recordReadonly && tab !== 'history'" :class="recordReadonly && tab !== 'history' ? 'retrieval-readonly-zone' : null" class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
              <template v-if="true">
                <div class="flex-none full-width">
                  <template v-if="tab == &quot;retrieve&quot;">
                    <retrieval-retrieve />
                  </template>
                  <template v-if="tab == &quot;uiSettings&quot;">
                    <retrieval-uisettings />
                  </template>
                  <template v-if="tab == &quot;languages&quot;">
                    <retrieval-languages />
                  </template>
                  <template v-if="tab == &quot;testSets&quot;">
                    <retrieval-test-sets />
                  </template>
                  <template v-if="tab == &quot;history&quot;">
                    <entity-audit-history
                      v-if="entity?.id"
                      entity-type="retrieval_tool"
                      :entity-id="entity.id"
                      :invalidate-query-keys="historyInvalidateKeys"
                      @restored="onRestored"
                    />
                  </template>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #drawer>
      <div :inert="recordReadonly" :class="recordReadonly ? 'retrieval-readonly-zone' : null" class="full-height">
        <retrieval-drawer :open="openTest" @update:open="openTest = $event" />
      </div>
    </template>
  </layouts-details-layout>
  <retrieval-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
  <ai-edit-drawer
    v-if="entity?.id"
    v-model:open="showAiEdit"
    entity-type="retrieval_tool"
    :entity-id="entity.id"
    @apply="onAiApply"
  />
</template>

<script>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { validSystemName } from '@/utils/validationRules'
import { useEntityAccess } from '@/composables/useEntityAccess'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'
import AiEditDrawer from '@/components/shared/AiEditDrawer.vue'
import EntityAuditHistory from '@/components/shared/EntityAuditHistory.vue'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { applyAiVariantResult, setAiSaveContext } from '@/utils/aiEditMerge'
import { entityKeys } from '@/queries/queryKeys'

export default {
  components: { AiEditDrawer, EntityAuditHistory },
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            save: saveEntity, revert, refetch, buildPayload, remove } = useVariantEntityDetail('retrieval')
    const removeMutation = queries.retrieval.useRemove()

    const { canEdit, canDelete, canCreate, recordReadonly, provideReadonly } = useEntityAccess('retrieval', draft)
    provideReadonly()

    return {
      draft,
      canEdit,
      canDelete,
      canCreate,
      recordReadonly,
      isLoading,
      isDirty,
      updateField,
      updateFields,
      updateVariantField,
      selectedVariant,
      activeVariant,
      variants,
      setSelectedVariant,
      createVariant,
      deleteVariant,
      activateVariant,
      saveEntity,
      revert,
      refetch,
      buildPayload,
      remove,
      m,
      tab: ref('retrieve'),
      tabs: ref([
        { value: 'retrieve', label: m.common_retrieve() },
        { value: 'languages', label: m.common_language() },
        { value: 'uiSettings', label: m.common_uiSettings() },
        { value: 'testSets', label: m.common_testSets() },
        { value: 'history', label: m.common_history() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      showAiEdit: ref(false),
      saving: ref(false),
      activeRetrieval: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      editBuffer: useEditBufferStore(),
      removeMutation,
      validSystemName,
    }
  },
  computed: {
    name: {
      get() {
        return this.draft?.name || ''
      },
      set(value) {
        this.updateField('name', value)
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
    activeRetrievalId() {
      return this.$route.params.id
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
    entity() {
      return this.draft
    },
    historyInvalidateKeys() {
      const id = this.entity?.id
      return id
        ? [entityKeys.retrieval.detail(id), entityKeys.retrieval.lists()]
        : [entityKeys.retrieval.lists()]
    },
    headerFieldClasses() {
      if (!this.entity?.id) return {}
      const key = `retrieval:${this.entity.id}`
      const changed = this.editBuffer.getChangedPaths(key)
      const aiSuggested = this.editBuffer.getAiSuggestedPaths(key)
      const cls = (path) => ({
        'field--ai-suggested': aiSuggested.has(path),
        'field--unsaved': changed.has(path),
      })
      return {
        name: cls('name'),
        description: cls('description'),
        systemName: cls('system_name'),
      }
    },
    _activeVariantIndex() {
      const variants = this.entity?.variants
      const active = this.entity?.active_variant
      if (!Array.isArray(variants)) return -1
      return variants.findIndex((v) => v?.variant === active)
    },
    tabsWithDirty() {
      if (!this.entity?.id) return this.tabs
      const key = `retrieval:${this.entity.id}`
      const changed = this.editBuffer.getChangedPaths(key)
      if (changed.size === 0) return this.tabs
      const idx = this._activeVariantIndex
      const v = idx >= 0 ? `variants[${idx}].` : null
      const tabPathPrefixes = {
        retrieve: v ? [`${v}retrieve`] : [],
        languages: v ? [`${v}language`] : [],
        uiSettings: v ? [`${v}ui_settings`] : [],
      }
      const arr = [...changed]
      const isDirty = (prefixes) =>
        prefixes.some((p) =>
          arr.some((path) => path === p || path.startsWith(`${p}.`) || path.startsWith(`${p}[`)),
        )
      return this.tabs.map((t) => {
        const prefixes = tabPathPrefixes[t.value]
        return prefixes && prefixes.length ? { ...t, dirty: isDirty(prefixes) } : t
      })
    },
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
        notify.error(systemNameValidation)
        return
      }
      this.saving = true
      try {
        if (this.entity?.id) {
          setAiSaveContext(this.editBuffer, `retrieval:${this.entity.id}`, 'retrieval_tools', this.entity.id)
        }
        await this.saveEntity()
        notify.success(m.notify_savedSuccessfully())
      } catch (error) {
        notify.error(error.message || m.notify_failedToSave())
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeMutation.mutateAsync(this.$route.params.id)
      this.$emit('update:closeDrawer', null)
      notify.success(m.notify_entityDeleted({ entity: m.entity_retrievalTool() }))
      this.navigate('/retrieval')
    },
    async onRestored() {
      try {
        await this.refetch?.()
      } catch { /* refetch may be a no-op */ }
    },
    onAiApply(result) {
      // RetrievalToolsBase is a "flat" variant.
      if (!this.entity?.id) return
      const key = `retrieval:${this.entity.id}`
      if (!applyAiVariantResult(this.editBuffer, key, result, { shape: 'flat' })) {
        notify.error(m.aiEdit_noActiveVariant())
        return
      }
      this.showAiEdit = false
    },
  },
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.retrieval-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.retrieval-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>

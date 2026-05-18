<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" :created-by="entity?.created_by" :updated-by="entity?.updated_by" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #subheader>
      <rag-sub-header />
    </template>
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="rag-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_ragTool() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_ragTool() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_ragTool() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'rag-readonly-zone' : null" class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
              <template v-if="true">
                <div class="flex-none full-width">
                  <template v-if="tab == &quot;retrieve&quot;">
                    <rag-retrieve />
                  </template>
                  <template v-if="tab == &quot;generate&quot;">
                    <rag-generate />
                  </template>
                  <template v-if="tab == &quot;postProcess&quot;">
                    <rag-postprocess />
                  </template>
                  <template v-if="tab == &quot;uiSettings&quot;">
                    <rag-uisettings />
                  </template>
                  <template v-if="tab == &quot;languages&quot;">
                    <rag-languages />
                  </template>
                  <template v-if="tab == &quot;testSets&quot;">
                    <rag-test-sets />
                  </template>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #drawer>
      <div :inert="recordReadonly" :class="recordReadonly ? 'rag-readonly-zone' : null" class="full-height">
        <rag-drawer :open="openTest" @update:open="openTest = $event" />
      </div>
    </template>
  </layouts-details-layout>
  <rag-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
</template>

<script>
import { ref } from 'vue'
import { validSystemName } from '@/utils/validationRules'
import { useEntityAccess } from '@/composables/useEntityAccess'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const {
      draft, isLoading, isDirty, updateField, updateFields, updateVariantField,
      selectedVariant, activeVariant, variants, setSelectedVariant,
      createVariant, deleteVariant, activateVariant,
      save, revert, refetch, buildPayload, remove,
    } = useVariantEntityDetail('rag_tools')

    const { canEdit, canDelete, canCreate, recordReadonly, provideReadonly } = useEntityAccess('rag_tools', draft)
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
      save,
      revert,
      refetch,
      buildPayload,
      remove,
      m,
      tab: ref('retrieve'),
      tabs: ref([
        { value: 'retrieve', label: m.common_retrieve() },
        { value: 'generate', label: m.common_generate() },
        { value: 'languages', label: m.common_language() },
        { value: 'postProcess', label: m.common_postProcess() },
        { value: 'uiSettings', label: m.common_uiSettings() },
        { value: 'testSets', label: m.common_testSets() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      openTest: ref(true),
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
    activeRagId() {
      return this.$route.params.id
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
    entity() {
      return this.draft
    },
  },

  mounted() {
    if (this.$route.query?.variant) {
      this.setSelectedVariant(this.$route.query?.variant)
    }
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async handleSave() {
      const systemNameValidation = validSystemName()(this.entity?.system_name)
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
    async confirmDelete() {
      await this.remove()
      this.$emit('update:closeDrawer', null)
      notify.success('RAG Tool has been deleted.')
      this.navigate('/rag-tools')
    },
  },
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
.rag-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.rag-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>

<template>
  <div class="prompt-details full-height">
    <km-inner-loading :showing="loading" />
    <layouts-details-layout v-if="!loading">
      <template #header>
        <layouts-details-header :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
          <template #actions>
            <km-btn v-if="isDirty && !recordReadonly" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="composableRevert()" />
            <km-btn v-if="!recordReadonly" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
            <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="prompt-readonly-icon" />
            <ds-dropdown-menu-root>
              <ds-dropdown-menu-trigger as-child>
                <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
              </ds-dropdown-menu-trigger>
              <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
                <ds-dropdown-menu-item data-test="clone-btn" :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
                <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
              </ds-dropdown-menu-content>
            </ds-dropdown-menu-root>
          </template>
          <template #meta>
            <div class="cluster" data-gap="xs" data-wrap="no" data-align="center">
              <div class="km-input-label text-secondary-text">{{ m.common_category() }}</div>
              <km-dropdown-select v-model="category" :placeholder="m.label_categories()" :options="categoryOptions" :disabled="recordReadonly" />
            </div>
          </template>
          <template #variants>
            <prompts-sub-header />
          </template>
        </layouts-details-header>
      </template>
      <template #content>
        <!-- Tabs stay interactive so a read-only user can still switch tabs;
             individual tab panels carry the inert + readonly-zone wrap. -->
        <km-tabs v-model="tab" class="prompt-details__tabs full-height" :items="tabs">
          <template #panel-promptTemplate>
            <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="prompt-details__tab-panel">
              <prompts-prompttemplate />
            </div>
          </template>
          <template #panel-advancedSettings>
            <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="prompt-details__tab-panel">
              <prompts-advancedsettings />
            </div>
          </template>
          <template #panel-responseFormat>
            <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="prompt-details__tab-panel">
              <prompts-responseformat />
            </div>
          </template>
          <template #panel-samples>
            <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="prompt-details__tab-panel">
              <prompts-sampleinput />
            </div>
          </template>
          <template #panel-testSets>
            <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="prompt-details__tab-panel">
              <prompts-test-sets />
            </div>
          </template>
        </km-tabs>
      </template>
      <template #drawer>
        <div :inert="recordReadonly" :class="recordReadonly ? 'prompt-readonly-zone' : null" class="full-height">
          <prompts-drawer :open="openTest" @update:open="openTest = $event" />
        </div>
      </template>
    </layouts-details-layout>
    <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_promptTemplate() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
      <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_promptTemplate() }) }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_promptTemplate() }) }}</div>
    </km-popup-confirm>
    <prompts-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
  </div>
</template>

<script>
import { categoryOptions } from '@/config/prompts/prompts'
import { useEntityQueries } from '@/queries/entities'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { computed, provide, ref } from 'vue'
import { validSystemName } from '@/utils/validationRules'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'
import { usePermissions } from '@shared'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isLoading, isDirty, updateField, setSelectedVariant,
            save, revert, remove, refetch, buildPayload } = useVariantEntityDetail('promptTemplates')
    const removeMutation = queries.promptTemplates.useRemove()

    // PR 10 — record-level permission gating; same shape as Agents/details.
    const { can, canOn } = usePermissions()
    const canEdit = computed(() => canOn(draft?.value, 'edit', 'prompts'))
    const canDelete = computed(() => canOn(draft?.value, 'delete', 'prompts'))
    const canCreate = computed(() => can('write:prompts'))
    const recordReadonly = computed(() => {
      const p = draft?.value
      if (!p) return false
      return canEdit.value === false
    })
    provide('promptReadonly', recordReadonly)

    return {
      draft,
      isLoading,
      isDirty,
      updateField,
      setSelectedVariant,
      composableSave: save,
      composableRevert: revert,
      composableRemove: remove,
      refetch,
      buildPayload,
      canEdit,
      canDelete,
      canCreate,
      recordReadonly,
      m,
      tab: ref('promptTemplate'),
      tabs: ref([
        { value: 'promptTemplate', label: m.common_promptTemplate() },
        { value: 'advancedSettings', label: m.common_modelSettings() },
        { value: 'responseFormat', label: m.common_responseFormat() },
        { value: 'samples', label: m.common_notes() },
        { value: 'testSets', label: m.common_testSets() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      openTest: ref(true),
      removeMutation,
      categoryOptions,
      validSystemName,
    }
  },
  computed: {
    category: {
      get() {
        return this.draft?.category || ''
      },
      set(value) {
        this.updateField('category', value)
      },
    },
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
    activePromptTemplateId() {
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
  activated() {
    // refetch handles re-sync on KeepAlive reactivation
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
        await this.composableSave()
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
      notify.success(m.notify_entityDeleted({ entity: m.entity_promptTemplate() }))
      this.navigate('/prompt-templates')
    },
  },
}
</script>

<style>
.prompt-details {
  min-block-size: 0;
}

.prompt-details__tabs {
  min-block-size: 0;
}

.prompt-details__tabs .ds-tabs__panel {
  overflow: auto;
}

.prompt-details__tab-panel {
  inline-size: 100%;
  min-block-size: 0;
}

.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}

/* PR 10 readonly visual cue. `inert` blocks all interactivity; styles just
 * dim the zone so the user understands it's not editable. */
.prompt-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.prompt-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>

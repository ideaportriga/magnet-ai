<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="activeAssistantToolDB?.created_at" :updated-at="activeAssistantToolDB?.updated_at" :created-by="activeAssistantToolDB?.created_by" :updated-by="activeAssistantToolDB?.updated_by" show-record-info :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty && !recordReadonly" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="!recordReadonly" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="handleSave" />
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="assistant-tool-readonly-icon" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item :disabled="!canCreate" @select="canCreate && (showNewDialog = true)">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canDelete" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_assistantTool() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_assistantTool() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_assistantTool() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <km-tabs v-model="tab" :items="tabs" />
      <div :inert="recordReadonly" :class="recordReadonly ? 'assistant-tool-readonly-zone' : null" class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="min-block-size: 0">
        <div class="cluster full-height full-width" data-gap="lg">
          <div class="flex-1 full-height full-width">
            <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
              <template v-if="true">
                <div class="flex-none full-width">
                  <template v-if="tab == &quot;general&quot; &amp;&amp; type == &quot;api&quot;">
                    <assistant-tools-general-api />
                  </template>
                  <template v-else-if="tab == &quot;general&quot; &amp;&amp; type == &quot;rag&quot;">
                    <assistant-tools-general-rag />
                  </template>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #drawer>
      <div :inert="recordReadonly" :class="recordReadonly ? 'assistant-tool-readonly-zone' : null" class="full-height">
        <assistant-tools-drawer :open="openTest" @update:open="openTest = $event" />
      </div>
    </template>
  </layouts-details-layout>
  <assistant-tools-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
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
    const { draft, isLoading, isDirty, updateField, save, revert, remove } = useEntityDetail('assistant_tools')
    const { canCreate, canDelete, recordReadonly, provideReadonly } = useEntityAccess('assistant_tools', draft)
    provideReadonly()
    const { data: listData } = queries.assistant_tools.useList()
    const items = computed(() => listData.value?.items ?? [])

    return {
      m,
      isLoading,
      tab: ref('general'),
      tabs: ref([{ value: 'general', label: m.common_general() }]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      activeAssistantTool: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      items,
      validSystemName,
      canCreate,
      canDelete,
      recordReadonly,
      draft,
      isDirty,
      updateField,
      save,
      revert,
      remove,
    }
  },
  computed: {
    type() {
      return this.draft?.type || ''
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
    currentAssistantTool() {
      return this.draft
    },
    activeAssistantToolId() {
      return this.$route.params.id
    },
    activeAssistantToolDB() {
      return this.items.find((item) => item.id == this.activeAssistantToolId)
    },
    activeAssistantToolName() {
      return this.items?.find((item) => item.id == this.activeAssistantToolId)?.name
    },
    options() {
      return this.items?.map((item) => item.name)
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
    async confirmDelete() {
      await this.remove()
      this.$emit('update:closeDrawer', null)
      notify.success('Assistant Tool has been deleted.')
      this.navigate('/assistant-tools')
    },
    async handleSave() {
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentAssistantTool?.system_name)
      if (systemNameValidation !== true) {
        notify.error(systemNameValidation)
        return
      }

      this.saving = true
      try {
        const result = await this.save()
        if (result.success) {
          notify.success('Saved successfully')
        } else if (result.error) {
          throw result.error
        }
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

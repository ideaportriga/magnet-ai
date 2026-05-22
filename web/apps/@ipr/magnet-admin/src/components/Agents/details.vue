<template>
  <km-inner-loading :showing="loading" />
  <!--
    Direct-link access failure handler (PR 9a). If the detail query errored
    (most commonly: backend returned 404 because the user lacks `view`
    record permission, or the agent is in another tenant blocked by RLS),
    render a friendly "no access" panel with a way back to the list
    instead of leaving the loading spinner hanging or crashing the layout.
  -->
  <div v-if="isError && !isLoading" class="flex flex-center full-height" data-test="agent-access-denied">
    <div class="stack items-center p-xl" data-gap="0" style="max-inline-size: 480px">
      <km-glyph name="lock" size="48px" tone="muted" />
      <div class="text-h6 mt-md text-center">{{ m.access_recordHiddenTitle() }}</div>
      <div class="text-body2 text-grey mt-sm text-center">{{ m.access_recordHiddenBody() }}</div>
      <km-btn class="mt-lg" outline tone="brand" :label="m.access_backToList()" no-caps @click="navigate('/agents')" />
    </div>
  </div>
  <layouts-details-layout v-else-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" :created-by="entity?.created_by" :updated-by="entity?.updated_by" show-record-info :no-header="$route?.name !== &quot;AgentDetail&quot;" :no-content-wrapper="$route?.name !== &quot;AgentDetail&quot;" :readonly="recordReadonly" :field-classes="headerFieldClasses" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #subheader>
      <!-- SubHeader is NOT wrapped in inert — switching variants is a
           read action (the user wants to see the different versions).
           Edit-style controls inside SubHeader (Activate / Copy-to-new /
           Delete / variant description) handle readonly themselves via
           the injected `agentReadonly` ref. -->
      <agents-sub-header />
    </template>
    <!-- Record-level access info (visibility / owner / department) lives
         inside the existing record-info tooltip (the (i) icon in the
         header). This keeps the toolbar uncluttered while still showing
         the metadata on hover. -->
    <template #record-info-extra>
      <agents-access-info :agent="entity" variant="tooltip" />
    </template>
    <template #header-actions>
      <!-- Read-only indicator: a single lock glyph (with tooltip) instead
           of a full chip — keeps the toolbar visually light. -->
      <km-glyph v-if="recordReadonly" name="lock" size="16px" tone="muted" :title="m.access_readOnlyTooltip()" data-test="agent-readonly-icon" />
      <km-chip
        v-if="aiSuggestedCount > 0"
        tone="info"
        size="sm"
        icon="magic"
        icon-size="12px"
        :label="`${aiSuggestedCount} AI suggested`"
        data-test="ai-suggested-chip"
      />
      <km-btn v-if="isDirty && canEdit" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="canEdit" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item v-if="canEdit && entity?.id" data-test="ai-edit-btn" @select="showAiEdit = true">{{ m.aiEdit_action() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item v-if="canCreate" data-test="clone-btn" @select="showNewDialog = true">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <template v-if="canEdit">
            <ds-dropdown-menu-separator />
            <access-control-menu :visibility="entity?.visibility" :department-id="entity?.department_id" @update:visibility="updateField('visibility', $event)" @update:department-id="updateField('department_id', $event)" />
          </template>
          <ds-dropdown-menu-separator v-if="canDelete" />
          <ds-dropdown-menu-item v-if="canDelete" data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_agent() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_agent() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_agentBody() }}</div>
      </km-popup-confirm>
      <km-popup-confirm :visible="showLeaveDialog" :confirm-button-label="m.access_leaveDiscard()" :cancel-button-label="m.access_leaveStay()" notification-icon="warning" @confirm="confirmLeave" @cancel="cancelLeave">
        <div class="cluster km-heading-7" data-justify="center">{{ m.access_leaveTitle() }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.access_leaveBody() }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <router-view v-if="$route?.name !== &quot;AgentDetail&quot;" />
      <template v-if="$route?.name === &quot;AgentDetail&quot;">
        <!-- Tabs themselves stay interactive so a read-only user can still
             navigate between Topics / Settings / Channels / etc. The tab
             *content* is wrapped in an inert zone — buttons, inputs and
             dialogs inside it can't be activated. -->
        <km-tabs v-model="tab" :items="tabsWithDirty" />
        <div
          :inert="recordReadonly && tab !== 'history'" :class="[
            'stack full-height full-width overflow-auto mb-md mt-lg km-flex-min-0',
            recordReadonly && tab !== 'history' ? 'agent-readonly-zone' : null,
          ]" data-gap="lg"
        >
          <agents-topics v-if="tab == &quot;topics&quot;" />
          <agents-post-processing v-if="tab == &quot;post-processing&quot;" />
          <agents-settings v-if="tab == &quot;settings&quot;" />
          <agents-conversations v-if="tab == &quot;conversations&quot;" />
          <agents-notes v-if="tab == &quot;notes&quot;" />
          <agents-test-sets v-if="tab == &quot;testSets&quot;" />
          <agents-channels v-if="tab == &quot;channels&quot;" />
          <entity-audit-history
            v-if="tab == &quot;history&quot; && entity?.id"
            entity-type="agent"
            :entity-id="entity.id"
            :invalidate-query-keys="historyInvalidateKeys"
            @restored="onRestored"
          />
        </div>
      </template>
    </template>
    <template #drawer>
      <!-- Drawer (topic / action editors) — same inert treatment. Keeps
           the panel visible (so users can read its contents) but blocks
           edits when the user has no permission. -->
      <div :inert="recordReadonly" :class="recordReadonly ? 'agent-readonly-zone' : null" class="full-height">
        <agents-drawer />
      </div>
    </template>
  </layouts-details-layout>
  <agents-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
  <ai-edit-drawer
    v-if="entity?.id"
    v-model:open="showAiEdit"
    entity-type="agent"
    :entity-id="entity.id"
    @apply="onAiApply"
  />
</template>

<script>
import { ref, computed, provide } from 'vue'
import { useRoute, onBeforeRouteLeave } from 'vue-router'
import { validSystemName } from '@/utils/validationRules'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'
import { usePermissions } from '@shared'
import AgentsAccessInfo from './AccessInfo.vue'
import EntityAuditHistory from '@/components/shared/EntityAuditHistory.vue'
import AiEditDrawer from '@/components/shared/AiEditDrawer.vue'
import { entityKeys } from '@/queries/queryKeys'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { applyAiVariantResult, setAiSaveContext } from '@/utils/aiEditMerge'

export default {
  components: { AgentsAccessInfo, EntityAuditHistory, AiEditDrawer },
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const { draft, isLoading, isError, error, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            activeTopic, conversationId,
            updateHighLevelNestedProperty, updateNestedListItemBySystemName,
            save: saveEntity, revert, remove: removeEntity, refetch, buildPayload, testSetItem } = useAgentEntityDetail()

    // ── Unsaved-changes guard ─────────────────────────────────────────
    // Show a confirm dialog before navigating away when the draft has
    // unsaved changes. Without this the previous UX silently discarded
    // edits on back-button / sidebar click.
    const showLeaveDialog = ref(false)
    const pendingNavigation = ref(null)
    onBeforeRouteLeave((to, from, next) => {
      if (!isDirty.value) {
        next()
        return
      }
      // Save the `next` continuation so the user can resolve via the popup.
      pendingNavigation.value = next
      showLeaveDialog.value = true
    })
    function confirmLeave() {
      showLeaveDialog.value = false
      try {
        // Discard the in-memory edits so the next time the user lands here
        // they don't see stale dirty state.
        revert()
      } catch { /* revert may be a no-op when buffer is empty */ }
      const next = pendingNavigation.value
      pendingNavigation.value = null
      if (typeof next === 'function') next()
    }
    function cancelLeave() {
      showLeaveDialog.value = false
      const next = pendingNavigation.value
      pendingNavigation.value = null
      if (typeof next === 'function') next(false)
    }

    // PR 9a: record-level permission gating. Reads `_permissions` from the
    // loaded agent (shipped by backend after PR 8). Falls through to global
    // capability for legacy records so existing UX doesn't regress.
    const { can, canOn } = usePermissions()
    const canCreate = computed(() => can('write:agents'))
    const canEdit = computed(() => canOn(draft?.value, 'edit', 'agents'))
    const canDelete = computed(() => canOn(draft?.value, 'delete', 'agents'))
    // Read-only state for the detail page: explicit `_permissions.edit=false`
    // on a loaded record. Until the record is loaded, default to false.
    const recordReadonly = computed(() => {
      // Record is loaded AND user cannot edit it — gate all edit-style
      // controls. We treat "no edit capability at all" the same as an
      // explicit `_permissions.edit=false` so legacy records without a
      // `_permissions` block don't accidentally look editable to roles
      // that lack global write capability (e.g. `viewer`).
      const a = draft?.value
      if (!a) return false
      return canEdit.value === false
    })

    // Expose to child components (SubHeader, drawers, tab sub-views).
    // Children that want to gate edit-only affordances (e.g. SubHeader's
    // Activate / Copy / Delete variant buttons) inject this ref.
    provide('agentReadonly', recordReadonly)

    return {
      m,
      draft,
      isLoading,
      isError,
      error,
      isDirty,
      updateField,
      saveEntity,
      refetch,
      revert,
      removeEntity,
      setSelectedVariant,
      canEdit,
      canCreate,
      canDelete,
      recordReadonly,
      showLeaveDialog,
      confirmLeave,
      cancelLeave,
      editBuffer: useEditBufferStore(),
      showAiEdit: ref(false),
      tab: ref('topics'),
      tabs: ref([
        { value: 'topics', label: m.common_topics() },
        { value: 'post-processing', label: m.common_postProcessing() },
        { value: 'settings', label: m.common_settings() },
        { value: 'channels', label: m.common_channels() },
        { value: 'conversations', label: m.common_conversations() },
        { value: 'notes', label: m.common_notes() },
        { value: 'testSets', label: m.common_testSets() },
        { value: 'history', label: m.common_history() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
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
    loading() {
      // Don't sit on the spinner when the query errored — we want the
      // "no access / not found" panel to render in that case.
      if (this.isError) return false
      return this.isLoading || !this.draft?.system_name
    },
    entity() {
      return this.draft
    },
    historyInvalidateKeys() {
      // After a restore the agent's own detail/list caches go stale.
      // Invalidate both so the form re-renders with the restored state
      // and any open list view shows the new updated_at.
      const id = this.entity?.id
      return id
        ? [entityKeys.agents.detail(id), entityKeys.agents.lists()]
        : [entityKeys.agents.lists()]
    },
    aiSuggestedCount() {
      // Number of dot-paths the AI most recently suggested and the user
      // hasn't reverted yet. Drives the "N AI suggested" chip next to
      // Save so the user sees there's pending AI work waiting to be
      // committed (or thrown away with Revert).
      if (!this.entity?.id) return 0
      return this.editBuffer.getAiSuggestedPaths(`agents:${this.entity.id}`).size
    },
    headerFieldClasses() {
      // Pass per-field highlight classes for the header inputs. We
      // compute them eagerly (not via composable) so the same Options
      // API call site works without a Composition setup migration.
      if (!this.entity?.id) return {}
      const key = `agents:${this.entity.id}`
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
    /** Tabs with a `dirty` flag derived from per-section path prefixes
     *  in the edit buffer. Each prefix matches the variant-relative
     *  paths the corresponding tab edits (e.g. the `settings` tab
     *  touches paths under `variants[N].value.settings.*`). */
    tabsWithDirty() {
      if (!this.entity?.id) return this.tabs
      const key = `agents:${this.entity.id}`
      const changed = this.editBuffer.getChangedPaths(key)
      if (changed.size === 0) return this.tabs

      const idx = this._activeVariantIndex
      const v = idx >= 0 ? `variants[${idx}].value.` : null
      // Each tab's paths — matched as PREFIX on the changed-path set.
      const tabPathPrefixes = {
        topics: v
          ? [`${v}topics`, `${v}prompt_templates`]
          : [],
        'post-processing': v ? [`${v}post_processing`] : [],
        settings: v ? [`${v}settings`] : [],
        channels: ['channels'],
        // History / Conversations / Notes / TestSets aren't edit
        // surfaces for the entity body — never dirty here.
      }
      const isDirty = (prefixes) =>
        prefixes.some((p) =>
          [...changed].some((path) => path === p || path.startsWith(`${p}.`) || path.startsWith(`${p}[`)),
        )
      return this.tabs.map((t) => {
        const prefixes = tabPathPrefixes[t.value]
        return prefixes && prefixes.length ? { ...t, dirty: isDirty(prefixes) } : t
      })
    },
    /** Index of the active variant in `draft.variants` — used by
     *  ``tabsWithDirty`` to build paths into the buffer. */
    _activeVariantIndex() {
      const variants = this.draft?.variants
      const active = this.draft?.active_variant
      if (!Array.isArray(variants)) return -1
      return variants.findIndex((v) => v?.variant === active)
    },
  },

  mounted() {
    if (this.$route.query?.variant) {
      this.setSelectedVariant(this.$route.query?.variant)
    }
  },
  methods: {
    changeTab(tab) {
      this.tab = tab
    },
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
        // Forward the AI request id (if any) into the upcoming PATCH so
        // the audit row records which AI suggestion produced this save.
        if (this.entity?.id) {
          setAiSaveContext(this.editBuffer, `agents:${this.entity.id}`, 'agents', this.entity.id)
        }
        await this.saveEntity()
        notify.success(m.agents_savedSuccessfully())
      } catch (error) {
        notify.error(error.message || m.agents_failedToSave())
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeEntity()
      this.$emit('update:closeDrawer', null)
      notify.success(m.agents_agentDeleted())
      this.navigate('/agents')
    },
    async onRestored() {
      // The audit history component already invalidated the agent's
      // detail/list cache; pull the new state into the local edit buffer.
      try {
        await this.refetch?.()
      } catch { /* refetch may not be available on stub */ }
    },
    onAiApply(result) {
      // The AI editor returns just the editable subset (an
      // ``AgentVariantValue``). Patch it into the active variant of the
      // current draft, then push the merged object back through
      // editBuffer.applyAiPatch so the form picks up an "AI-suggested"
      // highlight on every changed path.
      if (!this.entity?.id) return
      const key = `agents:${this.entity.id}`
      if (!applyAiVariantResult(this.editBuffer, key, result, { shape: 'wrapped' })) {
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

/*
 * Read-only zone — applied to subheader / tab content / drawer when the
 * user has no edit permission. Native `inert` attribute on the wrapping
 * <div> handles all the interactivity blocking (no clicks, no focus, no
 * form input); these styles just supply the visual cue.
 */
.agent-readonly-zone {
  opacity: 0.72;
  cursor: not-allowed;
}
.agent-readonly-zone :where(input, textarea, select, button, [role='button']) {
  cursor: not-allowed;
}
</style>

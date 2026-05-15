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
  <layouts-details-layout v-else-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" :created-by="entity?.created_by" :updated-by="entity?.updated_by" show-record-info :no-header="$route?.name !== &quot;AgentDetail&quot;" :no-content-wrapper="$route?.name !== &quot;AgentDetail&quot;" :readonly="recordReadonly" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
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
      <km-btn v-if="isDirty && canEdit" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn v-if="canEdit" data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" @select="showNewDialog = true">{{ m.common_clone() }}</ds-dropdown-menu-item>
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
        <km-tabs v-model="tab" :items="tabs" />
        <div
          :inert="recordReadonly" :class="[
            'stack full-height full-width overflow-auto mb-md mt-lg km-flex-min-0',
            recordReadonly ? 'agent-readonly-zone' : null,
          ]" data-gap="lg"
        >
          <agents-topics v-if="tab == &quot;topics&quot;" />
          <agents-post-processing v-if="tab == &quot;post-processing&quot;" />
          <agents-settings v-if="tab == &quot;settings&quot;" />
          <agents-conversations v-if="tab == &quot;conversations&quot;" />
          <agents-notes v-if="tab == &quot;notes&quot;" />
          <agents-test-sets v-if="tab == &quot;testSets&quot;" />
          <agents-channels v-if="tab == &quot;channels&quot;" />
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

export default {
  components: { AgentsAccessInfo },
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
    const { canOn } = usePermissions()
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
      revert,
      removeEntity,
      setSelectedVariant,
      canEdit,
      canDelete,
      recordReadonly,
      showLeaveDialog,
      confirmLeave,
      cancelLeave,
      tab: ref('topics'),
      tabs: ref([
        { value: 'topics', label: m.common_topics() },
        { value: 'post-processing', label: m.common_postProcessing() },
        { value: 'settings', label: m.common_settings() },
        { value: 'channels', label: m.common_channels() },
        { value: 'conversations', label: m.common_conversations() },
        { value: 'notes', label: m.common_notes() },
        { value: 'testSets', label: m.common_testSets() },
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

<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" :system-name-rules="[validSystemName()]" :created-at="entity?.created_at" :updated-at="entity?.updated_at" :created-by="entity?.created_by" :updated-by="entity?.updated_by" show-record-info :no-header="$route?.name !== &quot;AgentDetail&quot;" :no-content-wrapper="$route?.name !== &quot;AgentDetail&quot;" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #subheader>
      <agents-sub-header />
    </template>
    <template #header-actions>
      <km-btn v-if="isDirty" data-test="revert-btn" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn data-test="save-btn" :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" data-test="show-more-btn" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item data-test="clone-btn" @select="showNewDialog = true">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item data-test="delete-btn" variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.deleteConfirm_deleteEntity({ entity: m.entity_agent() })" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_agent() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_agentBody() }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <router-view v-if="$route?.name !== &quot;AgentDetail&quot;" />
      <template v-if="$route?.name === &quot;AgentDetail&quot;">
        <km-tabs v-model="tab" :items="tabs" />
        <div class="stack full-height full-width overflow-auto mb-md mt-lg km-flex-min-0" data-gap="lg">
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
      <agents-drawer />
    </template>
  </layouts-details-layout>
  <agents-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { validSystemName } from '@/utils/validationRules'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const route = useRoute()
    const { draft, isLoading, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            activeTopic, conversationId,
            updateHighLevelNestedProperty, updateNestedListItemBySystemName,
            save: saveEntity, revert, remove: removeEntity, refetch, buildPayload, testSetItem } = useAgentEntityDetail()

    return {
      m,
      draft,
      isLoading,
      isDirty,
      updateField,
      saveEntity,
      revert,
      removeEntity,
      setSelectedVariant,
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
</style>

<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading')
  template(#header)
    km-input-flat.km-heading-4.full-width.text-black(:placeholder='m.common_name()', :modelValue='name', @change='name = $event')
    km-input-flat.km-description.full-width.text-black(:placeholder='m.common_description()', :modelValue='description', @change='description = $event')
    .row.items-center.q-pl-6
      q-icon.col-auto(name='o_info', color='text-secondary')
        q-tooltip.bg-white.block-shadow.text-black.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
      km-input-flat.col.km-description.full-width(
        :placeholder='m.placeholder_enterSystemNameReadable()',
        :modelValue='system_name',
        @change='system_name = $event',
        @focus='showInfo = true',
        @blur='showInfo = false',
        :rules='[validSystemName()]'
      )
    .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
  template(#subheader)
    configuration-sub-header
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_ragTool() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_ragTool() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_ragTool() }) }}
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
import { ref } from 'vue'
import { validSystemName } from '@/utils/validationRules'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { m } from '@/paraglide/messages'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const {
      draft, isLoading, isDirty, updateField, updateFields, updateVariantField,
      selectedVariant, activeVariant, variants, setSelectedVariant,
      createVariant, deleteVariant, activateVariant,
      save, revert, refetch, buildPayload, remove,
    } = useVariantEntityDetail('rag_tools')

    return {
      draft,
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
        { name: 'retrieve', label: m.common_retrieve() },
        { name: 'generate', label: m.common_generate() },
        { name: 'languages', label: m.common_language() },
        { name: 'postProcess', label: m.common_postProcess() },
        { name: 'uiSettings', label: m.common_uiSettings() },
        { name: 'testSets', label: m.common_testSets() },
      ]),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      openTest: ref(true),
      showInfo: ref(false),
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
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: systemNameValidation, timeout: 3000 })
        return
      }
      this.saving = true
      try {
        await this.save()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.remove()
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

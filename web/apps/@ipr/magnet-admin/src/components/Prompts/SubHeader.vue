<template>
  <div class="prompt-variant-subheader">
    <km-separator class="my-sm" />
    <div class="prompt-variant-toolbar cluster" data-gap="sm">
      <div class="flex-none py-auto">
        <km-dropdown-select :model-value="selectedVariant" :options="variants" @update:model-value="setSelectedVariant" />
      </div>
      <div class="prompt-variant-toolbar__description flex-1 mx-sm">
        <km-input-flat class="km-description full-width" :placeholder="m.common_description()" :model-value="variant_description" :readonly="promptReadonly" @change="variant_description = $event" />
      </div>
      <div v-if="isActive" class="prompt-variant-toolbar__status flex-none mr-sm">
        <km-chip class="mr-sm" :label="m.common_active()" tone="brand" />
      </div>
      <div v-if="!promptReadonly && !isActive" class="prompt-variant-toolbar__status flex-none mr-sm">
        <km-btn :label="m.common_activate()" icon="check" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="promptReadonly" @click="activateVariantAction" />
      </div>
      <km-separator v-if="!promptReadonly" vertical tone="inverse" />
      <div v-if="!promptReadonly" class="flex-none text-white mx-md">
        <km-btn :label="m.common_copyToNew()" icon="add" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="promptReadonly" @click="addVariant" />
      </div>
      <div v-if="!promptReadonly" class="flex-none text-white mr-md">
        <km-btn class="mx-xs" flat :icon="&quot;delete&quot;" icon-size="16px" size="13px" :disable="promptReadonly || variants?.length === 1" :tooltip="m.common_delete()" @click="deleteVariantAction" />
      </div>
      <prompts-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
      <km-inner-loading :showing="loading" />
    </div>
  </div>
</template>

<script>
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { ref, computed, inject } from 'vue'
import { notify } from '@shared/utils/notify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isDirty, selectedVariant, activeVariant, variants: variantsRaw,
            updateVariantField, setSelectedVariant, createVariant, deleteVariant,
            activateVariant, save, buildPayload } = useVariantEntityDetail('promptTemplates')
    const { data: listData } = queries.promptTemplates.useList()
    const { mutateAsync: updateEntity } = queries.promptTemplates.useUpdate()
    const { mutateAsync: createEntity } = queries.promptTemplates.useCreate()
    const { mutateAsync: removeEntity } = queries.promptTemplates.useRemove()
    const items = computed(() => listData.value?.items ?? [])
    const promptReadonlyRef = inject('promptReadonly', null)
    const promptReadonly = computed(() => Boolean(promptReadonlyRef?.value))

    return {
      m,
      draft,
      isDirty,
      selectedVariant,
      activeVariant,
      variantsRaw,
      updateVariantField,
      setSelectedVariant,
      createVariant: createVariant,
      deleteVariant: deleteVariant,
      activateVariant: activateVariant,
      composableSave: save,
      buildPayload,
      items,
      updateEntity,
      createEntity,
      removeEntity,
      loading: ref(false),
      showNewDialog: ref(false),
      promptReadonly,
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    variants() {
      return this.draft?.variants?.map((el) => ({
        label: el.display_name || this.getVariantLabel(el.variant),
        value: el.variant,
        badgeLabel: el.variant == this.draft?.active_variant ? m.common_active() : '',
        badgeTone: 'brand',
        badgeIcon: 'check',
      }))
    },
    variant_description: {
      get() {
        return this.activeVariant?.description
      },
      set(value) {
        this.updateVariantField('description', value)
      },
    },
    created_at() {
      if (!this.activeRowDB.created_at) return ''
      return `${this.formatDate(this.activeRowDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRowDB.updated_at) return ''
      return `${this.formatDate(this.activeRowDB.updated_at)}`
    },
    currentRow() {
      return this.draft
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.items.find((item) => item.id == this.activeRowId)
    },

    activeRowName: {
      get() {
        return this.activeRowDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.name, value: item }))
    },
  },
  watch: {},
  created() {},

  methods: {
    getVariantLabel(variant) {
      const v = this.draft?.variants?.find((el) => el.variant === variant)
      if (v?.display_name) return v.display_name

      const match = variant?.match(/variant_(\d+)/)
      if (!match) return variant
      return `${m.common_variant()} ${match?.[1]}`
    },
    activateVariantAction() {
      this.activateVariant()
      notify.success(m.common_variantActivated())
    },
    addVariant() {
      this.createVariant()
      notify.success(m.common_variantAdded())
    },
    deleteVariantAction() {
      this.confirm(m.common_deleteVariantConfirm(), () => this.deleteVariant())
    },

    confirm(message, callback) {
      notify.confirm({
        message,
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          callback()
          notify.success(m.common_variantDeleted())
        },
      })
    },

    deletePromptTemplate() {
      notify.confirm({
        message: m.deleteConfirm_aboutToDelete({ entity: m.entity_promptTemplate() }),
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          this.loadingDelelete = true
          this.removeEntity(this.$route.params.id)
          this.$emit('update:closeDrawer', null)
          notify.success(m.notify_entityDeleted({ entity: m.entity_promptTemplate() }))
          this.navigate('/prompt-templates')
        },
      })
    },
    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      this.loading = true
      await this.composableSave()
      this.loading = false
    },
    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
}
</script>

<style scoped>
.prompt-variant-toolbar {
  min-inline-size: 0;
}

.prompt-variant-toolbar__description {
  min-inline-size: 0;
}

.prompt-variant-toolbar__status {
  display: inline-flex;
  align-items: center;
}
</style>

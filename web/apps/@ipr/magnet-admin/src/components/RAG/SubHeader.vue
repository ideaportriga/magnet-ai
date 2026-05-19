<template>
  <div>
    <km-separator class="my-sm" />
    <div class="cluster">
      <div class="flex-none py-auto">
        <km-dropdown-select :model-value="selectedVariant" :options="variants" @update:model-value="setSelectedVariant" />
      </div>
      <div class="flex-1 mx-sm">
        <km-input-flat class="km-description full-width" :placeholder="m.common_description()" :model-value="variant_description" :readonly="ragReadonly" @change="variant_description = $event" />
      </div>
      <div v-if="isActive" class="flex-none mr-sm">
        <km-chip class="mr-sm" :label="m.common_active()" tone="brand" />
      </div>
      <div v-if="!ragReadonly && !isActive" class="flex-none mr-sm">
        <km-btn class="width-100" :label="m.common_activate()" icon="check" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="ragReadonly" @click="activateVariant" />
      </div>
      <km-separator v-if="!ragReadonly" vertical tone="inverse" />
      <div v-if="!ragReadonly" class="flex-none text-white mx-md">
        <km-btn :label="m.common_copyToNew()" icon="add" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="ragReadonly" @click="addVariant" />
      </div>
      <div v-if="!ragReadonly" class="flex-none text-white mr-md">
        <km-btn class="mx-xs" flat :icon="&quot;delete&quot;" icon-size="16px" size="13px" :disable="ragReadonly || variants?.length === 1" @click="deleteVariant" />
      </div>
      <prompts-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
      <km-inner-loading :showing="loading" />
    </div>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { computed, inject, ref } from 'vue'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { notify } from '@shared/utils/notify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const {
      draft, isDirty, updateField, updateVariantField,
      selectedVariant, activeVariant, variants,
      setSelectedVariant, createVariant: composableCreateVariant,
      deleteVariant: composableDeleteVariant, activateVariant: composableActivateVariant,
      save, revert,
    } = useVariantEntityDetail('rag_tools')
    const { options: items } = useCatalogOptions('rag_tools')
    const ragReadonlyRef = inject('ragReadonly', null)
    const ragReadonly = computed(() => Boolean(ragReadonlyRef?.value))

    return {
      m,
      draft,
      isDirty,
      updateField,
      updateVariantField,
      selectedVariant,
      activeVariant,
      variantsList: variants,
      setSelectedVariant,
      composableCreateVariant,
      composableDeleteVariant,
      composableActivateVariant,
      save,
      revert,
      items,
      loading: ref(false),
      showNewDialog: ref(false),
      ragReadonly,
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    variants() {
      return this.draft?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
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
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    activateVariant() {
      this.composableActivateVariant()
      notify.success(m.common_variantActivated())
    },
    addVariant() {
      this.composableCreateVariant()
      notify.success(m.common_variantAdded())
    },
    deleteVariant() {
      this.confirm(m.common_deleteVariantConfirm(), () => this.composableDeleteVariant())
    },
    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
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

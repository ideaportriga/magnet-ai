<template>
  <div>
    <km-separator class="my-sm" />
    <div class="cluster">
      <div class="flex-none py-auto">
        <km-dropdown-select :model-value="selectedVariant" :options="variantOptions" @update:model-value="setSelectedVariant" />
      </div>
      <div class="flex-1 mx-sm">
        <km-input-flat class="km-description full-width" :placeholder="m.common_description()" :model-value="variant_description" :readonly="retrievalReadonly" @change="variant_description = $event" />
      </div>
      <div v-if="isActive" class="flex-none mr-sm">
        <km-chip class="mr-sm" :label="m.common_active()" tone="brand" />
      </div>
      <div v-if="!retrievalReadonly && !isActive" class="flex-none mr-sm">
        <km-btn class="width-100" :label="m.common_activate()" icon="check" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="retrievalReadonly" @click="handleActivateVariant" />
      </div>
      <km-separator v-if="!retrievalReadonly" vertical tone="inverse" />
      <div v-if="!retrievalReadonly" class="flex-none text-white mx-md">
        <km-btn :label="m.common_copyToNew()" icon="add" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="retrievalReadonly" @click="addVariant" />
      </div>
      <div v-if="!retrievalReadonly" class="flex-none text-white mr-md">
        <km-btn class="mx-xs" flat :icon="&quot;delete&quot;" icon-size="16px" size="13px" :disable="retrievalReadonly || variantOptions?.length === 1" @click="handleDeleteVariant" />
      </div>
      <prompts-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" copy @cancel="showNewDialog = false" />
      <km-inner-loading :showing="loading" />
    </div>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { computed, inject, ref } from 'vue'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { notify } from '@shared/utils/notify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

export default {
  components: { KmDropdownSelect },
  setup() {
    const { draft, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants,
            setSelectedVariant, createVariant, deleteVariant, activateVariant,
             save, revert, refetch, buildPayload } = useVariantEntityDetail('retrieval')
    const retrievalReadonlyRef = inject('retrievalReadonly', null)
    const retrievalReadonly = computed(() => Boolean(retrievalReadonlyRef?.value))
    return {
      m,
      draft,
      isDirty,
      updateField,
      updateVariantField,
      selectedVariant,
      activeVariant,
      variants,
      setSelectedVariant,
      createVariant: createVariant,
      deleteVariant: deleteVariant,
      activateVariant: activateVariant,
      loading: ref(false),
      showNewDialog: ref(false),
      retrievalReadonly,
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    variantOptions() {
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
    handleActivateVariant() {
      this.activateVariant()
      notify.success(m.common_variantActivated())
    },
    addVariant() {
      this.createVariant()
      notify.success(m.common_variantAdded())
    },
    handleDeleteVariant() {
      this.confirm(m.common_deleteVariantConfirm(), () => this.deleteVariant())
    },
  },
}
</script>

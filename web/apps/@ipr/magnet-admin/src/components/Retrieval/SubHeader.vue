<template lang="pug">
q-separator.q-my-sm
.row.items-center
  .col-auto.q-py-auto
    km-select-flat(:options='variantOptions', v-model='selected_variant', bg-color='background', height='30px', hasDropdownSearch)
      template(#option='{ itemProps, select, option }')
        q-item.bb-border(clickable, v-bind='itemProps', dense, @click='select(option)')
          q-item-section
            q-item-label.km-label {{ option.label }}
          q-item-section(v-if='option?.active_variant', avatar)
            q-chip.q-mr-sm(:label='m.common_active()', color='primary-light', text-color='primary', flat, size='sm')

  .col.q-mx-sm
    km-input-flat.km-description.full-width(:placeholder='m.common_description()', :modelValue='variant_description', @change='variant_description = $event')
  .col-auto.q-mr-sm
    km-btn.width-100(
      v-if='!isActive',
      :label='m.common_activate()',
      icon='far fa-circle-check',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='handleActivateVariant'
    )
    q-chip.q-mr-sm(v-if='isActive', :label='m.common_active()', color='primary-light', text-color='primary')

  q-separator(vertical, color='white')
  .col-auto.text-white.q-mx-md
    km-btn(
      :label='m.common_copyToNew()',
      icon='fas fa-plus',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='addVariant'
    )
  .col-auto.text-white.q-mr-md
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='handleDeleteVariant', :disable='variantOptions?.length === 1')

  prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
  km-inner-loading(:showing='loading')
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { notify } from '@shared/utils/notify'

export default {
  setup() {
    const { draft, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants,
            setSelectedVariant, createVariant, deleteVariant, activateVariant,
            save, revert, refetch, buildPayload } = useVariantEntityDetail('retrieval')
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
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    selected_variant: {
      get() {
        return this.getVariantLabel(this.selectedVariant)
      },
      set(value) {
        this.setSelectedVariant(value.value)
      },
    },
    variantOptions() {
      return this.draft?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
        value: el.variant,
        active_variant: el.variant == this.draft?.active_variant,
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

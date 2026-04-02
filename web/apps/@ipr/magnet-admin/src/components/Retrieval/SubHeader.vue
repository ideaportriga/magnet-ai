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
            q-chip.q-mr-sm(label='Active', color='primary-light', text-color='primary', flat, size='sm')

  .col.q-mx-sm
    km-input-flat.km-description.full-width(placeholder='Description', :modelValue='variant_description', @change='variant_description = $event')
  .col-auto.q-mr-sm
    km-btn.width-100(
      v-if='!isActive',
      label='Activate',
      icon='far fa-circle-check',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='handleActivateVariant'
    )
    q-chip.q-mr-sm(v-if='isActive', label='Active', color='primary-light', text-color='primary')

  q-separator(vertical, color='white')
  .col-auto.text-white.q-mx-md
    km-btn(
      label='Copy to new',
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
import { ref } from 'vue'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  setup() {
    const { draft, isDirty, updateField, updateFields, updateVariantField,
            selectedVariant, activeVariant, variants,
            setSelectedVariant, createVariant, deleteVariant, activateVariant,
            save, revert, refetch, buildPayload } = useVariantEntityDetail('retrieval')
    return {
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
      this.$q.notify({
        message,
        color: 'red-9', textColor: 'white',
        icon: 'error',
        group: 'error',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              callback()
              this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Variant has been deleted.', timeout: 1000 })
            },
          },
        ],
      })
    },
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    handleActivateVariant() {
      this.activateVariant()
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Variant has been activated.', timeout: 1000 })
    },
    addVariant() {
      this.createVariant()
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'New variant has been added.', timeout: 1000 })
    },
    handleDeleteVariant() {
      this.confirm('Are you sure you want to delete this variant?', () => this.deleteVariant())
    },
  },
}
</script>

<template lang="pug">
q-separator.q-my-sm
.row.items-center
  km-select-flat.bg-white(:options='variants', v-model='selected_variant', bg-color='background', height='30px', hasDropdownSearch)
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
      @click='activateVariant'
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
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='deleteVariant', :disable='variants?.length === 1')
</template>
<script>
import { computed, ref } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useApiToolDetailStore } from '@/stores/entityDetailStores'
export default {
  setup() {
    const queries = useEntityQueries()
    const apiToolStore = useApiToolDetailStore()
    const { data: listData } = queries.api_tools.useList()
    const { mutateAsync: updateEntity } = queries.api_tools.useUpdate()
    const { mutateAsync: createEntity } = queries.api_tools.useCreate()
    const items = computed(() => listData.value?.items ?? [])
    const selectedVariantName = ref(null)
    return { items, updateEntity, createEntity, apiToolStore, selectedVariantName }
  },
  computed: {
    selected_variant: {
      get() {
        const variantName = this.selectedVariantName || this.apiToolStore.entity?.active_variant
        return { label: this.getVariantLabel(variantName), value: variantName }
      },
      set(value) {
        this.selectedVariantName = value.value
      },
    },
    selectedTool() {
      return this.apiToolStore.entity
    },
    currentVariantName() {
      return this.selectedVariantName || this.apiToolStore.entity?.active_variant
    },
    currentVariant() {
      return this.selectedTool?.variants?.find((v) => v.variant === this.currentVariantName)
    },
    variants() {
      return this.selectedTool?.variants?.map((el) => ({
        label: el.variant.replace('variant_', 'Variant '),
        value: el.variant,
        active_variant: el.variant == this.apiToolStore.entity?.active_variant,
      }))
    },
    isActive() {
      return this.currentVariantName == this.apiToolStore.entity?.active_variant
    },
    variant_description: {
      get() {
        return this.currentVariant?.description
      },
      set(value) {
        if (!this.currentVariant) return
        const variants = [...(this.selectedTool?.variants || [])]
        const idx = variants.findIndex((v) => v.variant === this.currentVariantName)
        if (idx >= 0) {
          variants[idx] = { ...variants[idx], description: value }
          this.apiToolStore.updateProperty({ key: 'variants', value: variants })
        }
      },
    },
  },
  methods: {
    activateVariant() {
      this.apiToolStore.updateProperty({ key: 'active_variant', value: this.currentVariantName })
      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'Variant has been activated.',
        timeout: 1000,
      })
    },
    getVariantLabel(variant) {
      return variant?.replace('variant_', 'Variant ')
    },
    addVariant() {
      const variants = [...(this.selectedTool?.variants || [])]
      const newIndex = variants.length + 1
      const newVariant = {
        variant: `variant_${newIndex}`,
        description: '',
        value: JSON.parse(JSON.stringify(this.currentVariant?.value || {})),
      }
      variants.push(newVariant)
      this.apiToolStore.updateProperty({ key: 'variants', value: variants })
      this.selectedVariantName = newVariant.variant
      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'New variant has been added.',
        timeout: 1000,
      })
    },
    deleteVariant() {
      this.$q.notify({
        message: 'Are you sure you want to delete this variant?',
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
              const variants = (this.selectedTool?.variants || []).filter((v) => v.variant !== this.currentVariantName)
              this.apiToolStore.updateProperty({ key: 'variants', value: variants })
              this.selectedVariantName = variants[0]?.variant || null
              this.$q.notify({
                color: 'green-9', textColor: 'white',
                icon: 'check_circle',
                group: 'success',
                message: 'Variant has been deleted.',
                timeout: 1000,
              })
            },
          },
        ],
      })
    },
  },
}
</script>

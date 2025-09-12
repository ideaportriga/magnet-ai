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
import { useChroma } from '@shared'
export default {
  setup() {
    const { items, update, create, selectedRow } = useChroma('api_tools')
    return { items, update, create, selectedRow }
  },
  computed: {
    selected_variant: {
      get() {
        return { label: this.getVariantLabel(this.$store.getters.selectedApiToolVariant), value: this.$store.getters.selectedApiToolVariant }
      },
      set(value) {
        this.$store.commit('setSelectedApiToolVariant', value.value)
      },
    },
    selectedTool() {
      return this.$store.getters.api_tool
    },
    variants() {
      return this.selectedTool?.variants?.map((el) => ({
        label: el.variant.replace('variant_', 'Variant '),
        value: el.variant,
        active_variant: el.variant == this.$store.getters.api_tool?.active_variant,
      }))
    },
    isActive() {
      return this.$store.getters.selectedApiToolVariant == this.$store.getters.api_tool?.active_variant
    },
    variant_description: {
      get() {
        return this.$store.getters.api_tool_variant?.description
      },
      set(value) {
        this.$store.commit('updateNestedApiToolProperty', { path: 'description', value })
      },
    },
  },
  methods: {
    activateVariant() {
      this.$store.commit('activateApiToolVariant')
      this.$q.notify({
        position: 'top',
        message: 'Variant has been activated.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    getVariantLabel(variant) {
      return variant?.replace('variant_', 'Variant ')
    },
    addVariant() {
      this.$store.commit('createApiToolVariant')
      this.$q.notify({
        position: 'top',
        message: 'New variant has been added.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    deleteVariant() {
      this.$q.notify({
        message: 'Are you sure you want to delete this variant?',
        color: 'error-text',
        position: 'top',
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
              // notify with success
              this.$store.commit('deleteApiToolVariant')
              this.$q.notify({
                position: 'top',
                message: 'Variant has been deleted.',
                color: 'positive',
                textColor: 'black',
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

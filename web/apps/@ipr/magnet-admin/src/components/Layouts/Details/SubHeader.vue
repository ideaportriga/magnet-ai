<template lang="pug">
q-separator.q-my-sm
.row.items-center
  km-select-flat.bg-white(
    :options='variantsOptions',
    :modelValue='variantValue',
    @update:modelValue='selectVariant',
    bg-color='background',
    height='30px',
    hasDropdownSearch
  )
    template(#option='{ itemProps, select, option }')
      q-item.bb-border(clickable, v-bind='itemProps', dense, @click='select(option)')
        q-item-section
          q-item-label.km-label {{ option.label }}
        q-item-section(v-if='option?.active_variant', avatar)
          q-chip.q-mr-sm(:label='m.common_activate()', color='primary-light', text-color='primary', flat, size='sm')
  .col.q-mx-sm
    km-input-flat.km-description.full-width(:placeholder='m.common_description()', :modelValue='variant_description', @change='updateVariantDescription')
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
      @click='activateVariant'
    )
    q-chip.q-mr-sm(v-if='isActive', :label='m.common_activate()', color='primary-light', text-color='primary')
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
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='deleteVariant', :disable='variants?.length === 1')
</template>

<script setup>
/* eslint-disable */
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useNotify } from '@/composables/useNotify'

const $q = useQuasar()
const { notifySuccess } = useNotify()

const props = defineProps({
  variants: {
    type: Array,
    default: () => [],
  },
  selectedVariant: {
    type: Object,
    default: () => {},
  },
  activeVariant: {
    type: String,
    default: '',
  },
})
const emit = defineEmits(['addVariant', 'deleteVariant', 'activateVariant', 'selectVariant', 'updateVariantProperty'])

const isActive = computed(() => props.activeVariant === props.selectedVariant)
const variant_description = computed(() => props.selectedVariant?.description)

const getVariantLabel = (variant) => {
  return variant?.replace('variant_', 'Variant ')
}

const variantsOptions = computed(() => {
  return props.variants.map((variant) => ({
    label: getVariantLabel(variant.variant),
    value: variant.variant,
    active_variant: variant.variant === props.activeVariant,
  }))
})
const variantValue = computed(() => {
  return { label: getVariantLabel(props.selectedVariant), value: props.selectedVariant }
})

const activateVariant = () => {
  emit('activateVariant')
  notifySuccess('Variant has been activated.')
}
const addVariant = () => {
  emit('addVariant')
  notifySuccess('New variant has been added.')
}
const deleteVariant = () => {
  $q.notify({
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
          emit('deleteVariant')
          notifySuccess('Variant has been deleted.')
        },
      },
    ],
  })
}
const selectVariant = ({ value }) => {
  emit('selectVariant', value)
}

const updateVariantDescription = (value) => {
  emit('updateVariantProperty', { key: 'description', value })
}
</script>

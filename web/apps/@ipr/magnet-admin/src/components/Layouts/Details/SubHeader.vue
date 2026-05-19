<template>
  <div>
    <km-separator class="my-sm" />
    <div class="cluster">
      <km-dropdown-select :model-value="selectedVariantValue" :options="variantsOptions" @update:model-value="selectVariant" />
      <div class="flex-1 mx-sm">
        <km-input-flat class="km-description full-width" :placeholder="m.common_description()" :model-value="variant_description" :readonly="readonly" @change="updateVariantDescription" />
      </div>
      <div class="flex-none mr-sm">
        <km-btn v-if="!readonly && !isActive" class="width-100" :label="m.common_activate()" icon="check" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="activateVariant" />
        <km-chip v-if="isActive" class="mr-sm" :label="m.common_active()" tone="brand" />
      </div>
      <km-separator v-if="!readonly" vertical tone="inverse" />
      <div v-if="!readonly" class="flex-none text-white mx-md">
        <km-btn :label="m.common_copyToNew()" icon="add" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="addVariant" />
      </div>
      <div v-if="!readonly" class="flex-none text-white mr-md">
        <km-btn class="mx-xs" flat :icon="&quot;delete&quot;" icon-size="16px" size="13px" :disable="variants?.length === 1" @click="deleteVariant" />
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable */
import { m } from '@/paraglide/messages'
import { computed } from 'vue'
import { useNotify } from '@/composables/useNotify'
import KmDropdownSelect from '@ds/components/domain/KmDropdownSelect.vue'

const { notifySuccess, notifyConfirm } = useNotify()

const props = defineProps({
  variants: {
    type: Array,
    default: () => [],
  },
  selectedVariant: {
    type: [String, Object],
    default: '',
  },
  activeVariant: {
    type: String,
    default: '',
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['addVariant', 'deleteVariant', 'activateVariant', 'selectVariant', 'updateVariantProperty'])

const selectedVariantValue = computed(() => {
  if (props.selectedVariant && typeof props.selectedVariant === 'object') {
    return props.selectedVariant.variant ?? props.selectedVariant.value
  }
  return props.selectedVariant
})
const selectedVariantRecord = computed(() => {
  return props.variants.find((variant) => variant.variant === selectedVariantValue.value) ?? (typeof props.selectedVariant === 'object' ? props.selectedVariant : null)
})
const isActive = computed(() => props.activeVariant === selectedVariantValue.value)
const variant_description = computed(() => selectedVariantRecord.value?.description)

const getVariantLabel = (variant) => {
  return variant?.replace('variant_', 'Variant ')
}

const variantsOptions = computed(() => {
  return props.variants.map((variant) => ({
    label: getVariantLabel(variant.variant),
    value: variant.variant,
    badgeLabel: variant.variant === props.activeVariant ? m.common_active() : '',
    badgeTone: 'brand',
    badgeIcon: 'check',
  }))
})
const activateVariant = () => {
  if (props.readonly) return
  emit('activateVariant')
  notifySuccess('Variant has been activated.')
}
const addVariant = () => {
  if (props.readonly) return
  emit('addVariant')
  notifySuccess('New variant has been added.')
}
const deleteVariant = () => {
  if (props.readonly) return
  notifyConfirm({
    message: 'Are you sure you want to delete this variant?',
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    onConfirm: () => {
      emit('deleteVariant')
      notifySuccess('Variant has been deleted.')
    },
  })
}
const selectVariant = (value) => {
  emit('selectVariant', value)
}

const updateVariantDescription = (value) => {
  if (props.readonly) return
  emit('updateVariantProperty', { key: 'description', value })
}
</script>

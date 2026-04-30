<template>
  <div class="flex-1" v-bind="$attrs">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ label }}</div>
    <div class="cluster gap-sm relative-position" data-wrap="no">
      <km-input class="full-width" :model-value="localValue" :readonly="!editMode" :placeholder="localPlaceholder" @update:model-value="emit(&quot;update:value&quot;, $event)" />
      <div class="controls full-height cluster">
        <km-btn v-if="!editMode" icon="edit" flat icon-size="12px" size="xs" @click="enterEditMode" />
        <km-btn v-if="editMode &amp;&amp; !isNew" icon="close" flat icon-size="12px" size="xs" @click="cancelEditMode" />
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps({
  value: {
    type: [String, Boolean],
    required: true,
  },
  encryptedValue: {
    type: [String, Boolean],
    required: true,
  },
  label: {
    type: String,
    default: 'Value',
  },
  placeholder: {
    type: String,
    default: 'Enter value',
  },
  no_value_placeholder: {
    type: String,
    default: 'Enter new value',
  },
  fakeEncryptedValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:value'])
const isNew = computed(() => !props.encryptedValue)
const editMode = ref(isNew.value)

const localPlaceholder = computed(() => {
  if (isNew.value) {
    return props.placeholder
  }
  return props.no_value_placeholder
})
const localValue = computed(() => {
  if (!editMode.value) {
    if (props.fakeEncryptedValue) {
      return props.fakeEncryptedValue
    }
    return props.encryptedValue || ''
  }
  return props.value || ''
})

const cancelEditMode = () => {
  editMode.value = false
  emit('update:value', null)
}
const enterEditMode = () => {
  editMode.value = true
  emit('update:value', '')
}

watch(
  () => props.encryptedValue,
  (newVal) => {
    if (newVal) {
      editMode.value = false
    }
  }
)
</script>
<style scoped>
.controls {
  position: absolute;
  inset-inline-end: 5px;
  inset-block-start: 0;
}
</style>

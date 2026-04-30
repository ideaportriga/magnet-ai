<template>
  <div class="cluster mt-md" data-gap="sm" data-wrap="no">
    <div class="flex-1">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_key() }}</div>
      <km-input :model-value="itemKey" :readonly="!isNew" @update:model-value="update(itemKey, $event, value)" />
    </div>
    <div class="flex-1">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_value() }}</div>
      <div class="cluster gap-sm relative-position" data-wrap="no">
        <km-input class="full-width" :model-value="getSecretDisplayValue(itemKey, value)" :readonly="!editMode" :placeholder="!isNew ? m.common_enterNewValue() : &quot;&quot;" @update:model-value="updateSecret(itemKey, itemKey, $event)" />
        <div class="controls full-height cluster">
          <km-btn v-if="!editMode" icon="edit" flat icon-size="12px" size="xs" @click="editMode = !editMode" />
          <km-btn v-if="editMode &amp;&amp; !isNew" icon="close" flat icon-size="12px" size="xs" @click="cancelEditMode" />
          <!--km-btn(icon='check' flat iconSize='12px' @click='editMode = false' size='xs' v-if='editMode && !isNew')-->
        </div>
      </div>
    </div>
    <div class="flex-none">
      <div class="km-field text-secondary-text pb-xs pl-sm">&nbsp;</div>
      <km-btn icon="delete" size="sm" flat tone="danger" @click="removeSecret(itemKey)" />
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps({
  itemKey: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
  isNew: {
    type: Boolean,
    required: false,
    default: false,
  },
})

const emit = defineEmits(['update', 'delete'])

const getSecretDisplayValue = (key, value) => {
  if (!editMode.value && !props.value) {
    return '*****'
  } else {
    return value || ''
  }
}

const editMode = ref(props.value.length || props.isNew)

const cancelEditMode = () => {
  editMode.value = false
  emit('update', props.itemKey, props.itemKey, '')
}

const update = (key, newKey, newValue) => {
  emit('update', key, newKey, newValue)
}

const updateSecret = (key, newKey, newValue) => {
  emit('update', key, newKey, newValue)
}

const removeSecret = (key) => {
  emit('delete', key)
}
</script>
<style scoped>
.controls {
  position: absolute;
  inset-inline-end: 5px;
  inset-block-start: 0;
}
</style>

<template>
  <kg-dialog-base
    :model-value="showDialog"
    :title="`Add to Schema: ${discoveredField?.name || 'Field'}`"
    :subtitle="discoveredField?.name"
    confirm-label="Continue"
    size="md"
    :disable-confirm="!canContinue"
    @update:model-value="$emit('update:show-dialog', $event)"
    @cancel="$emit('update:show-dialog', false)"
    @confirm="handleConfirm"
  >
    <!-- Action Selection -->
    <kg-dialog-section
      title="Choose Action"
      description="Select how you want to add this discovered field to your schema."
      icon="add_circle"
      icon-color="primary"
    >
      <kg-tile-select v-model="selectedAction" :options="actionOptions" :cols="2" />
    </kg-dialog-section>

    <!-- Field Selection (shown when linking to existing) -->
    <kg-dialog-section
      v-if="selectedAction === 'link'"
      title="Select Schema Field"
      description="Choose which existing schema field to link this discovered field to."
      icon="link"
      icon-color="teal-7"
    >
      <div v-if="existingFields.length === 0" class="no-fields-message">
        <q-icon name="info" size="24px" color="grey-5" />
        <span>No schema fields defined yet. Please create a new field instead.</span>
      </div>
      <q-list v-else class="field-list" bordered separator>
        <q-item
          v-for="field in existingFields"
          :key="field.id"
          clickable
          :active="selectedFieldId === field.id"
          active-class="field-item--active"
          class="field-item"
          @click="selectedFieldId = field.id"
        >
          <q-item-section side>
            <q-radio v-model="selectedFieldId" :val="field.id" color="primary" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="field-item__name">{{ field.display_name || field.name }}</q-item-label>
            <q-item-label caption class="field-item__meta">
              <span v-if="field.description" class="field-item__description">{{ field.description }}</span>
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgTileSelect, type TileOption } from '../common'
import { MetadataDiscoveredField, MetadataFieldDefinition } from './models'

const props = defineProps<{
  showDialog: boolean
  discoveredField: MetadataDiscoveredField | null
  existingFields: MetadataFieldDefinition[]
}>()

const emit = defineEmits<{
  (e: 'update:show-dialog', value: boolean): void
  (e: 'create-new', field: MetadataDiscoveredField): void
  (e: 'link-existing', payload: { discovered: MetadataDiscoveredField; targetFieldId: string }): void
}>()

const selectedAction = ref<'create' | 'link'>('create')
const selectedFieldId = ref<string>('')

const actionOptions: TileOption[] = [
  {
    value: 'create',
    label: 'Create New Field',
    icon: 'add',
    description: 'Define a new schema field based on this discovered field.',
  },
  {
    value: 'link',
    label: 'Link to Existing',
    icon: 'link',
    description: 'Map this discovered field to an existing schema field.',
  },
]

const canContinue = computed(() => {
  if (selectedAction.value === 'create') {
    return true
  }
  // For link action, must have a field selected and fields must exist
  return selectedAction.value === 'link' && selectedFieldId.value && props.existingFields.length > 0
})

const handleConfirm = () => {
  if (!props.discoveredField) return

  if (selectedAction.value === 'create') {
    emit('create-new', props.discoveredField)
  } else if (selectedAction.value === 'link' && selectedFieldId.value) {
    emit('link-existing', {
      discovered: props.discoveredField,
      targetFieldId: selectedFieldId.value,
    })
  }
  emit('update:show-dialog', false)
}

// Reset state when dialog opens
watch(
  () => props.showDialog,
  (open) => {
    if (open) {
      selectedAction.value = 'create'
      selectedFieldId.value = props.existingFields[0]?.id || ''
    }
  }
)
</script>

<style scoped>
.no-fields-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
}

.field-list {
  border-radius: 8px;
  overflow: hidden;
}

.field-item {
  transition: background-color 0.15s ease;
}

.field-item:hover {
  background-color: #f9fafb;
}

.field-item--active {
  background-color: color-mix(in srgb, var(--q-primary) 8%, white) !important;
}

.field-item__name {
  font-weight: 500;
  font-size: 13px;
  color: #1f2937;
}

.field-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.field-item__description {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}
</style>

<template>
  <kg-dialog-base
    :model-value="showDialog"
    :title="m.knowledgeGraph_addToSchema({ name: discoveredField?.name || 'Field' })"
    :subtitle="discoveredField?.name"
    :confirm-label="m.common_continue()"
    size="md"
    :disable-confirm="!canContinue"
    @update:model-value="$emit('update:show-dialog', $event)"
    @cancel="$emit('update:show-dialog', false)"
    @confirm="handleConfirm"
  >
    <!-- Action Selection -->
    <kg-dialog-section
      :title="m.knowledgeGraph_chooseAction()"
      :description="m.knowledgeGraph_chooseActionDesc()"
      icon="add_circle"
      tone="brand"
    >
      <kg-tile-select v-model="selectedAction" :options="actionOptions" :cols="2" />
    </kg-dialog-section>

    <!-- Field Selection (shown when linking to existing) -->
    <kg-dialog-section
      v-if="selectedAction === 'link'"
      :title="m.knowledgeGraph_selectSchemaField()"
      :description="m.knowledgeGraph_selectSchemaFieldDesc()"
      icon="link"
      tone="accent"
    >
      <div v-if="existingFields.length === 0" class="no-fields-message">
        <km-glyph name="info" size="24px" tone="muted" />
        <span>{{ m.knowledgeGraph_noSchemaFieldsYet() }}</span>
      </div>
      <ul v-else class="km-list field-list" bordered separator>
        <li
          v-for="field in existingFields"
          :key="field.id"
          class="km-item field-item"
          clickable
          :active="selectedFieldId === field.id"
          active-class="field-item--active"
          @click="selectedFieldId = field.id"
        >
          <div class="km-item-section" side>
            <km-radio v-model="selectedFieldId" :val="field.id" />
          </div>
          <div class="km-item-section">
            <span class="km-item-label field-item__name">{{ field.display_name || field.name }}</span>
            <span class="km-item-label field-item__meta" caption>
              <span v-if="field.description" class="field-item__description">{{ field.description }}</span>
            </span>
          </div>
        </li>
      </ul>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
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
    label: m.knowledgeGraph_createNewField(),
    icon: 'add',
    description: m.knowledgeGraph_createNewFieldDesc(),
  },
  {
    value: 'link',
    label: m.knowledgeGraph_linkToExisting(),
    icon: 'link',
    description: m.knowledgeGraph_linkToExistingDesc(),
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
  background: var(--ds-color-background);
  border-radius: var(--ds-radius-lg);
  color: var(--ds-color-secondary-text);
  font-size: var(--ds-font-size-label);
}

.field-list {
  border-radius: var(--ds-radius-lg);
  overflow: hidden;
}

.field-item {
  transition: background-color 0.15s ease;
}

.field-item:hover {
  background-color: var(--ds-color-background);
}

.field-item--active {
  background-color: var(--ds-color-primary-bg) !important;
}

.field-item__name {
  font-weight: 500;
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
}

.field-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-block-start: 2px;
}

.field-item__description {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-secondary-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-inline-size: 300px;
}
</style>

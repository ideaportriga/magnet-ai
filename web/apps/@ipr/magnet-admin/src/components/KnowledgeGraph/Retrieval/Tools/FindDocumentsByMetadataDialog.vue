<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="localTool?.label"
    confirm-label="Apply"
    size="md"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="$emit('update:modelValue', false)"
    @confirm="save"
  >
    <!-- Tool Description -->
    <kg-prompt-section
      v-model="localTool.description"
      title="Tool Description"
      description="Explain when the agent should use this tool. This description will be used to generate a prompt for the agent."
    />

    <!-- Search Settings Section -->
    <kg-dialog-section
      title="Search Control"
      description="Select the control mode for metadata filtering. This determines whether the agent, the caller, or both specify filter criteria."
      icon="tune"
      icon-color="teal-7"
    >
      <template #header-actions>
        <kg-section-control v-model="localTool.searchControl" :options="searchControlOptions" />
      </template>

      <div class="column q-gap-16">
        <!-- Control mode description -->
        <div class="control-description">
          <span class="text-grey-8">{{ controlModeDescription }}</span>
        </div>

        <!-- Merge Strategy - only shown for 'collaborative' mode -->
        <div v-if="localTool.searchControl === 'collaborative'" class="merge-strategy-section">
          <div class="km-input-label q-pb-sm">Conflict resolution (Agent vs External)</div>
          <km-select v-model="localTool.filterMergeStrategy" :options="mergeStrategyOptions" emit-value map-options />
        </div>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgPromptSection, KgSectionControl, type ControlOption } from '../../common'

const props = defineProps<{
  modelValue: boolean
  tool: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', tool: any): void
}>()

const localTool = ref<any>(null)

const searchControlOptions: ControlOption[] = [
  { label: 'Agent Controls', value: 'agent' },
  { label: 'Collaborative', value: 'collaborative' },
  { label: 'External Control', value: 'external' },
]

const mergeStrategyOptions = [
  { label: 'Merge filters (AND)', value: 'merge_and' },
  { label: 'Merge filters (OR)', value: 'merge_or' },
  { label: 'Agent takes priority', value: 'agent_priority' },
  { label: 'External takes priority', value: 'external_priority' },
]

const controlModeDescription = computed(() => {
  switch (localTool.value?.searchControl) {
    case 'agent':
      return "The agent will autonomously decide which metadata fields to use for filtering documents based on the user's query."
    case 'collaborative':
      return 'Both the agent and external callers (direct users, API consumers) can provide metadata filters. Configure how to handle overlapping filters below.'
    case 'external':
      return 'The agent will not add its own metadata filters. Only filters provided by external callers (API clients or other systems) will be used.'
    default:
      return ''
  }
})

watch(
  () => props.tool,
  (newVal) => {
    if (newVal) {
      localTool.value = JSON.parse(JSON.stringify(newVal))
      // Set default merge strategy if not present
      if (!localTool.value.filterMergeStrategy) {
        localTool.value.filterMergeStrategy = 'merge_and'
      }
    }
  },
  { immediate: true, deep: true }
)

const save = () => {
  emit('save', localTool.value)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.control-description {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background-color: var(--q-grey-2, #f5f5f5);
  border-radius: 8px;
  line-height: 1.5;
}

.merge-strategy-section {
  padding-top: 8px;
}
</style>

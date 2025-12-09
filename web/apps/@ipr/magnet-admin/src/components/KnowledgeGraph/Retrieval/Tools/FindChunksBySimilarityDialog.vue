<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="q-pa-sm" style="min-width: 720px; max-width: 720px">
      <q-card-section>
        <div class="row items-center">
          <div class="col row items-center no-wrap">
            <div class="km-heading-7">{{ localTool?.label }}</div>
          </div>
          <q-btn icon="close" flat round dense color="grey-6" @click="$emit('update:modelValue', false)" />
        </div>
      </q-card-section>

      <q-card-section class="column q-gap-16 q-pa-md">
        <!-- Tool Description -->
        <DialogPromptSection
          v-model="localTool.description"
          title="Tool Description"
          description="Explain when the agent should use this tool. This description will be used to generate a prompt for the agent."
        />

        <!-- Search Settings Section -->
        <dialog-section
          title="Search Settings"
          description="Tune tool settings to control the scope and precision of the search. Choose whether the agent can override the search method or must follow this configuration."
          icon="tune"
          color="teal-7"
        >
          <template #header-actions>
            <q-btn-toggle
              v-model="localTool.searchControl"
              class="section-control-toggle"
              no-caps
              rounded
              unelevated
              toggle-color="primary"
              color="grey-3"
              text-color="grey-8"
              dense
              :options="controlOptions"
            />
          </template>

          <div class="column q-gap-16 section-fields" :class="{ 'section-fields-disabled': localTool.searchControl === 'agent' }">
            <div class="row q-col-gutter-x-lg">
              <div :class="{ 'col-6': localTool.searchMethod === 'hybrid', 'full-width': localTool.searchMethod !== 'hybrid' }">
                <div class="row items-center q-gutter-x-sm q-pb-sm">
                  <div class="km-input-label">Method</div>
                  <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium" />
                </div>
                <km-select v-model="localTool.searchMethod" :options="searchMethodOptions" emit-value map-options disable />
              </div>
              <div class="col-6">
                <!-- Hybrid Weight - only shown when hybrid method selected -->
                <div v-if="localTool.searchMethod === 'hybrid'">
                  <div class="km-input-label q-pb-12">
                    <span>Hybrid Score Distribution</span>
                  </div>
                  <div class="row items-center q-gutter-x-md">
                    <span class="km-input-label text-primary text-weight-bold">Keyword {{ ((1 - localTool.hybridWeight) * 100).toFixed(0) }}%</span>
                    <q-slider v-model="localTool.hybridWeight" :min="0" :max="1" :step="0.05" color="primary" class="col" />
                    <span class="km-input-label text-primary text-weight-bold">{{ (localTool.hybridWeight * 100).toFixed(0) }}% Vector</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="row q-col-gutter-x-lg">
              <div class="col-6">
                <div class="km-input-label row justify-between q-pb-12">
                  <span>Score Threshold</span>
                  <span class="text-primary text-weight-bold">{{ localTool.scoreThreshold }}</span>
                </div>
                <q-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" color="primary" />
              </div>
              <div class="col-6">
                <div class="km-input-label q-pb-sm">Result Limit</div>
                <km-input v-model.number="localTool.limit" type="number" :min="1" :max="20" />
              </div>
            </div>
          </div>
        </dialog-section>

        <!-- Context Expansion Section -->
        <dialog-section
          title="Context Expansion"
          description="Enrich search results by including related chunks from the knowledge graph. Choose whether the agent can override the context expansion or must follow this configuration."
          icon="hub"
          color="purple-7"
        >
          <template #title-badge>
            <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium q-mt-xs" />
          </template>
          <template #header-actions>
            <q-btn-toggle
              v-model="localTool.contextControl"
              class="section-control-toggle"
              no-caps
              rounded
              unelevated
              toggle-color="primary"
              color="grey-3"
              text-color="grey-8"
              dense
              :options="controlOptions"
              disable
            />
          </template>

          <div class="column q-gap-16 section-fields section-fields-disabled">
            <div class="row q-col-gutter-x-lg">
              <div class="col-6">
                <q-toggle :model-value="false" label="Include Referenced Chunks" />
                <div class="km-description text-secondary-text q-ml-sm">Include chunks that are referenced by the matched chunks.</div>
              </div>
              <div class="col-6">
                <q-toggle :model-value="false" label="Include Adjacent Chunks" />
                <div class="km-description text-secondary-text q-ml-sm">Include adjacent chunks that share the same parent.</div>
              </div>
            </div>
          </div>
        </dialog-section>
      </q-card-section>

      <q-card-actions class="q-pa-md">
        <km-btn label="Cancel" flat color="primary" @click="$emit('update:modelValue', false)" />
        <q-space />
        <km-btn label="Apply" @click="save" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import DialogSection from '../DialogSection.vue'
import DialogPromptSection from '../DialogPromptSection.vue'
import { searchMethodOptions } from '../models'

const props = defineProps<{
  modelValue: boolean
  tool: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', tool: any): void
}>()

const localTool = ref<any>(null)

const controlOptions = [
  { label: 'Agent decides', value: 'agent' },
  { label: 'Static', value: 'configuration' },
]

watch(
  () => props.tool,
  (newVal) => {
    if (newVal) {
      localTool.value = JSON.parse(JSON.stringify(newVal))
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
.section-fields {
  transition: opacity 0.2s ease;
}

.section-fields-disabled {
  opacity: 0.5;
  pointer-events: none;
}

.section-control-toggle :deep(.q-btn) {
  padding: 4px 8px;
  min-height: 24px;
  font-size: 12px;
  font-weight: 500;
}

.section-control-toggle :deep(.q-btn .block) {
  font-size: 12px;
}
</style>

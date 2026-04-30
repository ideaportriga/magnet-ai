<template>
  <div class="flex-1">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ title }}</div>
    <div v-if="!editMode" class="cluster ba-border border-radius-12 p-lg" @mouseenter="hover = true" @mouseleave="hover = false">
      <div class="flex-1">
        <div class="km-heading">{{ defaultModel?.display_name || '-' }}</div>
        <div class="cluster" data-gap="sm">
          <div class="km-description">Model Providers</div>
          <km-chip v-if="defaultModel?.provider_name" class="bg-in-progress" size="19px">
            <div class="text-placeholder km-small-chip px-xs">{{ defaultModel?.provider_name }}</div>
          </km-chip>
        </div>
      </div>
      <div class="flex-none">
        <km-btn v-if="hover" icon="edit" flat icon-size="14px" @click="editMode = !editMode" />
      </div>
    </div>
    <div v-if="editMode" class="cluster ba-primary border-radius-12 p-lg">
      <div class="flex-1">
        <div class="km-field text-secondary-text pb-xs pl-sm">Default Model</div>
        <km-select v-model="selectedModel" :options="modelOptions" option-value="system_name" option-label="display_name" emit-value map-options>
          <template #option="{ itemProps, opt, toggleOption }">
            <li class="km-item ba-border" v-bind="itemProps" dense @click="toggleOption(opt)">
              <div class="km-item-section">
                <span class="km-item-label km-label">{{ opt.display_name }}</span>
                <div v-if="opt.provider_system_name" class="cluster mt-xs">
                  <km-chip tone="brand" size="sm" dense>{{ opt.provider_system_name }}</km-chip>
                </div>
              </div>
            </li>
          </template>
        </km-select>
        <div class="cluster pt-lg" data-justify="between">
          <km-btn :label="m.common_cancel()" flat @click="cancelEdit" />
          <km-btn :label="m.common_save()" @click="saveDefault" />
        </div>
      </div>
    </div>
  </div>
  <km-popup-confirm :visible="showDialog" confirm-button-label="OK, change default" notification-icon="info" :cancel-button-label="m.common_cancel()" @cancel="showDialog = false" @confirm="confirmChange">
    <div class="cluster km-heading-7" data-justify="center">You are about to change default model</div>
    <div class="cluster text-center" data-justify="center">This will affect newly created Prompt Templates and any existing</div>
    <div class="cluster text-center" data-justify="center">Prompt Templates that have no model selected.</div>
  </km-popup-confirm>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useAppStore } from '@/stores/appStore'
import { useQueryClient } from '@tanstack/vue-query'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  modelType: {
    type: String,
    required: true, // 'prompts', 'embeddings', 're-ranking'
  },
})

const queries = useEntityQueries()
const appStore = useAppStore()
const queryClient = useQueryClient()
const { data: modelListData } = queries.model.useList()
const hover = ref(false)
const editMode = ref(false)
const showDialog = ref(false)
const selectedModel = ref(null)

// Get all models of the specified type
const modelOptions = computed(() => {
  const models = modelListData.value?.items ?? []
  return models.filter((model) => model.type === props.modelType)
})

// Get the default model of the specified type
const defaultModel = computed(() => {
  return modelOptions.value.find((model) => model.is_default)
})

// Initialize selectedModel when defaultModel changes
watch(
  defaultModel,
  (newDefaultModel) => {
    if (newDefaultModel && !editMode.value) {
      selectedModel.value = newDefaultModel.system_name
    }
  },
  { immediate: true }
)

const cancelEdit = () => {
  selectedModel.value = defaultModel.value?.system_name
  editMode.value = false
  hover.value = false
}

const saveDefault = () => {
  if (selectedModel.value === defaultModel.value?.system_name) {
    // No change, just close
    editMode.value = false
    hover.value = false
    return
  }
  showDialog.value = true
}

const confirmChange = async () => {
  const modelToSet = modelOptions.value.find((m) => m.system_name === selectedModel.value)

  if (modelToSet) {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    await fetchData({
      method: 'POST',
      endpoint,
      service: 'model/set_default',
      credentials: 'include',
      body: JSON.stringify({
        type: modelToSet.type,
        system_name: modelToSet.system_name,
      }),
      headers: { 'Content-Type': 'application/json' },
    })
    await queryClient.invalidateQueries({ queryKey: ['model'] })
  }

  showDialog.value = false
  editMode.value = false
  hover.value = false
}
</script>

<template lang="pug">
.col
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ title }}
  .row.ba-border.border-radius-12.q-pa-16(v-if='!editMode', @mouseenter='hover = true', @mouseleave='hover = false')
    .col
      .km-heading {{ defaultModel?.display_name || '-' }}
      .row.items-center.q-gap-8
        .km-description Model Providers
        km-chip.bg-in-progress(size='19px', v-if='defaultModel?.provider_name')
          .text-placeholder.km-small-chip.q-px-4 {{ defaultModel?.provider_name }}
    .col-auto
      km-btn(icon='fa fa-pen', flat, iconSize='14px', @click='editMode = !editMode', v-if='hover')
  .row.ba-primary.border-radius-12.q-pa-16(v-if='editMode')
    .col
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Default Model
      km-select(v-model='selectedModel', :options='modelOptions', option-value='system_name', option-label='display_name', emit-value, map-options)
        template(v-slot:option='{ itemProps, opt, selected, toggleOption }')
          q-item.ba-border(v-bind='itemProps', dense, @click='toggleOption(opt)')
            q-item-section
              q-item-label.km-label {{ opt.display_name }}
              .row.q-mt-xs(v-if='opt.provider_system_name')
                q-chip(color='primary-light', text-color='primary', size='sm', dense) {{ opt.provider_system_name }}
      .row.q-pt-16.justify-between
        km-btn(label='Cancel', flat, @click='cancelEdit')
        km-btn(label='Save', @click='saveDefault')

km-popup-confirm(
  :visible='showDialog',
  confirmButtonLabel='OK, change default',
  notificationIcon='fas fa-circle-info',
  cancelButtonLabel='Cancel',
  @cancel='showDialog = false',
  @confirm='confirmChange'
)
  .row.item-center.justify-center.km-heading-7 You are about to change default model
  .row.text-center.justify-center This will affect newly created Prompt Templates and any existing
  .row.text-center.justify-center Prompt Templates that have no model selected.
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'

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

const store = useStore()
const hover = ref(false)
const editMode = ref(false)
const showDialog = ref(false)
const selectedModel = ref(null)

// Get all models of the specified type
const modelOptions = computed(() => {
  const models = store.getters['chroma/model']?.items || []
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
    await store.dispatch('modelConfig/setDefault', modelToSet)
  }

  showDialog.value = false
  editMode.value = false
  hover.value = false
}
</script>

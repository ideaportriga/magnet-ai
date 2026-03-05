<template lang="pug">
.row.q-gap-16.flex-wrap
  model-providers-default-models-item(title='Chat completion', modelType='prompts')
  model-providers-default-models-item(title='Vector embedding', modelType='embeddings')
  model-providers-default-models-item(title='Re-ranking', modelType='re-ranking')
  model-providers-default-models-item(title='Speech-to-Text', modelType='stt')
  model-providers-default-models-item(title='Text-to-Speech', modelType='tts')
  model-providers-default-models-item(title='Image Generation', modelType='image_generation')
</template>
<script setup>
import { onMounted } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

onMounted(() => {
  // Load models if not already loaded
  if (!store.getters['chroma/model']?.items?.length) {
    store.dispatch('chroma/get', { entity: 'model' })
  }
})
</script>

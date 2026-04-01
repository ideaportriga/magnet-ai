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
import { useEntityQueries } from '@/queries/entities'

const queries = useEntityQueries()
queries.model.useList()
</script>

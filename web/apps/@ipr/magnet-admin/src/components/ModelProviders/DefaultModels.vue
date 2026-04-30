<template>
  <div class="cluster" data-gap="lg">
    <model-providers-default-models-item title="Chat completion" model-type="prompts" />
    <model-providers-default-models-item title="Vector embedding" model-type="embeddings" />
    <model-providers-default-models-item title="Re-ranking" model-type="re-ranking" />
    <model-providers-default-models-item title="Speech-to-Text" model-type="stt" />
    <model-providers-default-models-item title="Text-to-Speech" model-type="tts" />
    <model-providers-default-models-item title="Image Generation" model-type="image_generation" />
  </div>
</template>
<script setup>
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'

const queries = useEntityQueries()
queries.model.useList()
</script>

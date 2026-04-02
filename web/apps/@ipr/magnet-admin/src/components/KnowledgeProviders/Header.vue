<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ server?.name }}
</template>
<script setup>
import { useEntityDetail } from '@/composables/useEntityDetail'

const { draft } = useEntityDetail('provider')
const server = draft
</script>

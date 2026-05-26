<template>
  <div class="column q-gap-32">
    <section v-if="span?.input" class="column q-gap-12">
      <header class="section-header">
        <span class="section-title">Input Parameters</span>
      </header>
      <observability-traces-default-span-renderer :value="span?.input" />
    </section>
    <template v-if="toolType === 'search'">
      <section class="column q-gap-12">
        <header class="section-header">
          <span class="section-title">Search results</span>
          <span class="section-meta">{{ recordsFound }}</span>
        </header>
        <template v-if="Array.isArray(span?.output) && span.output.length > 0">
          <div v-for="(document, index) in span.output" :key="index" class="col-auto ba-border border-radius-8" style="max-width: 463px">
            <div class="row q-gap-12 q-pa-sm bg-light no-wrap cursor-pointer" style="border-radius: 8px 8px 0 0" @click="toggleCollapse(index)">
              <div class="row" style="font-size: 13px">
                {{ document?.metadata?.title ?? document?.metadata?.name ?? document?.title }}
              </div>
              <q-space />
              <div class="row" style="font-size: 13px">
                {{ formatScore(document?.score) }}
              </div>
              <q-icon v-if="document?.content" :name="collapsed[index] ? 'expand_less' : 'expand_more'" size="16px" />
            </div>
            <div
              v-if="collapsed[index] && document?.content"
              class="row q-pa-sm bt-border"
              style="min-height: 50px; font-size: 13px; white-space: pre-wrap; word-break: break-all"
            >
              {{ document?.content }}
            </div>
          </div>
        </template>
      </section>
    </template>
    <observability-traces-default-span-renderer v-else-if="span?.output" :value="span?.output" label="Outputs" />
  </div>
</template>

<script setup lang="ts">
import { formatScore } from '@shared/utils'
import { computed, ref } from 'vue'

const props = defineProps<{
  span: any
}>()

const toolType = computed(() => props.span?.extra_data?.tool_type)

const recordsFound = computed(() => {
  const output = props.span?.output
  if (Array.isArray(output)) return output.length
  if (output && typeof output.count === 'number') return output.count
  return 0
})

const collapsed = ref<Record<number, boolean>>({})

const toggleCollapse = (index: number) => {
  collapsed.value[index] = !collapsed.value[index]
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e1e4e8;
}
.section-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #6e7681;
}
.section-meta {
  font-size: 11px;
  font-weight: 500;
  color: #8c959f;
  background-color: #f1f3f5;
  border-radius: 999px;
  padding: 1px 8px;
  line-height: 1.4;
}
</style>

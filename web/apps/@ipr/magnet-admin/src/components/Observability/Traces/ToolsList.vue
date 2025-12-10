<template>
  <div class="column q-gap-8">
    <div v-for="(toolCall, index) in tools" :key="getToolKey(toolCall, index)" class="col-auto ba-border border-radius-8 overflow-hidden">
      <div class="row q-pa-sm bg-light items-center q-gap-8">
        <span style="font-size: 13px">
          {{ getFunctionName(toolCall) }}
        </span>
      </div>

      <div class="column bt-border q-pa-sm q-gap-8">
        <div v-if="getDescription(toolCall)" class="text-grey-8" style="font-size: 12px">
          {{ getDescription(toolCall) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
type ToolFunction = {
  name?: string
  description?: string
}

type Tool = {
  id?: string
  type?: string
  function?: ToolFunction
  name?: string
  description?: string
  [key: string]: unknown
}

defineProps<{
  tools: Tool[]
}>()

const getToolKey = (toolCall: Tool, index: number): string => {
  return toolCall.id ?? `${getFunctionName(toolCall)}-${index}`
}

const getFunctionName = (toolCall: Tool): string => {
  return toolCall.function?.name ?? toolCall.name ?? 'Unknown'
}

const getDescription = (toolCall: Tool): string => {
  return toolCall.function?.description ?? toolCall.description ?? ''
}
</script>

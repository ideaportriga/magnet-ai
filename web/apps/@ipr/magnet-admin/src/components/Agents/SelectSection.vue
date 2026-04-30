<template>
  <template v-if="searchResults.length &gt; 0">
    <div class="cluster py-sm px-lg bg-light full-width bb-border cursor-pointer" data-gap="sm" @click.stop="open = !open">
      <km-checkbox :model-value="serverCheckbox" @update:model-value="toggleServerTools" />
      <div class="flex-1">
        <div class="km-title">{{ server.name }}</div>
        <div class="km-description">{{ server.url }}</div>
      </div>
      <km-chip v-if="selectedQty &gt; 0" class="text-primary" tone="brand" :label="m.agents_ofSelected({ selected: selectedQty, total: server.tools.length })" round />
      <km-btn :icon="open ? &quot;o_expand_less&quot; : &quot;o_expand_more&quot;" flat @click.stop="open = !open" />
    </div>
    <div v-if="open" class="stack full-width pl-lg" data-gap="0">
      <template v-for="tool in searchResults" :key="tool.id ?? tool.system_name ?? tool.name">
        <div class="cluster p-sm bg-white full-width gap-sm bb-border">
          <km-checkbox :model-value="isSelected(tool)" @update:model-value="onSelect(tool)" />
          <div class="flex-1">
            <div class="cluster" data-gap="sm">
              <div class="km-title">{{ tool.name }}</div>
              <km-chip v-if="tool.system_name === &quot;fullSearch&quot;" :label="m.agents_fullSearch()" tone="brand" round dense />
            </div>
            <div class="km-description">{{ tool.description }}</div>
          </div>
        </div>
      </template>
    </div>
  </template>
</template>
<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps({
  server: {
    type: Object,
    required: true,
  },
  selected: {
    type: Array,
    required: true,
  },
  openOnMount: {
    type: Boolean,
    default: false,
  },
  searchString: {
    type: String,
    default: '',
  },
  systemNameKey: {
    type: String,
    default: 'name',
  },
  searchFields: {
    type: Array,
    default: () => ['name', 'description'],
  },
  type: {
    type: String,
    required: true,
  },
})

const searchResults = computed(() => {
  const fields = props.searchFields
  const searchString = props.searchString.toLowerCase()
  const seenTools = new Set()
  const tools = []

  if (!searchString.trim()) {
    return props.server.tools || []
  }
  for (const field of fields) {
    const isMatchServer = props.server[field]?.toLowerCase()?.includes(searchString)
    if (isMatchServer) {
      return props.server.tools
    }
  }

  for (const field of fields) {
    const results = (props.server.tools || []).filter((item) => item[field]?.toLowerCase()?.includes(searchString))

    results.forEach((tool) => {
      const toolKey = tool.name
      if (!seenTools.has(toolKey)) {
        seenTools.add(toolKey)
        tools.push(tool)
      }
    })
  }

  return tools
})

const emit = defineEmits(['select', 'selectMultiple'])

const open = ref(props.openOnMount)
const value = ref(false)

const onSelect = (item) => {
  emit('select', {
    id: `${props.server.name}-${item[props.systemNameKey]}`,
    name: item.name,
    system_name: item[props.systemNameKey],
    description: item.description,
    type: props.type,
    tool_provider: props.server.system_name,
  })
}

const serverCheckbox = computed(() => {
  if (selectedQty.value === props.server.tools.length) {
    return true
  }
  if (selectedQty.value === 0) {
    return false
  }
  return null
})

const selectedQty = computed(() => {
  return props.selected.filter((item) => item.tool_provider === props.server.system_name).length
})

const isSelected = (item) => {
  return props.selected.some((selectedItem) => selectedItem.id === `${props.server.name}-${item[props.systemNameKey]}`)
}

const toggleServerTools = () => {
  let targetItems = []
  if (serverCheckbox.value === null) {
    targetItems = searchResults.value.filter((item) => isSelected(item))
  } else if (serverCheckbox.value === true) {
    targetItems = searchResults.value.filter((item) => isSelected(item))
  } else {
    targetItems = searchResults.value.filter((item) => !isSelected(item))
  }
  emit(
    'selectMultiple',
    targetItems.map((item) => ({
      id: `${props.server.name}-${item[props.systemNameKey]}`,
      name: item.name,
      system_name: item[props.systemNameKey],
      description: item.description,
      type: props.type,
      tool_provider: props.server.system_name,
    }))
  )
}
</script>

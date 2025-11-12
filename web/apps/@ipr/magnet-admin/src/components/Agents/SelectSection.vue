<template lang="pug">
template(v-if='searchResults.length > 0')
  .row.q-py-8.q-px-16.bg-light.items-center.full-width.q-gap-8.bb-border.cursor-pointer(@click.stop='open = !open')
    km-checkbox(:model-value='serverCheckbox', @update:model-value='toggleServerTools')
    .col
      .km-title {{ server.name }}
      .km-description {{ server.url }}
    km-chip.text-primary(color='primary-transparent', :label='`${selectedQty} of ${server.tools.length} selected`', round, v-if='selectedQty > 0')
    km-btn(:icon='open ? "o_expand_less" : "o_expand_more"', flat, color='icon', @click.stop='open = !open')
  .column.full-width.q-pl-lg(v-if='open')
    template(v-for='tool in searchResults')
      .row.q-pa-8.bg-white.items-center.full-width.q-gap-8.bb-border
        km-checkbox(:model-value='isSelected(tool)', @update:model-value='onSelect(tool)')
        .col
          .km-title {{ tool.name }}
          .km-description {{ tool.description }}
</template>
<script setup>
import { ref, computed } from 'vue'

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

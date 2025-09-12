<template lang="pug">
.row.q-pa-16.bg-light.items-center.full-width.q-gap-8.bb-border
  km-checkbox(:model-value='serverCheckbox', size='44px', @update:model-value='toggleServerTools')
  .col
    .km-title {{ server.name }}
    .km-description {{ server.url }}
  km-chip.text-primary(color='primary-transparent', :label='`${selectedQty} of ${server.tools.length} selected`', round)
  km-btn(:icon='open ? "o_expand_less" : "o_expand_more"', flat, color='icon', @click='open = !open')
  //- q-icon(:name='open ? "expand_less" : "expand_more"', size='24px', color='icon', @click='open = !open')
.column.full-width.q-pl-lg(v-if='open')
  template(v-for='tool in server.tools')
    .row.q-pa-16.bg-white.items-center.full-width.q-gap-8.bb-border
      km-checkbox(:model-value='isSelected(tool)', size='44px', @update:model-value='onSelect(tool)')
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
})

const emit = defineEmits(['select'])

const open = ref(props.openOnMount)
const value = ref(false)

const onSelect = (item) => {
  emit('select', {
    id: `${props.server.name}-${item.name}`,
    name: item.name,
    system_name: item.name,
    description: item.description,
    type: 'mcp_tool',
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
  return props.selected.some((selectedItem) => selectedItem.id === `${props.server.name}-${item.name}`)
}

const toggleServerTools = () => {
  let targetItems = []
  if (serverCheckbox.value === null) {
    targetItems = props.server.tools.filter((item) => isSelected(item))
  } else if (serverCheckbox.value === true) {
    targetItems = props.server.tools.filter((item) => isSelected(item))
  } else {
    targetItems = props.server.tools.filter((item) => !isSelected(item))
  }
  targetItems.forEach((item) => {
    onSelect(item)
  })
}
</script>

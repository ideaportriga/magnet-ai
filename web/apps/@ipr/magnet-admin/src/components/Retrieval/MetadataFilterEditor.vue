<script setup lang="ts">
/**
 * Filter editor — popover anchored to the trigger that adds/removes
 * conditions for one filter field. Rewritten on `@ds` (DsPopover +
 * DsDropdownMenu) — no more `<km-popup-edit>`/`<km-menu>` and no Quasar
 * type imports.
 */

import _ from 'lodash'
import { computed, ref } from 'vue'
import type { Condition, Filter } from '@shared/types'
import { DsDropdownMenu, DsPopover } from '@ds/primitives'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmInput from '@ds/components/domain/KmInput.vue'
import RetrievalMetadataFilterCondition from './MetadataFilterCondition.vue'

const DEFAULT_T = {
  valueCondition: 'Value condition',
  emptyCondition: 'Empty condition',
  existsCondition: 'Exists condition',
  addCondition: 'Add condition',
  addValueCondition: 'Add value condition',
  undefinedNullOrEmpty: 'undefined, null or empty string',
  exists: 'exists',
  cancel: 'Cancel',
}

const props = defineProps<{
  title: string
  saveButtonLabel: string
  t?: Record<string, string>
}>()

const resolvedT = computed(() => ({ ...DEFAULT_T, ...(props.t ?? {}) }))

const emit = defineEmits<{
  cancel: []
  save: [pendingChanges: Filter, currentFilter: Filter]
}>()

const open = ref(false)
const currentFilter = ref<Filter | null>(null)
const pendingChanges = ref<Filter | null>(null)

const emptyCondition = computed(() => pendingChanges.value?.conditions?.find((c) => c.type === 'empty'))
const existsCondition = computed(() => pendingChanges.value?.conditions?.find((c) => c.type === 'exists'))

const addMenuItems = computed(() => {
  const items: { label: string; onSelect: () => void }[] = [
    { label: resolvedT.value.valueCondition, onSelect: () => addCondition('value') },
  ]
  if (!emptyCondition.value) items.push({ label: resolvedT.value.emptyCondition, onSelect: () => addCondition('empty') })
  if (!existsCondition.value) items.push({ label: resolvedT.value.existsCondition, onSelect: () => addCondition('exists') })
  return items
})

defineExpose({
  show: (filter: Filter) => {
    currentFilter.value = filter
    pendingChanges.value = _.cloneDeep(filter)
    open.value = true
  },
  hide: () => {
    open.value = false
  },
})

function discardChanges() {
  open.value = false
  emit('cancel')
}

function saveChanges() {
  if (pendingChanges.value && currentFilter.value) {
    emit('save', pendingChanges.value, currentFilter.value)
  }
  open.value = false
}

function addCondition(type?: string) {
  if (!pendingChanges.value) return
  if (!type) {
    if (emptyCondition.value && existsCondition.value) {
      type = 'value'
    } else {
      return
    }
  }
  pendingChanges.value.conditions = [...(pendingChanges.value.conditions ?? []), { type, operator: 'equal' } as Condition]

  if (type === 'value') {
    setTimeout(() => {
      const inputs = document.querySelectorAll('.metadata-filter-condition__input input')
      const last = inputs[inputs.length - 1] as HTMLInputElement | undefined
      last?.focus()
    }, 0)
  }
}

function removeCondition(condition: Condition) {
  if (!pendingChanges.value) return
  pendingChanges.value.conditions = pendingChanges.value.conditions?.filter((c) => c !== condition) ?? []
}
</script>

<template>
  <DsPopover v-model:open="open" :width="360">
    <template #trigger>
      <span class="metadata-filter-editor__anchor" />
    </template>

    <div class="metadata-filter-editor stack" data-gap="md">
      <h3 class="metadata-filter-editor__title">{{ title }}</h3>

      <div class="stack" data-gap="sm">
        <KmInput v-if="pendingChanges" v-model="pendingChanges.field" readonly />

        <div class="metadata-filter-editor__conditions stack" data-gap="xs">
          <RetrievalMetadataFilterCondition
            v-for="(condition, index) in pendingChanges?.conditions?.filter((c) => c.type === 'value')"
            :key="index"
            :model-value="condition"
            @remove="removeCondition(condition)"
          />
          <RetrievalMetadataFilterCondition
            v-if="emptyCondition"
            :model-value="emptyCondition"
            readonly
            :placeholder="resolvedT.undefinedNullOrEmpty"
            @remove="removeCondition(emptyCondition)"
          />
          <RetrievalMetadataFilterCondition
            v-if="existsCondition"
            :model-value="existsCondition"
            readonly
            :placeholder="resolvedT.exists"
            @remove="removeCondition(existsCondition)"
          />
        </div>

        <DsDropdownMenu v-if="!emptyCondition || !existsCondition" :items="addMenuItems">
          <template #trigger>
            <KmBtn
              flat
              :label="!emptyCondition || !existsCondition ? resolvedT.addCondition : resolvedT.addValueCondition"
              icon="add"
              icon-size="14px"
              tone="brand"
            />
          </template>
        </DsDropdownMenu>
        <KmBtn
          v-else
          flat
          :label="resolvedT.addValueCondition"
          icon="add"
          icon-size="14px"
          tone="brand"
          @click="addCondition('value')"
        />
      </div>

      <div class="cluster gap-sm" data-justify="end">
        <KmBtn flat :label="resolvedT.cancel" @click="discardChanges" />
        <KmBtn :label="saveButtonLabel" @click="saveChanges" />
      </div>
    </div>
  </DsPopover>
</template>

<style scoped>
.metadata-filter-editor__anchor {
  display: inline-block;
  inline-size: 0;
  block-size: 0;
}
.metadata-filter-editor { max-block-size: 480px; overflow: auto; }
.metadata-filter-editor__title {
  font-size: var(--ds-font-size-body);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.metadata-filter-editor__conditions { max-block-size: 400px; overflow-block: auto; position: relative; }
</style>

<template>
  <q-popup-edit ref="filterPopup" v-model="pendingChanges" persistent fit :cover="false">
    <div class="km-heading-4 q-mb-md">{{ title }}</div>
    <div class="column q-gap-8">
      <km-input v-model="pendingChanges.field" readonly />
      <div style="max-height: 400px; overflow-y: auto">
        <div class="column q-gap-6 q-mt-md relative-position">
          <retrieval-metadata-filter-condition
            v-for="(condition, index) in pendingChanges?.conditions?.filter((c) => c.type === 'value')"
            :key="index"
            :model-value="condition"
            @remove="removeCondition(condition)"
          />
          <retrieval-metadata-filter-condition
            v-if="emptyCondition"
            :model-value="emptyCondition"
            readonly
            placeholder="undefined, null or empty string"
            @remove="removeCondition(emptyCondition)"
          />
          <retrieval-metadata-filter-condition
            v-if="existsCondition"
            :model-value="existsCondition"
            readonly
            placeholder="exists"
            @remove="removeCondition(existsCondition)"
          />
        </div>
      </div>
      <q-btn class="self-start" no-caps padding="5px 10px" color="secondary" text-color="primary" flat @click="addCondition()">
        <q-icon name="fas fa-plus" size="14px" />
        <span class="q-ml-sm">
          {{ !emptyCondition || !existsCondition ? 'Add condition' : 'Add value condition' }}
        </span>
        <q-menu v-if="!emptyCondition || !existsCondition" ref="conditionMenu">
          <q-list>
            <q-item clickable @click="addCondition('value')">
              <q-item-section>
                <q-item-label>Value condition</q-item-label>
              </q-item-section>
            </q-item>
            <q-item v-if="!emptyCondition" clickable @click="addCondition('empty')">
              <q-item-section>
                <q-item-label>Empty condition</q-item-label>
              </q-item-section>
            </q-item>
            <q-item v-if="!existsCondition" clickable @click="addCondition('exists')">
              <q-item-section>
                <q-item-label>Exists condition</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
      <div class="row q-gap-8 justify-end q-my-sm">
        <km-btn label="Cancel" flat @click="discardChanges" />
        <km-btn :label="saveButtonLabel" @click="saveChanges" />
      </div>
    </div>
  </q-popup-edit>
</template>

<script setup lang="ts">
import _ from 'lodash'
import type { QMenu, QPopupEdit } from 'quasar'
import { useTemplateRef, computed, ref } from 'vue'
import type { Condition, Filter } from '@shared/types'

// Models & Props
defineProps<{
  title: string
  saveButtonLabel: string
}>()

const filterPopup = useTemplateRef<QPopupEdit>('filterPopup')
const conditionMenu = useTemplateRef<QMenu>('conditionMenu')

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'save', pendingChanges: Filter, currentFilter: Filter): void
}>()

const currentFilter = ref<Filter | null>(null)
const pendingChanges = ref<Filter | null>(null)
const emptyCondition = computed(() => pendingChanges.value?.conditions.find((c) => c.type === 'empty'))
const existsCondition = computed(() => pendingChanges.value?.conditions.find((c) => c.type === 'exists'))

defineExpose({
  show: (filter: Filter) => {
    currentFilter.value = filter
    pendingChanges.value = _.cloneDeep(filter)
    filterPopup.value.show()
  },
  hide: () => {
    filterPopup.value.hide()
  },
})

const discardChanges = () => {
  filterPopup.value.hide()
}

const saveChanges = () => {
  emit('save', pendingChanges.value, currentFilter.value)
  filterPopup.value.hide()
}

const addCondition = (type?: string) => {
  if (!type) {
    if (emptyCondition.value && existsCondition.value) {
      type = 'value'
    } else {
      return
    }
  }
  pendingChanges.value.conditions.push({ type, operator: 'equal' })
  conditionMenu.value?.hide()

  // Focus on the new input field after adding a new value condition
  if (type === 'value') {
    setTimeout(() => {
      const inputs = document.querySelectorAll('.condition-input input')
      if (inputs.length) {
        ;(inputs[inputs.length - 1] as HTMLInputElement).focus()
      }
    }, 0)
  }
}

const removeCondition = (condition: Condition) => {
  pendingChanges.value.conditions = pendingChanges.value.conditions.filter((c) => c !== condition)
}
</script>

<style lang="stylus">
.condition-input input
  padding-left: 30px !important
</style>

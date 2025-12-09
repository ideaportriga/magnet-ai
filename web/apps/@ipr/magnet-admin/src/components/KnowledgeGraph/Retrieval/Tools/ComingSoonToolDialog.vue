<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="q-px-md q-py-sm" style="width: 600px; max-width: 95vw">
      <q-card-section>
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">{{ tool?.label || 'Tool Coming Soon' }}</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="$emit('update:modelValue', false)" />
          </div>
        </div>
      </q-card-section>

      <q-card-section>
        <div class="column items-center justify-center q-py-md text-center">
          <q-icon name="warning" color="orange-8" size="56px" class="q-mb-md" />
          <div class="km-heading-6 text-bold text-orange-9 q-mb-xs">Coming Soon</div>
          <div class="km-description text-secondary-text q-mt-xs" style="font-size: 17px">
            <div>This tool is part of the future retrieval toolkit.</div>
            <div class="text-weight-medium">It will not execute until support for this tool is implemented.</div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right" class="q-py-lg q-pr-lg">
        <km-btn label="Close" @click="$emit('update:modelValue', false)" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean
  tool: any
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>

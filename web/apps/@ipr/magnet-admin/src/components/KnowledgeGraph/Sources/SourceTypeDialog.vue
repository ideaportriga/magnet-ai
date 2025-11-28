<template>
  <q-dialog v-model="dialogOpen" transition-show="scale" transition-hide="scale">
    <q-card>
      <q-card-section class="q-pa-lg">
        <div class="row items-center">
          <div class="col">
            <div class="km-heading-7">Add New Source</div>
            <div class="dialog-subtitle">Choose a source type to get started</div>
          </div>
          <div class="col-auto">
            <q-btn icon="close" flat dense @click="onCancel" />
          </div>
        </div>
      </q-card-section>

      <q-separator />

      <q-card-section class="q-py-lg q-px-xl">
        <div class="row q-gutter-md justify-center items-start">
          <source-type-avatar
            name="File Upload"
            icon="fas fa-upload"
            icon-color="black"
            background-color="grey-3"
            @select="selectSourceType('upload')"
          />
          <source-type-avatar
            name="SharePoint"
            image="images/brands/sharepoint.svg"
            background-color="blue-1"
            @select="selectSourceType('sharepoint')"
          />
          <source-type-avatar
            name="Fluid Topics"
            image="images/brands/fluid-topics.png"
            background-color="red-1"
            @select="selectSourceType('fluid_topics')"
          />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import SourceTypeAvatar from './SourceTypeAvatar.vue';

const props = defineProps<{
  showDialog: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'select', sourceType: 'upload' | 'sharepoint' | 'fluid_topics'): void
  (e: 'cancel'): void
}>()

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (value) => emit('update:showDialog', value),
})

const selectSourceType = (sourceType: 'upload' | 'sharepoint' | 'fluid_topics') => {
  emit('select', sourceType)
  dialogOpen.value = false
}

const onCancel = () => {
  emit('cancel')
  dialogOpen.value = false
}
</script>

<style scoped>
.dialog-subtitle {
  font-size: 14px;
  color: #6b6b6b;
  font-weight: 400;
  line-height: 1.4;
}
</style>

<template>
  <q-dialog v-model="dialogOpen">
    <q-card style="min-width: 300px; max-width: unset">
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

      <!-- <q-separator /> -->

      <q-card-section class="q-pb-xl q-px-xl">
        <div class="source-grid">
          <source-type-avatar
            name="File Upload"
            icon="fas fa-upload"
            icon-color="black"
            background-color="grey-3"
            @select="selectSourceType('upload')"
          />
          <source-type-avatar name="SharePoint" :image="sharepointImage" background-color="blue-1" @select="selectSourceType('sharepoint')" />
          <source-type-avatar name="Fluid Topics" :image="fluidTopicsImage" background-color="red-1" @select="selectSourceType('fluid_topics')" />
          <source-type-avatar name="Confluence" :image="confluenceImage" background-color="blue-1" disabled coming-soon />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'
import { computed } from 'vue'
import SourceTypeAvatar from './SourceTypeAvatar.vue'

const props = defineProps<{
  showDialog: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'select', sourceType: 'upload' | 'sharepoint' | 'fluid_topics' | 'confluence'): void
  (e: 'cancel'): void
}>()

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (value) => emit('update:showDialog', value),
})

const selectSourceType = (sourceType: 'upload' | 'sharepoint' | 'fluid_topics' | 'confluence') => {
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

.source-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  justify-items: center;
}
</style>

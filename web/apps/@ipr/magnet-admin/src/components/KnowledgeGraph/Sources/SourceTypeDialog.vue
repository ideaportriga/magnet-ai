<template>
  <km-dialog v-model="dialogOpen">
    <km-card style="min-inline-size: 300px; max-inline-size: unset">
      <div class="km-card-section p-lg">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-heading-7">{{ m.knowledgeGraph_addNewSource() }}</div>
            <div class="dialog-subtitle">{{ m.knowledgeGraph_chooseSourceType() }}</div>
          </div>
          <div class="flex-none">
            <km-btn icon="close" flat dense @click="onCancel" />
          </div>
        </div>
      </div>

      <!-- <km-separator /> -->

      <div class="km-card-section pb-xl px-xl">
        <div class="source-grid">
          <source-type-avatar
            :name="m.knowledgeGraph_fileUpload()"
            icon="upload"
            avatar-tone="neutral"
            @select="selectSourceType('upload')"
          />
          <source-type-avatar name="SharePoint" :image="sharepointImage" avatar-tone="brand-soft" @select="selectSourceType('sharepoint')" />
          <source-type-avatar name="Fluid Topics" :image="fluidTopicsImage" avatar-tone="danger-soft" @select="selectSourceType('fluid_topics')" />
          <source-type-avatar name="Salesforce" :image="salesforceImage" avatar-tone="brand-soft" @select="selectSourceType('salesforce')" />
          <source-type-avatar name="Confluence" :image="confluenceImage" avatar-tone="brand-soft" @select="selectSourceType('confluence')" />
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import { m } from '@/paraglide/messages'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import salesforceImage from '@/assets/brands/salesforce.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'
import { computed } from 'vue'
import SourceTypeAvatar from './SourceTypeAvatar.vue'


const props = defineProps<{
  showDialog: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'select', sourceType: 'upload' | 'sharepoint' | 'fluid_topics' | 'salesforce' | 'confluence'): void
  (e: 'cancel'): void
}>()

const dialogOpen = computed({
  get: () => props.showDialog,
  set: (value) => emit('update:showDialog', value),
})

const selectSourceType = (sourceType: 'upload' | 'sharepoint' | 'fluid_topics' | 'salesforce' | 'confluence') => {
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
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-secondary-text);
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

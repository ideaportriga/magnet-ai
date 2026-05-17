<template>
  <div class="row no-wrap q-gutter-x-xs">
    <template v-for="type in row.source_types" :key="type">
      <q-avatar :color="iconConfig(type).bgColor" square size="24px" class="source-type-icon">
        <q-img v-if="iconConfig(type).image" :src="iconConfig(type).image" width="16px" height="16px" no-spinner no-transition />
        <q-icon v-else :name="iconConfig(type).icon" color="grey-8" size="14px" />
        <q-tooltip anchor="top middle" self="bottom middle">{{ iconConfig(type).label }}</q-tooltip>
      </q-avatar>
    </template>
  </div>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import salesforceImage from '@/assets/brands/salesforce.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'

defineProps<{
  row: Record<string, any>
  name: string
}>()

interface IconConfig {
  label: string
  bgColor: string
  icon?: string
  image?: string
}

const TYPE_CONFIGS: Record<string, IconConfig> = {
  upload: { label: 'Manual Upload', bgColor: 'grey-3', icon: 'fas fa-upload' },
  web: { label: 'Web', bgColor: 'grey-3', icon: 'fas fa-globe' },
  sharepoint: { label: 'SharePoint', bgColor: 'teal-1', image: sharepointImage },
  sharepoint_pages: { label: 'SharePoint Pages', bgColor: 'teal-1', image: sharepointImage },
  fluid_topics: { label: 'Fluid Topics', bgColor: 'red-1', image: fluidTopicsImage },
  salesforce: { label: 'Salesforce', bgColor: 'blue-1', image: salesforceImage },
  confluence: { label: 'Confluence', bgColor: 'blue-1', image: confluenceImage },
  api_ingest: { label: 'API Ingest', bgColor: 'grey-3', icon: 'fas fa-code' },
  api_fetch: { label: 'API Fetch', bgColor: 'grey-3', icon: 'fas fa-code' },
  file: { label: 'File', bgColor: 'grey-3', icon: 'fas fa-file' },
}

const FALLBACK: IconConfig = { label: 'Unknown', bgColor: 'grey-3', icon: 'fas fa-database' }

function iconConfig(type: string): IconConfig {
  return TYPE_CONFIGS[type] ?? FALLBACK
}
</script>

<style scoped>
.source-type-icon {
  border-radius: 4px;
  flex-shrink: 0;
}
</style>

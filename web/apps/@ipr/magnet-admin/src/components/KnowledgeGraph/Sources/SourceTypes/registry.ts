import type { Component } from 'vue'
import FluidTopicsDialog from './FluidTopicsDialog.vue'
import SharePointDialog from './SharePointDialog.vue'
import UploadDialog from './UploadDialog.vue'

export type SourceTypeKey = 'upload' | 'sharepoint' | 'fluid_topics'

export interface SourceTypeConfig {
  key: SourceTypeKey
  label: string
  syncable: boolean
  dialogComponent: Component
}

export const sourceRegistry: Record<SourceTypeKey, SourceTypeConfig> = {
  upload: {
    key: 'upload',
    label: 'Manual Upload',
    syncable: false,
    dialogComponent: UploadDialog,
  },
  sharepoint: {
    key: 'sharepoint',
    label: 'SharePoint',
    syncable: true,
    dialogComponent: SharePointDialog,
  },
  fluid_topics: {
    key: 'fluid_topics',
    label: 'Fluid Topics',
    syncable: false,
    dialogComponent: FluidTopicsDialog,
  },
}

export function getDialogComponentFor(type: SourceTypeKey): Component {
  return sourceRegistry[type].dialogComponent
}

export function isSyncable(type: string | undefined | null): boolean {
  if (!type) return false
  return sourceRegistry[type]?.syncable === true
}

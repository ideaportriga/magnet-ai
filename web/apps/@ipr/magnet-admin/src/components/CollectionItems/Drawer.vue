<template>
  <km-drawer-layout v-if="!!selectedRow" storage-key="drawer-collection-items">
    <template #header>
      <div class="cluster">
        <km-btn flat simple :label="`Back to Preview`" icon-size="16px" icon="arrow-left" tone="subtle" @click="closeDrawer" />
      </div>
      <div class="km-heading-4">{{ m.collectionItems_chunkDetails() }}</div>
    </template>
    <div v-if="selectedRow?.source" class="flex-none">
      <div class="flex-1 center-flex-y">
        <div class="km-heading-4" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn icon="external-link" :label="m.collectionItems_viewDocument()" icon-size="16px" flat @click="openDocument" />
      </div>
    </div>
    <div class="stack pt-sm pl-sm pr-2xl">
      <div class="basis-12 py-sm">
        <div class="km-field text-secondary-text pb-xs pl-sm">Title</div>
        <km-input :model-value="selectedRow?.metadata.title ?? &quot;-&quot;" :readonly="true" autogrow />
      </div>
      <div class="basis-12 py-sm">
        <div class="km-field text-secondary-text pb-xs pl-sm">Type</div>
        <km-input :model-value="selectedRow?.metadata.type ?? &quot;-&quot;" :readonly="true" />
      </div>
      <div class="basis-12 py-sm">
        <div class="cluster">
          <div class="km-field text-secondary-text pb-xs pl-sm flex-1"><span v-if="(selectedRow?.content == selectedRow?.metadata?.content_override || !selectedRow?.metadata?.content_override) &amp;&amp; (selectedRow?.content == selectedRow?.metadata?.content?.retrieval || !selectedRow?.metadata?.content?.retrieval)">Indexed & retrieval content</span><span v-else>Indexed content</span></div>
          <div class="flex-none">
            <km-btn flat :ripple="false" round tone="muted" :icon="indexedContentExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="indexedContentExpanded = !indexedContentExpanded" />
          </div>
        </div>
        <km-input :model-value="indexedContent" :readonly="true" autogrow />
      </div>
      <div v-if="selectedRow?.metadata?.content_override &amp;&amp; selectedRow?.content != selectedRow?.metadata?.content_override" class="basis-12 py-sm">
        <div class="cluster">
          <div class="km-field text-secondary-text pb-xs pl-sm flex-1">Retrieval content</div>
          <div class="flex-none">
            <km-btn flat :ripple="false" round tone="muted" :icon="retrievalContentExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="retrievalContentExpanded = !retrievalContentExpanded" />
          </div>
        </div>
        <km-input :model-value="retrievalContent" :readonly="true" autogrow />
      </div>
      <div v-else-if="selectedRow?.metadata?.content?.retrieval &amp;&amp; selectedRow?.content != selectedRow?.metadata?.content?.retrieval" class="basis-12 py-sm">
        <div class="cluster">
          <div class="km-field text-secondary-text pb-xs pl-sm flex-1">Retrieval content</div>
          <div class="flex-none">
            <km-btn flat :ripple="false" round tone="muted" :icon="retrievalContentExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="retrievalContentExpanded = !retrievalContentExpanded" />
          </div>
        </div>
        <km-input :model-value="retrievalContent" :readonly="true" autogrow />
      </div>
      <div v-if="selectedRow?.metadata?.content?.unmodified &amp;&amp; selectedRow?.content != selectedRow?.metadata?.content?.unmodified &amp;&amp; selectedRow?.metadata?.content?.unmodified != selectedRow?.metadata?.content?.retrieval" class="basis-12 py-sm">
        <div class="cluster">
          <div class="km-field text-secondary-text pb-xs pl-sm flex-1">Original unmodified content</div>
          <div class="flex-none">
            <km-btn flat :ripple="false" round tone="muted" :icon="unmodifiedContentExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="unmodifiedContentExpanded = !unmodifiedContentExpanded" />
          </div>
        </div>
        <km-input :model-value="unmodifiedContent" :readonly="true" autogrow />
      </div>
      <div class="basis-12 py-sm">
        <div class="km-field text-secondary-text pl-sm">Metadata</div>
        <km-codemirror v-model="metadata" class="fit" :readonly="true" />
      </div>
      <div class="basis-6 py-sm">
        <div class="km-field text-secondary-text pl-sm">Created</div>
        <km-input :model-value="createdTime" :readonly="true" />
      </div>
      <div class="basis-6 py-sm pl-sm">
        <div class="km-field text-secondary-text pl-sm">Modified</div>
        <km-input :model-value="modifiedTime" :readonly="true" />
      </div>
    </div>
  </km-drawer-layout>
</template>
<script>
import { defineComponent, ref } from 'vue'
import { m } from '@/paraglide/messages'
import { formatDateTime } from '@shared'
import { useEntityConfig } from '@/composables/useEntityConfig'

export default defineComponent({
  props: ['selectedRow'],
  emits: ['close'],
  setup() {
    const { config } = useEntityConfig('documents')
    return {
      config,
      m,
      indexedContentExpanded: ref(false),
      retrievalContentExpanded: ref(false),
      unmodifiedContentExpanded: ref(false),
    }
  },
  computed: {
    indexedContent() {
      let content = this.selectedRow?.content
      if (!this.indexedContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    retrievalContent() {
      let content = this.selectedRow?.metadata?.content?.retrieval || this.selectedRow?.metadata?.content_override
      if (!this.retrievalContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    unmodifiedContent() {
      let content = this.selectedRow?.metadata?.content?.unmodified
      if (!this.unmodifiedContentExpanded) {
        content = content.substring(0, 200)
      }
      return content ?? '-'
    },
    createdTime() {
      if (this.selectedRow?.metadata?.createdTime) {
        return formatDateTime(this.selectedRow?.metadata?.createdTime)
      }
      return '-'
    },
    modifiedTime() {
      if (this.selectedRow?.metadata?.modifiedTime) {
        return formatDateTime(this.selectedRow?.metadata?.modifiedTime)
      }
      return '-'
    },
    metadata() {
      if (!this.selectedRow) return '{}'
      //return JSON.stringify(this.selectedRow?.metadata, null, 2)
      const { config } = this
      const metaKeys = Object.keys(this.selectedRow?.metadata).filter((key) => {
        const currentConfig = config[key]
        if (!currentConfig) return true
        return currentConfig.fromMetadata
      })
      const localMeta = {}
      metaKeys.forEach((key) => {
        localMeta[key] = this.selectedRow?.metadata[key]
      })
      if (!localMeta) return '{}'
      return JSON.stringify(localMeta, null, 2)
    },
  },
  methods: {
    closeDrawer() {
      this.$emit('close')
    },
    openDocument() {
      if (this.selectedRow && this.selectedRow?.source) {
        window.open(this.selectedRow?.source, '_blank')
      } else {

      }
    },
  },
})
</script>

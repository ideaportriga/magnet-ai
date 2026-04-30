<template>
  <div class="stack fit" data-gap="0">
    <div class="flex-none">
      <div class="cluster">
        <km-btn flat icon="chevron-left" icon-size="20px" tone="subtle" @click="$emit(&quot;close&quot;)" />
        <div class="km-heading-7 mb-xs ml-sm">{{ m.collectionItems_chunkDetails() }}</div>
      </div>
    </div>
    <km-separator class="mb-md" />
    <template v-if="!selectedRow?.id">
      <div class="flex flex-center full-height">
        <div class="km-description text-grey">{{ m.collectionItems_noChunkSelected() }}</div>
      </div>
    </template>
    <template v-else>
      <div v-if="selectedRow?.metadata?.source" class="flex-none">
        <div class="cluster" data-justify="end">
          <km-btn icon="external-link" :label="m.collectionItems_viewDocument()" icon-size="16px" flat @click="openDocument" />
        </div>
      </div>
      <div class="flex-1">
        <km-scroll-area class="fit">
          <div class="stack pt-sm pl-sm pr-2xl" data-gap="0">
            <div class="py-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_title() }}</div>
              <km-input :model-value="selectedRow?.metadata?.title ?? &quot;-&quot;" :readonly="true" autogrow />
            </div>
            <div class="py-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_type() }}</div>
              <km-input :model-value="selectedRow?.metadata?.type ?? &quot;-&quot;" :readonly="true" />
            </div>
            <div class="py-sm">
              <div class="cluster">
                <div class="km-field text-secondary-text pb-xs pl-sm flex-1"><span v-if="!hasAlternateContent">{{ m.collectionItems_indexedRetrievalContent() }}</span><span v-else>{{ m.collectionItems_indexedContent() }}</span></div>
                <div class="flex-none">
                  <km-btn flat round tone="muted" :icon="indexedExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="indexedExpanded = !indexedExpanded" />
                </div>
              </div>
              <km-input :model-value="indexedExpanded ? selectedRow?.content : truncate(selectedRow?.content)" :readonly="true" autogrow />
            </div>
            <div v-if="retrievalContent &amp;&amp; retrievalContent !== selectedRow?.content" class="py-sm">
              <div class="cluster">
                <div class="km-field text-secondary-text pb-xs pl-sm flex-1">{{ m.collectionItems_retrievalContent() }}</div>
                <div class="flex-none">
                  <km-btn flat round tone="muted" :icon="retrievalExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="retrievalExpanded = !retrievalExpanded" />
                </div>
              </div>
              <km-input :model-value="retrievalExpanded ? retrievalContent : truncate(retrievalContent)" :readonly="true" autogrow />
            </div>
            <div v-if="unmodifiedContent &amp;&amp; unmodifiedContent !== selectedRow?.content &amp;&amp; unmodifiedContent !== retrievalContent" class="py-sm">
              <div class="cluster">
                <div class="km-field text-secondary-text pb-xs pl-sm flex-1">{{ m.collectionItems_originalUnmodifiedContent() }}</div>
                <div class="flex-none">
                  <km-btn flat round tone="muted" :icon="unmodifiedExpanded ? &quot;collapse&quot; : &quot;expand&quot;" size="xs" @click="unmodifiedExpanded = !unmodifiedExpanded" />
                </div>
              </div>
              <km-input :model-value="unmodifiedExpanded ? unmodifiedContent : truncate(unmodifiedContent)" :readonly="true" autogrow />
            </div>
            <div class="py-sm">
              <div class="km-field text-secondary-text pl-sm">{{ m.common_metadata() }}</div>
              <km-codemirror class="fit" :model-value="metadataJson" :readonly="true" />
            </div>
            <div class="collections-drawer-chunk__meta-grid">
              <div class="py-sm">
                <div class="km-field text-secondary-text pl-sm">{{ m.common_created() }}</div>
                <km-input :model-value="selectedRow?.metadata?.createdTime ?? &quot;-&quot;" :readonly="true" />
              </div>
              <div class="py-sm pl-sm">
                <div class="km-field text-secondary-text pl-sm">{{ m.common_lastModified() }}</div>
                <km-input :model-value="selectedRow?.metadata?.modifiedTime ?? &quot;-&quot;" :readonly="true" />
              </div>
            </div>
          </div>
        </km-scroll-area>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import type { Document } from '@/types'

const props = defineProps<{ selectedRow?: Document | null }>()
defineEmits<{ close: [] }>()

const indexedExpanded = ref(false)
const retrievalExpanded = ref(false)
const unmodifiedExpanded = ref(false)

const TRUNCATE_LENGTH = 200

function truncate(text?: string): string {
  if (!text) return '-'
  return text.length > TRUNCATE_LENGTH ? text.substring(0, TRUNCATE_LENGTH) + '...' : text
}

const retrievalContent = computed(() =>
  props.selectedRow?.metadata?.content?.retrieval || props.selectedRow?.metadata?.content_override || null,
)

const unmodifiedContent = computed(() =>
  props.selectedRow?.metadata?.content?.unmodified || null,
)

const hasAlternateContent = computed(() =>
  (retrievalContent.value && retrievalContent.value !== props.selectedRow?.content) ||
  (unmodifiedContent.value && unmodifiedContent.value !== props.selectedRow?.content),
)

const metadataJson = computed(() => {
  const meta = props.selectedRow?.metadata
  if (!meta) return '{}'
  // Exclude content-related fields that are shown separately
  const { content, content_override, ...rest } = meta as Record<string, unknown>
  return JSON.stringify(rest, null, 2)
})

function openDocument() {
  const source = props.selectedRow?.metadata?.source
  if (source) window.open(String(source), '_blank')
}
</script>

<style scoped>
.collections-drawer-chunk__meta-grid {
  display: grid;
  gap: var(--ds-space-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .collections-drawer-chunk__meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>

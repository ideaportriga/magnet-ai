<template lang="pug">
.column.fit
  .col-auto
    .row.items-center
      km-btn(flat, icon='fas fa-chevron-left', @click='$emit("close")', iconSize='20px', color='secondary-text')
      .km-heading-7.q-mb-xs.q-ml-sm {{ m.collectionItems_chunkDetails() }}
  q-separator.q-mb-md

  template(v-if='!selectedRow?.id')
    .flex.flex-center.full-height
      .km-description.text-grey {{ m.collectionItems_noChunkSelected() }}

  template(v-else)
    .col-auto(v-if='selectedRow?.metadata?.source')
      .row.items-center
        .col
        .col-auto
          km-btn(icon='fas fa-external-link-alt', :label='m.collectionItems_viewDocument()', iconSize='16px', flat, @click='openDocument')
    .col
      q-scroll-area.fit
          .row.justify-between.q-pt-8.q-pl-8.q-pr-24
            .col-12.q-py-8
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_title() }}
            km-input(:model-value='selectedRow?.metadata?.title ?? "-"', :readonly='true', autogrow)
          .col-12.q-py-8
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_type() }}
            km-input(:model-value='selectedRow?.metadata?.type ?? "-"', :readonly='true')

          //- Indexed content
          .col-12.q-py-8
            .row.items-center
              .km-field.text-secondary-text.q-pb-xs.q-pl-8.col
                span(v-if='!hasAlternateContent') {{ m.collectionItems_indexedRetrievalContent() }}
                span(v-else) {{ m.collectionItems_indexedContent() }}
              .col-auto
                q-btn(flat, round, color='secondary', :icon='indexedExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"', @click='indexedExpanded = !indexedExpanded', size='xs')
            km-input(:model-value='indexedExpanded ? selectedRow?.content : truncate(selectedRow?.content)', :readonly='true', autogrow)

          //- Retrieval content (if different from indexed)
          .col-12.q-py-8(v-if='retrievalContent && retrievalContent !== selectedRow?.content')
            .row.items-center
              .km-field.text-secondary-text.q-pb-xs.q-pl-8.col {{ m.collectionItems_retrievalContent() }}
              .col-auto
                q-btn(flat, round, color='secondary', :icon='retrievalExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"', @click='retrievalExpanded = !retrievalExpanded', size='xs')
            km-input(:model-value='retrievalExpanded ? retrievalContent : truncate(retrievalContent)', :readonly='true', autogrow)

          //- Original unmodified content (if different)
          .col-12.q-py-8(v-if='unmodifiedContent && unmodifiedContent !== selectedRow?.content && unmodifiedContent !== retrievalContent')
            .row.items-center
              .km-field.text-secondary-text.q-pb-xs.q-pl-8.col {{ m.collectionItems_originalUnmodifiedContent() }}
              .col-auto
                q-btn(flat, round, color='secondary', :icon='unmodifiedExpanded ? "fas fa-compress-alt" : "fas fa-expand-alt"', @click='unmodifiedExpanded = !unmodifiedExpanded', size='xs')
            km-input(:model-value='unmodifiedExpanded ? unmodifiedContent : truncate(unmodifiedContent)', :readonly='true', autogrow)

          //- Metadata JSON
          .col-12.q-py-8
            .km-field.text-secondary-text.q-pl-8 {{ m.common_metadata() }}
            km-codemirror.fit(:model-value='metadataJson', :readonly='true')

          //- Timestamps
          .col-6.q-py-8
            .km-field.text-secondary-text.q-pl-8 {{ m.common_created() }}
            km-input(:model-value='selectedRow?.metadata?.createdTime ?? "-"', :readonly='true')
          .col-6.q-py-8.q-pl-8
            .km-field.text-secondary-text.q-pl-8 {{ m.common_lastModified() }}
            km-input(:model-value='selectedRow?.metadata?.modifiedTime ?? "-"', :readonly='true')
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

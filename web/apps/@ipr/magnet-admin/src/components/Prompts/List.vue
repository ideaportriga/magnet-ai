<template>
  <div class="stack py-md pl-md pr-md full-height" data-gap="lg">
    <div class="flex-none">
      <div class="cluster">
        <div class="flex-1">
          <div class="km-heading-4">{{ m.nav_promptTemplates() }}</div>
        </div>
      </div>
    </div>
    <div class="flex-none">
      <km-input class="full-width" icon-before="search" :model-value="search" :placeholder="m.common_searchPromptTemplates()" clearable @input="search = $event" />
    </div>
    <div class="cluster pt-lg">
      <km-btn :label="m.common_newPromptTemplate()" @click="$emit(&quot;create&quot;)" />
    </div>
    <div class="flex-1 overflow-auto pr-sm">
      <template v-for="item in displayPrompts" :key="item">
        <div class="rounded-borders cursor-pointer py-sm prompt-card bb-border" :class="{ &quot;bg-table-active text-black&quot;: selected === item.id }" @click.stop="$emit(&quot;update:selected&quot;, item.id)">
          <div class="cluster px-sm" data-gap="md" data-wrap="no">
            <div class="flex-1">
              <div class="km-title ellipsis" style="text-overflow: ellipsis">{{ item.name }}</div>
              <div style="min-block-size: 22px">
                <div class="km-description ellipsis-2-lines" :class="selected === item.id ? &quot;text-grey&quot; : &quot;text-grey&quot;">{{ item.description }}</div>
              </div>
            </div>
            <div class="flex-none">
              <template v-if="item.pinned === 1">
                <km-btn class="pin-selected px-xs pt-sm" icon="pin" flat size="8px" tone="muted" @click.stop="$emit(&quot;setPin&quot;, { id: item.id, val: 0 })" />
              </template>
              <template v-else>
                <km-btn class="pin-not-selected px-xs pt-sm" icon="pin" flat size="8px" @click.stop="$emit(&quot;setPin&quot;, { id: item.id, val: 1 })" />
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
const promptSearchFields = ['name', 'description']
export default {
  props: ['selected'],
  emits: ['update:selected', 'create', 'setPin'],
  setup() {
    const queries = useEntityQueries()
    const { data: promptListData } = queries.promptTemplates.useList()
    const promptItems = computed(() => promptListData.value?.items ?? [])
    return {
      m,
      search: ref(''),
      promptItems,
    }
  },
  computed: {
    prompts() {
      return this.promptItems ?? []
    },

    displayPrompts() {
      let display = [...this.prompts].sort((a, b) => b.pinned - a.pinned || a.name?.localeCompare(b.name))

      if (this.search) {
        const constrain = this.search.toLowerCase().replace(/\s/g, '')
        display =
          display?.filter((opt) => {
            let searchString =
              Object.entries(opt)
                .filter(([key, val]) => promptSearchFields.includes(key) && val)
                .map(([, val]) => `${val}`.toLowerCase().replace(/\s/g, ''))
                .join('') ?? ''
            return searchString.includes(constrain)
          }) ?? []
      }
      return display
    },
  },
  watch: {},
  created() {},
  methods: {
    setProp() {},
  },
}
</script>

<style scoped>
.prompt-card:hover {
  background: var(--ds-color-table-active);
}
.pin-not-selected {
  color: transparent !important;
}
.prompt-card:hover .pin-not-selected {
  color: var(--ds-color-gray-500) !important;
}
.prompt-card:hover .pin-not-selected:hover {
  color: var(--ds-color-primary) !important;
}
.prompt-card:hover .pin-selected:hover {
  color: var(--ds-color-gray-200) !important;
}
</style>

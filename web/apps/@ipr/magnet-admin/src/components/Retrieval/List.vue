<template lang="pug">
.column.q-py-md.q-pl-md.q-pr-md.q-gap-16.no-wrap.full-height
  //- HEADER
  .col-auto
    .row.items-center
      .col
        .km-heading-4 {{ m.nav_promptTemplates() }}

  //- SEARCH
  .col-auto
    km-input.full-width(icon-before='search', @input='search = $event', :model-value='search', :placeholder='m.common_searchPromptTemplates()', clearable)
  .row.q-pt-16
    km-btn(:label='m.common_newPromptTemplate()', @click='$emit("create")')

  //- LIST
  .col.overflow-auto.q-pr-sm
    template(v-for='item in displayPrompts')
      .rounded-borders.cursor-pointer.q-py-sm.prompt-card.bb-border(
        @click.stop='$emit("update:selected", item.id)',
        :class='{ "bg-table-active text-black": selected === item.id }'
      )
        .row.items-center.q-gap-12.q-px-sm.no-wrap
          .col
            .km-title.ellipsis(style='text-overflow: hidden') {{ item.name }}
            div(style='min-height: 22px')
              .km-description.ellipsis-2-lines(:class='selected === item.id ? "text-grey" : "text-grey"') {{ item.description }}
          .col-auto
            template(v-if='item.pinned === 1')
              q-btn.pin-selected.q-px-xs.q-pt-sm(
                icon='fas fa-thumbtack',
                flat,
                size='8px',
                color='secondary',
                @click.stop='$emit("setPin", { id: item.id, val: 0 })'
              )
            template(v-else)
              q-btn.pin-not-selected.q-px-xs.q-pt-sm(
                icon='fas fa-thumbtack',
                flat,
                size='8px',
                color='transparent',
                @click.stop='$emit("setPin", { id: item.id, val: 1 })'
              )
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
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

<style lang="stylus" scoped>
.prompt-card:hover
  background: var(--q-table-active)
  .pin-not-selected
    color: grey !important
  .pin-not-selected:hover
    color: var(--q-primary) !important
  .pin-selected:hover
    color: lightgrey !important
</style>

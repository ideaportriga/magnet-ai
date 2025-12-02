<template lang="pug">
q-dialog(:model-value='modal', @hide='$emit("update:modal", false)')
  .column.q-pa-md.bg-background(style='width: 692px; max-width: 800px; border-radius: 8px; min-height: 668px')
    .col-auto
      //- Search
      //- icon-before="search"
      km-input.full-width(
        icon-before='search',
        @input='page = 1; search = $event',
        :model-value='search',
        autofocus,
        placeholder='search icons',
        clearable
      )

    //- Body

    .col.q-mt-md
      .row.q-gap-12
        template(v-for='icon in pageIcons')
          .col-auto.bg-white.rounded-borders(@click='setIcon(icon)')
            .icon-card.q-pa-md
              div
                .center-flex-x
                  q-icon.icon-display(:name='`${icon.name}`', size='26px', color='text-grey')

                .q-mt-xs
                .km-tiny.text-grey-6.ellipsis-2-lines.icon-text {{ icon.title }}

    .q-mt-sm.row.items-center
      .col
        //- div {{pagination}}
      .col-auto
        q-btn.q-px-sm(icon='fas fa-angle-left', flat, color='grey-7', size='md', @click='page -= 1', :disable='page <= 1')
      .col-auto.q-px-sm
        .km-description {{ `${page} of ${pagination.maxPages}` }}
      .col-auto
        q-btn.q-px-sm(icon='fas fa-angle-right', flat, color='grey-7', size='md', @click='page += 1', :disable='page >= pagination.maxPages')
</template>

<script>
import { ref } from 'vue'
import iconList from '@quasar/extras/fontawesome-v5/icons.json'
import kebabCase from 'lodash/kebabCase'

export default {
  props: {
    modelValue: String,
    modal: Boolean,
  },
  emits: ['update:modelValue', 'update:modal'],
  setup() {
    return {
      pageSize: 36,
      search: ref(),
      page: ref(1),
    }
  },
  computed: {
    icons() {
      return (iconList ?? []).map((icon) => {
        const kebab = kebabCase(icon)
        const arr = kebab.split('-')

        return {
          name: `${arr[0]} fa-${arr.slice(1).join('-')}`,
          title: arr.slice(1).join(' '),
        }
      })
    },
    displayIcons() {
      let display = this.icons

      // search
      if (this.search) {
        display =
          display?.filter((opt) => {
            let searchString =
              Object.entries(opt)
                .filter(([key, val]) => ['name'].includes(key) && val)
                .map(([, val]) => `${val}`.toLowerCase().replace(/\s/g, ''))
                .join('') ?? ''
            // console.log('picker - searchString: ',searchString )
            return searchString.includes(this.search.toLowerCase().replace(/\s/g, ''))
          }) ?? []
      }
      //         max: Math.ceil(this.displayIcons?.length / this.pageSize),
      // count: this.displayIcons.length,
      // page
      return display
    },

    pageIcons() {
      return (this.displayIcons ?? [])?.slice(this.pagination.start, this.pagination.end)
    },

    pagination() {
      return {
        start: this.pageSize * (this.page - 1),
        end: this.pageSize * this.page,
        maxPages: Math.ceil(this.displayIcons?.length / this.pageSize),
        count: this.displayIcons?.length,
      }
    },
  },
  methods: {
    setIcon(icon) {
      this.$emit('update:modelValue', icon.name)
      this.$emit('update:modal', false)
    },
  },
}
</script>

<style lang="stylus" scoped>
.icon-card
  width 100px
  height 80px
  cursor pointer
  border-radius 4px
  &:hover
    background var(--q-table-hover)
    .icon-text
      color: var(--q-primary) !important
    .icon-display
      color: var(--q-primary) !important


.icon-text
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-align: center;
</style>

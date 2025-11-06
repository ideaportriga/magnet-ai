<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  q-scroll-area.fit
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md
          .border.border-radius-12.bg-white.ba-border.q-my-16.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y
                .km-heading-2 Dashboard
            .row.q-gap-16.items-center.q-pb-16
              template(v-for='filter in filter')
                .row.items-center.q-gap-4(v-if='!filter.hide')
                  km-select(
                    v-model='activeFilters[filter.label]',
                    :hasDropdownSearch='filter.search',
                    :options='filter.options',
                    useChips,
                    mapOption,
                    optionLabel='label',
                    optionValue='value',
                    :permanentPlaceholder='filter.label',
                    :multiple='filter.multiple',
                    placeholder='All'
                  )
                  q-icon.q-my-auto.cursor-pointer(
                    v-if='filter.hidden',
                    color='secondary',
                    name='fa fa-times',
                    @click.stop.prevent='hideFilter(filter.key)'
                  )

              km-select-flat(
                v-if='hiddenFilters.length',
                placeholder='Add Filter',
                @update:modelValue='updateVisibleFilters',
                :options='hiddenFilters',
                modelValue=''
              )

            .dashboard-grid
              dashboard-board-card
                template(v-slot:body)
                  dashboard-board-bars(:data='data')
              dashboard-board-card
                template(v-slot:body)
                  template(v-for='i in 5')
                    .row.items-center.justify-between
                      .col-auto
                        .km-paragraph Lorem ipsum dolor
                      .col-auto
                        .km-chart-value(style='width: 30px') 22
              dashboard-board-card(bg='border')
              dashboard-board-card
            .dashboard-grid-3.q-pt-16
              dashboard-board-card
                template(v-slot:body)
                  .row.items-center.justify-between
                    .km-chart-value 54.06%
              dashboard-board-card
                template(v-slot:body)
                  .row.items-center.justify-between
                    .km-chart-value 54.06%
              dashboard-board-card
                template(v-slot:body)
                  .row.items-center.justify-between
                    .km-chart-value 54.06%
            dashboard-board-card.q-mt-16
              template(v-slot:body)
                .row.items-center.justify-between
                  .km-paragraph Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

//-
</template>
<script>
import { ref } from 'vue'

const filter = {
  channel: {
    label: 'Channel',
    key: 'channel',
    options: [
      { label: 'Production', value: 'production' },
      { label: 'Development', value: 'development' },
    ],
    multiple: true,
  },
  tool: {
    label: 'Tool',
    key: 'tool',
    options: [
      { label: 'Tool 1', value: 'tool1' },
      { label: 'Tool 2', value: 'tool2' },
      { label: 'Tool 3', value: 'tool3' },
    ],
    search: true,
  },
  timePeriod: {
    label: 'Time Period',
    key: 'timePeriod',
    options: [
      { label: 'Last 24 hours', value: 'last24hours' },
      { label: 'Last 7 days', value: 'last7days' },
    ],
    hide: true,
    hidden: true,
  },
}

export default {
  setup() {
    return {
      activeFilters: ref({}),
      selected: ref(null),
      options: ref([
        { label: 'Production', value: 'production' },
        { label: 'Development', value: 'development' },
      ]),
      data: ref([
        { title: 'Liked', value: 12222, action: () => console.log('liked') },
        { title: 'Disliked', value: 1121, action: () => console.log('disliked') },
      ]),
      filter: ref(filter),
    }
  },
  computed: {
    hiddenFilters() {
      return Object.values(this.filter)
        .filter((f) => f.hide)
        .map((f) => {
          return {
            label: f.label,
            value: f.key,
          }
        })
    },
  },
  methods: {
    updateVisibleFilters({ value }) {
      this.filter[value].hide = false
    },
    hideFilter(key) {
      this.filter[key].hide = true
    },
  },
}
</script>

<style lang="stylus" scoped>
.dashboard
    &-grid
      display: grid
      grid-template-columns: repeat(4, 1fr)
      gap: 16px
      justify-items: center
      align-items: baseline
      white-space: nowrap
      &-3
        @extend .dashboard-grid
        grid-template-columns: repeat(3, 1fr)
</style>

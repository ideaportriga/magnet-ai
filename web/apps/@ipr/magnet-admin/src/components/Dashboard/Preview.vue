<template>
  <div class="cluster overflow-hidden full-height" data-wrap="no">
    <km-scroll-area class="fit">
      <div class="flex full-height fit" style="justify-content: center; flex-wrap: nowrap">
        <div class="flex-none collection-container full-width">
          <div class="full-height pb-md relative-position px-md">
            <div class="border border-radius-12 bg-white ba-border my-lg p-lg gap-lg full-width">
              <div class="cluster mb-md" data-justify="between">
                <div class="flex-none center-flex-y">
                  <div class="km-heading-2">Dashboard</div>
                </div>
              </div>
              <div class="cluster pb-lg" data-gap="lg">
                <template v-for="filter in filter" :key="filter">
                  <div v-if="!filter.hide" class="cluster" data-gap="xs">
                    <km-select v-model="activeFilters[filter.label]" :has-dropdown-search="filter.search" :options="filter.options" use-chips map-option option-label="label" option-value="value" :permanent-placeholder="filter.label" :multiple="filter.multiple" :placeholder="m.common_all()" />
                    <km-glyph v-if="filter.hidden" class="my-auto cursor-pointer" name="close" @click.stop.prevent="hideFilter(filter.key)" />
                  </div>
                </template>
                <km-select-flat v-if="hiddenFilters.length" :placeholder="m.common_addFilter()" :options="hiddenFilters" model-value="" @update:model-value="updateVisibleFilters" />
              </div>
              <div class="dashboard-grid">
                <dashboard-board-card>
                  <template #body>
                    <dashboard-board-bars :data="data" />
                  </template>
                </dashboard-board-card>
                <dashboard-board-card>
                  <template #body>
                    <template v-for="i in 5" :key="i">
                      <div class="cluster" data-justify="between">
                        <div class="flex-none">
                          <div class="km-paragraph">Lorem ipsum dolor</div>
                        </div>
                        <div class="flex-none">
                          <div class="km-chart-value" style="inline-size: 30px">22</div>
                        </div>
                      </div>
                    </template>
                  </template>
                </dashboard-board-card>
                <dashboard-board-card theme="muted" />
                <dashboard-board-card />
              </div>
              <div class="dashboard-grid-3 pt-lg">
                <dashboard-board-card>
                  <template #body>
                    <div class="cluster" data-justify="between">
                      <div class="km-chart-value">54.06%</div>
                    </div>
                  </template>
                </dashboard-board-card>
                <dashboard-board-card>
                  <template #body>
                    <div class="cluster" data-justify="between">
                      <div class="km-chart-value">54.06%</div>
                    </div>
                  </template>
                </dashboard-board-card>
                <dashboard-board-card>
                  <template #body>
                    <div class="cluster" data-justify="between">
                      <div class="km-chart-value">54.06%</div>
                    </div>
                  </template>
                </dashboard-board-card>
              </div>
              <dashboard-board-card class="mt-lg">
                <template #body>
                  <div class="cluster" data-justify="between">
                    <div class="km-paragraph">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</div>
                  </div>
                </template>
              </dashboard-board-card>
            </div>
          </div>
        </div>
      </div>
    </km-scroll-area>
  </div>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'

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
      m,
      activeFilters: ref({}),
      selected: ref(null),
      options: ref([
        { label: 'Production', value: 'production' },
        { label: 'Development', value: 'development' },
      ]),
      data: ref([
        { title: 'Liked', value: 12222, action: () => {} },
        { title: 'Disliked', value: 1121, action: () => {} },
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

<style scoped>
.dashboard-grid,
.dashboard-grid-3 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  place-items: baseline center;
  white-space: nowrap;
}
.dashboard-grid-3,
.dashboard-grid-3-3 {
  grid-template-columns: repeat(3, 1fr);
}
</style>

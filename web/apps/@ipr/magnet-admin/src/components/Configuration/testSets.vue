<template lang="pug">
.full-width.q-mb-sm
  km-select(
    height='auto',
    minHeight='36px',
    placeholder='Test Set',
    :options='setItems',
    v-model='sampleTestSet',
    option-value='system_name',
    option-label='name',
    emit-value,
    map-options,
    hasDropdownSearch
  )
.row.q-mb-sm(v-if='sampleTestSet')
  km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='searchString = $event', clearable) 
.full-width(v-if='sampleTestSet')
  km-table(
    @selectRow='selectRecord',
    :selected='ragTestSetItem ? [ragTestSetItem] : []',
    row-key='user_input',
    :rows-per-page-options='[10]',
    v-model:selected='selected',
    :columns='columns',
    :rows='filteredTestSetItems ?? []',
    :pagination='pagination',
    binary-state-sort
  )
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { columnsSettings } from '@/config/evaluation_sets/evaluation_set_records'

export default {
  setup() {
    const { items: setItems } = useChroma('evaluation_sets')

    return {
      setItems,
      columns: Object.values(columnsSettings).sort((a, b) => a.columnNumber - b.columnNumber),
      createNew: ref(false),
      loading: ref(false),
      selectedRow: ref(null),
      searchString: ref(''),
      pagination: ref({
        rowsPerPage: 10,
        // sortBy: 'last_updated',
        // descending: true,
      }),
    }
  },
  computed: {
    ragTestSetItem() {
      return this.$store.getters.ragTestSetItem
    },
    refs() {
      return this.$refs
    },
    testSetItems() {
      return this.testSetObject?.items || []
    },
    testSetObject() {
      return this.setItems.find(({ system_name }) => system_name === this.sampleTestSet)
    },
    sampleTestSet: {
      get() {
        return this.$store.getters.ragVariant?.sample_test_set || ''
      },
      set(value) {
        this.$store.commit('updateNestedRagProperty', { path: 'sample_test_set', value })
      },
    },
    filteredTestSetItems() {
      if (!this.searchString) return this.testSetItems
      const fields = ['user_input', 'expected_result']
      return this.testSetItems.filter((item) => fields.some((field) => item[field].toLowerCase().includes(this.searchString.toLowerCase())))
    },
  },
  methods: {
    selectRecord(row) {
      this.$store.commit('setRagTestSetItem', row)
    },
  },
}
</script>

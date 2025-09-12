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
.full-width
  km-table.sticky-virtscroll-table(
    style='height: calc(100vh - 460px) !important',
    @selectRow='selectRecord',
    :selected='promptTemplateTestSetItem ? [promptTemplateTestSetItem] : []',
    row-key='user_input',
    :rows-per-page-options='[0]',
    v-model:selected='selected',
    :columns='columns',
    :rows='testSetItems ?? []',
    :pagination='agentPagination',
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
    }
  },
  computed: {
    promptTemplateTestSetItem() {
      return this.$store.getters.promptTemplateTestSetItem
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
        return this.$store.getters.retrievalVariant?.sample_test_set || ''
      },
      set(value) {
        this.$store.commit('updateNestedRetrievalProperty', { path: 'sample_test_set', value })
      },
    },
  },
  methods: {
    selectRecord(row) {
      this.$store.commit('setRetrievalTestSetItem', row)
    },
  },
}
</script>

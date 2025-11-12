<template lang="pug">
.row.q-gap-16.items-center
  q-icon(name='filter_list', size='24px', color='secondary')
  template(v-for='conf in processedConfigs', :key='conf.key')
    .row.items-center.q-gap-4(v-if='!conf.is_hidden')
      km-select(
        :modelValue='filterModel[conf.key]',
        @update:modelValue='setFilter(conf.key, $event)',
        :hasDropdownSearch='conf.search',
        :options='typeof conf.options === "function" ? conf.options() : conf.options',
        useChips,
        mapOption,
        optionLabel='label',
        optionValue='value',
        :permanentPlaceholder='conf.label',
        :multiple='conf.multiple'
      )

      q-icon.q-my-auto.cursor-pointer(v-if='conf?.is_hideable', color='secondary', name='fa fa-times', @click.stop.prevent='hideFilter(conf.key)')

  km-select-flat(
    v-if='hiddenFilters.length',
    placeholder='Add Filter',
    @update:modelValue='updateVisibleFilters',
    :options='hiddenFilters',
    modelValue=''
  )

  km-btn(label='Clear all filters', @click='clearAll', flat, v-if='showClearAll')
</template>

<script>
import { ref } from 'vue'
import { DateTime, Duration } from 'luxon'

const PRESET_FILTERS = {
  timePeriod: [
    { label: 'Last 15 minutes', value: 'PT15M' },
    { label: 'Last 30 minutes', value: 'PT30M' },
    { label: 'Last 1 hour', value: 'PT1H' },
    { label: 'Last 6 hours', value: 'PT6H' },
    { label: 'Last 12 hours', value: 'PT12H' },
    { label: 'Last 24 hours', value: 'P1D' },
    { label: 'Last 3 days', value: 'P3D' },
    { label: 'Last 5 days', value: 'P5D' },
    { label: 'Last 7 days', value: 'P7D' },
  ],
}

export default {
  props: {
    config: {
      type: Object,
      required: true,
    },
    filterObject: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    persistent: {
      type: Boolean,
      default: false,
    },
    persistentKey: {
      type: String,
      default: '',
    },
    outputFormat: {
      type: String,
      default: 'mongodb',
      validator: (value) => ['mongodb', 'sql'].includes(value),
    },
  },
  emits: ['update:config', 'update:filter', 'update:filterObject'],
  data() {
    return {
      filter: ref({}),
    }
  },
  computed: {
    transformToMongoFilter() {
      if (this.outputFormat === 'sql') {
        return this.transformFiltersToSqlQuery(this.filter, this.config)
      } else {
        return this.transformFiltersToMongoQuery(this.filter, this.config)
      }
    },

    showClearAll() {
      return !Object.values(this.filter).every(
        (value) =>
          value === null ||
          (Array.isArray(value) && value.length === 0) ||
          (typeof value === 'object' && value !== null && Object.keys(value).length === 0)
      )
    },
    hiddenFilters() {
      return Object.values(this.config)
        .filter((f) => f.is_hidden)
        .map((f) => ({
          label: f.label,
          value: f.key,
        }))
    },
    processedConfigs() {
      return Object.values(this.config).map((filter) => {
        if (filter.type === 'timePeriod' && !filter.options) {
          return {
            ...filter,
            options: PRESET_FILTERS?.timePeriod,
          }
        }
        return filter
      })
    },
    filterModel() {
      return this.filter
    },
  },
  watch: {
    transformToMongoFilter: {
      deep: true,
      handler(newVal) {
        this.$emit('update:filterObject', newVal)
      },
    },
    filter: {
      deep: true,
      handler(newVal) {
        if (this.persistent) {
          sessionStorage.setItem(this.persistentKey, JSON.stringify(newVal))
        }
      },
    },
  },
  mounted() {
    if (this.persistent) {
      const storedFilter = sessionStorage.getItem(this.persistentKey)
      if (storedFilter) {
        this.filter = JSON.parse(storedFilter)
        return
      }
    }
    if (!this.filterObject || Object.keys(this.filterObject).length === 0) {
      this.setDefault()
    }
  },
  methods: {
    transformFiltersToMongoQuery(activeFilters, filterConfig) {
      const conditions = []
      let searchString = null

      for (const key in filterConfig) {
        const config = filterConfig[key]
        const activeFilter = activeFilters[key]

        if (!activeFilter) continue
        if (Array.isArray(activeFilter) && activeFilter.length === 0) continue

        if (config.customLogic) {
          const res = config.customLogic(activeFilter)
          if (Array.isArray(res)) {
            res.forEach((condition) => {
              conditions.push(condition)
            })
          } else {
            conditions.push(res)
          }
        } else if (config.type === 'timePeriod') {
          const duration = Duration.fromISO(activeFilter.value)
          const dateThreshold = DateTime.now().minus(duration).toISO()

          const fieldName = config.field || key
          conditions.push({ [fieldName]: { $gte: dateThreshold } })
        } else if (config.type === 'search') {
          const searchValue = activeFilter.value !== undefined ? activeFilter.value : activeFilter
          searchString = searchValue
        } else {
          if (config.multiple) {
            const values = Array.isArray(activeFilter)
              ? activeFilter.map((item) => (item.value !== undefined ? item.value : item))
              : [activeFilter.value !== undefined ? activeFilter.value : activeFilter]
            conditions.push({ [config.key]: { $in: values } })
          } else {
            const value = activeFilter.value !== undefined ? activeFilter.value : activeFilter
            if (Array.isArray(value)) {
              conditions.push({ [config.key]: { $in: value } })
            } else {
              conditions.push({ [config.key]: { $eq: value } })
            }
          }
        }
      }

      const result = {}
      
      if (conditions.length === 1) {
        Object.assign(result, conditions[0])
      } else if (conditions.length > 1) {
        result.$and = conditions
      }

      if (searchString) {
        result.searchString = searchString
      }

      return result
    },

    transformFiltersToSqlQuery(activeFilters, filterConfig) {
      const result = {}
      let searchString = null

      for (const key in filterConfig) {
        const config = filterConfig[key]
        const activeFilter = activeFilters[key]

        if (!activeFilter) continue
        if (Array.isArray(activeFilter) && activeFilter.length === 0) continue

        if (config.type === 'timePeriod') {
          const duration = Duration.fromISO(activeFilter.value)
          const dateThreshold = DateTime.now().minus(duration).toISO()

          const fieldName = config.field || key
          
          // Convert field name to camelCase
          const camelCaseFieldName = this.toCamelCase(fieldName)
          
          // Add After field for filtering records after the threshold date
          result[`${camelCaseFieldName}After`] = dateThreshold
          
          // Optionally add Before field if needed for range filtering
          // result[`${camelCaseFieldName}Before`] = DateTime.now().toISO()
        } else if (config.type === 'search') {
          const searchValue = activeFilter.value !== undefined ? activeFilter.value : activeFilter
          searchString = searchValue
        } else {
          if (config.multiple) {
            const values = Array.isArray(activeFilter)
              ? activeFilter.map((item) => (item.value !== undefined ? item.value : item))
              : [activeFilter.value !== undefined ? activeFilter.value : activeFilter]
            
            // Convert to camelCase with 'In' suffix
            const fieldName = this.toCamelCaseWithIn(config.key)
            result[fieldName] = values
          } else {
            const value = activeFilter.value !== undefined ? activeFilter.value : activeFilter
            result[config.key] = Array.isArray(value) ? value : value
          }
        }
      }

      if (searchString) {
        result.searchString = searchString
      }

      return result
    },

    toCamelCase(str) {
      // Convert snake_case or kebab-case to camelCase
      return str.replace(/[-_](.)/g, (_, char) => char.toUpperCase())
    },

    toCamelCaseWithIn(str) {
      // Convert snake_case or kebab-case to camelCase and add 'In' suffix
      const camelCase = str.replace(/[-_](.)/g, (_, char) => char.toUpperCase())
      return camelCase + 'In'
    },

    updateVisibleFilters({ value: key }) {
      this.$emit('update:config', { ...this.config, [key]: { ...this.config[key], is_hidden: false } })
    },
    hideFilter(key) {
      this.$emit('update:config', { ...this.config, [key]: { ...this.config[key], is_hidden: true } })
      this.filter = { ...this.filter, [key]: null }
    },
    setFilter(key, value) {
      console.log('setFilter', key, value)
      this.filter = { ...this.filter, [key]: value }
    },
    setDefault() {
      for (const i in this.processedConfigs) {
        const config = this.processedConfigs[i]
        const key = config.key
        if (config.default && !config.is_hidden) {
          if (config.multiple) {
            const defaultOptions = config.default.map((defaultValue) => config.options.find((option) => option.value === defaultValue))
            this.filter = { ...this.filter, [key]: defaultOptions }
          } else {
            const defaultOption = config.options.find((option) => option.value === config.default)
            this.filter = { ...this.filter, [key]: defaultOption }
          }
        } else {
          this.filter = { ...this.filter, [key]: null }
        }
      }
    },
    clearAll() {
      this.filter = {}
    },
    clearFilter(keys) {
      keys = Array.isArray(keys) ? keys : [keys]
      this.filter = Object.fromEntries(Object.entries(this.filter).filter(([key]) => !keys.includes(key)))
    },
  },
}
</script>

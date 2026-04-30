<template>
  <div class="stack fit" data-gap="0">
    <div v-if="selectedRow" class="flex-1 fit">
      <div class="cluster km-table-chip km-small-chip text-black">{{ selectedRow.in }}</div>
      <div class="cluster pt-sm" data-justify="between">
        <div class="basis-12 py-sm">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
          <km-input :model-value="selectedRow.name" readonly />
        </div>
        <div class="basis-12 py-sm">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_description() }}</div>
          <div class="km-textarea-relaxed">
            <km-input v-model="description" type="textarea" rows="3" autogrow />
          </div>
        </div>
        <div class="cluster full-width" data-gap="lg" data-wrap="no">
          <div class="flex-1">
            <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_type() }}</div>
            <km-select v-model="type" class="full-width" :options="[&quot;string&quot;, &quot;number&quot;, &quot;integer&quot;, &quot;boolean&quot;, &quot;array&quot;, &quot;object&quot;]" />
          </div>
          <div class="flex-1">
            <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_responseFormat() }}</div>
            <km-select v-model="format" class="full-width" :options="formatOptions" :disable="formatOptions.length === 0" :disabled="formatOptions.length === 0" />
          </div>
        </div>
        <div class="stack mt-lg full-width" data-gap="0">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.apiTools_enumValues() }}</div>
          <template v-for="(item, index) in enumValues" :key="index">
            <div class="cluster" data-gap="sm" data-wrap="no">
              <km-input class="mb-sm full-width" :model-value="item" @update:model-value="(e) =&gt; setEnum(e, index)" />
              <km-btn flat icon="delete" icon-size="14px" @click="removeEnum(index)" />
            </div>
          </template>
        </div>
        <km-btn :label="m.common_add()" flat icon="add" icon-size="14px" @click="newEnum(&quot;&quot;)" />
      </div>
    </div>
  </div>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  props: {
    selectedRow: {
      type: Object,
      default: null,
    },
  },
  setup() {
    const { draft, updateField } = useEntityDetail('api_servers')
    return {
      m,
      list: ref([]),
      draft,
      updateField,
    }
  },

  computed: {
    formatOptions() {
      if (this.type === 'integer') {
        return ['', 'int32', 'int64']
      }
      if (this.type === 'number') {
        return ['', 'float', 'double']
      }
      if (this.type === 'string') {
        return ['', 'date', 'date-time', 'password', 'byte', 'binary', 'email', 'uuid', 'uri', 'hostname', 'ipv4', 'ipv6']
      }
      return []
    },
    toolIndex() {
      const tools = this.draft?.tools
      if (!tools) return -1
      return tools.findIndex((tool) => tool.system_name === this.$route.params.name)
    },
    apiTool() {
      if (this.toolIndex === -1) return undefined
      return this.draft?.tools?.[this.toolIndex]
    },
    input: {
      get() {
        if (this.selectedRow && this.apiTool) {
          return this.apiTool?.parameters?.input?.properties[this.selectedRow.in].properties[this.selectedRow.name]
        }
        return {}
      },
    },
    description: {
      get() {
        return this.input?.description
      },
      set(value) {
        this.setInputProp(value, 'description')
      },
    },
    type: {
      get() {
        return this.input?.type
      },
      set(value) {
        this.setInputProp(value, 'type')
      },
    },
    format: {
      get() {
        return this.input?.format ?? ''
      },
      set(value) {
        this.setInputProp(value, 'format')
      },
    },
    enumValues: {
      get() {
        return this.input?.enum
      },
    },
  },
  watch: {
    type() {
      const hasFormat = Object.hasOwn(this.input, 'format')
      if (hasFormat) {
        this.format = ''
      }
    },
  },
  methods: {
    setInputProp(value, key) {
      if (this.toolIndex === -1) return
      const target = `tools.${this.toolIndex}.parameters.input.properties.${this.selectedRow.in}.properties.${this.selectedRow.name}.${key}`
      this.updateField(target, value)
    },
    newEnum(value) {
      const array = this.enumValues || []
      array.push(value)
      this.setInputProp(array, 'enum')
    },
    setEnum(value, index) {
      const array = this.enumValues || []
      array[index] = value
      this.setInputProp(array, 'enum')
    },
    removeEnum(index) {
      const array = this.enumValues
      array?.splice(index, 1)
      this.setInputProp(array, 'enum')
    },
  },
}
</script>

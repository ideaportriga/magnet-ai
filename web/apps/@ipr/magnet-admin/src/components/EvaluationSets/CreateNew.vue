<template>
  <km-popup-confirm :visible="showNewDialog" :title="m.dialog_newTestSet()" :confirm-button-label="m.common_save()" :cancel-button-label="m.common_cancel()" :loading="loading" @confirm="createEvaluationSet" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_name() }}
      <div class="full-width">
        <km-input ref="nameRef" v-model="name" height="30px" :placeholder="m.placeholder_exampleMyFirstTestSet()" :rules="config.name.rules" />
      </div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_systemName() }}
      <div class="full-width">
        <km-input ref="system_nameRef" v-model="system_name" height="30px" :placeholder="m.placeholder_exampleMyFirstTestSetSystemName()" :rules="config.system_name.rules" />
      </div>
      <div class="km-description text-secondary-text pb-xs">{{ m.hint_systemNameUniqueId() }}</div>
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
      {{ m.common_type() }}
      <km-select ref="typeRef" v-model="newRow.type" min-height="30px" max-height="30px" :placeholder="m.common_type()" :options="typeOptions" option-value="value" emit-value map-options :rules="config.type.rules" />
    </div>
    <div v-if="!copy" class="km-field text-secondary-text pb-xs pl-sm">
      {{ m.label_file() }}
      <km-file-picker ref="fileRef" v-model="newRow.file" class="km-control km-input rounded-borders" style="block-size: 30px" outlined :label="m.common_fileUpload()" accept=".xlsx, .xls" dense>
        <template #append>
          <km-glyph name="attach" />
        </template>
      </km-file-picker>
      <div class="km-description text-secondary-text py-xs">{{ m.hint_evaluationSetImportFormat() }}</div>
    </div>
  </km-popup-confirm>
</template>
<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { cloneDeep } from 'lodash'
import { toUpperCaseWithUnderscores } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { validateRef } from '@/utils/validateRef'
import { typeOptions } from '@/config/evaluation_sets/evaluation_sets'

export default {
  props: {
    copy: {
      type: Boolean,
      default: false,
    },
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup(props, { emit }) {
    const router = useRouter()
    const queries = useEntityQueries()
    const { draft } = useEntityDetail('evaluation_sets')
    // §B.8 — useSafeMutation ensures `loading.value` is reset on failure
    // and surfaces a notifyError toast; previously a 500 left the form
    // frozen in loading state with no feedback.
    const createEntity = useSafeMutation(queries.evaluation_sets.useCreate())

    const entityConfig = useEntityConfig('evaluation_sets')
    const config = computed(() => entityConfig.config || {})
    const requiredFields = computed(() => entityConfig.requiredFields || [])

    const loading = ref(false)
    const createNew = ref(false)
    const newRow = reactive({
      name: '',
      description: '',
      system_name: '',
    })
    const autoChangeCode = ref(true)
    let isMounted = false

    const name = computed({
      get() { return newRow?.name || '' },
      set(val) {
        newRow.name = val
        if (autoChangeCode.value && isMounted) newRow.system_name = toUpperCaseWithUnderscores(val)
      },
    })

    const system_name = computed({
      get() { return newRow?.system_name || '' },
      set(val) {
        newRow.system_name = val
        autoChangeCode.value = false
      },
    })

    const currentRaw = computed(() => draft.value)

    const instance = getCurrentInstance()

    onMounted(() => {
      if (props.copy) {
        const raw = cloneDeep(currentRaw.value)
        Object.assign(newRow, raw)
        newRow.name = newRow.name + '_COPY'
        newRow.description = newRow.description + '_COPY'
        newRow.system_name = newRow.system_name + '_COPY'
        delete newRow.id
      }
      isMounted = true
    })

    onBeforeUnmount(() => {
      isMounted = false
      emit('cancel')
    })

    function validateFields() {
      const validStates = requiredFields.value.map((field) => validateRef(instance.refs[`${field}Ref`]))
      return !validStates.includes(false)
    }

    async function createEvaluationSet() {
      if (!validateFields()) return
      createNew.value = false
      loading.value = true
      const { success, data } = await createEntity.run(newRow)
      loading.value = false
      if (!success || !data) return
      router.push(`/evaluation-sets/${data.id}`)
    }

    return {
      m,
      typeOptions,
      createEntity,
      config,
      requiredFields,
      loading,
      createNew,
      newRow,
      autoChangeCode,
      name,
      system_name,
      currentRaw,
      createEvaluationSet,
    }
  },
}
</script>


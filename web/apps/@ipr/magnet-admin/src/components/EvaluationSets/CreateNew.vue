<template lang="pug">
km-popup-confirm(
  :visible='showNewDialog',
  :title='m.dialog_newTestSet()',
  :confirmButtonLabel='m.common_save()',
  :cancelButtonLabel='m.common_cancel()',
  @confirm='createEvaluationSet',
  @cancel='$emit("cancel")',
  :loading='loading'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_name() }}
    .full-width
      km-input(height='30px', :placeholder='m.placeholder_exampleMyFirstTestSet()', v-model='name', ref='nameRef', :rules='config.name.rules')
  //- .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Description
  //-   .full-width
  //-     km-input(
  //-       height='30px',
  //-       placeholder='E.g. My first test set for RAG',
  //-       v-model='newRow.description',
  //-       ref='descriptionRef',
  //-       :rules='config.description.rules'
  //-     )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_systemName() }}
    .full-width
      km-input(height='30px', :placeholder='m.placeholder_exampleMyFirstTestSetSystemName()', v-model='system_name', ref='system_nameRef', :rules='config.system_name.rules')
    .km-description.text-secondary-text.q-pb-4 {{ m.hint_systemNameUniqueId() }}
  .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_type() }}
    km-select(
      minHeight='30px',
      maxHeight='30px',
      :placeholder='m.common_type()',
      :options='typeOptions',
      v-model='newRow.type',
      ref='typeRef',
      option-value='value',
      emit-value,
      map-options,
      :rules='config.type.rules'
    )
  .km-field.text-secondary-text.q-pb-xs.q-pl-8(v-if='!copy') {{ m.label_file() }}
    q-file.km-control.km-input.rounded-borders(
      style='height: 30px',
      outlined,
      :label='m.common_fileUpload()',
      ref='fileRef',
      v-model='newRow.file',
      accept='.xlsx, .xls',
      dense
    )
      template(v-slot:append)
        q-icon(name='attach_file')

    .km-description.text-secondary-text.q-py-4 {{ m.hint_evaluationSetImportFormat() }}
    //- template(v-slot:prepend)
    //-   q-icon(name='attach_file')
    //- template(v-slot:append)
      //- q-icon(name='close', @click="newRow.file = null", color='icon', size='24px')
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
    const { mutateAsync: createEntity } = queries.evaluation_sets.useCreate()

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
      const validStates = requiredFields.value.map((field) => instance.refs[`${field}Ref`]?.validate())
      return !validStates.includes(false)
    }

    async function createEvaluationSet() {
      if (!validateFields()) return
      createNew.value = false
      loading.value = true
      const { id: inserted_id } = await createEntity(newRow)
      loading.value = false
      router.push(`/evaluation-sets/${inserted_id}`)
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

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: var(--q-white) !important;
</style>

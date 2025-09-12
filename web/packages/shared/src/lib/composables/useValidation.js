import { ref, computed, watch } from 'vue'

export default function useValidation(value, rules) {
  const runValidation = ref(false)
  const errorMessages = ref([])
  const errorMessage = computed(() => errorMessages.value[0])

  function executeValidationRulesIfNeeded(current) {
    if (runValidation.value && rules?.value?.length) {
      errorMessages.value = rules.value
        .map((rule) => {
          return rule(current ?? value.value)
        })
        .filter((ruleOutput) => ruleOutput !== true)
    }
  }

  function validate(current) {
    runValidation.value = true
    executeValidationRulesIfNeeded(current)
    return !errorMessage.value
  }

  function resetValidation() {
    runValidation.value = false
    errorMessages.value = []
  }

  watch(value, () => {
    executeValidationRulesIfNeeded()
  })

  return {
    errorMessage,
    validate,
    resetValidation,
  }
}

export function validationProps() {
  return {
    rules: [Object, Array],
  }
}

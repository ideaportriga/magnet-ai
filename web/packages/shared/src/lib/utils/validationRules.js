import { isString } from 'lodash'

const REQUIRED_DEFAULT_MESSAGE = 'Field can not be empty'
const MINLEGTH_DEFAULT_MESSAGE = (min) => `Field must consist of more than ${min} characters`
const INVALID_JSON_MESSAGE = ' Incorect json format'

export const required = (message) => {
  return (value) => {
    if (isString(value)) {
      value = value.trim()
    }
    return !!value || (message ?? REQUIRED_DEFAULT_MESSAGE)
  }
}

export const minLength = (min, message) => {
  return (value) => {
    if (isString(value)) {
      value = value.trim()
    }
    return value?.length >= min || (message ?? MINLEGTH_DEFAULT_MESSAGE(min))
  }
}
export const validJson = (message) => {
  return (value) => {
    try {
      JSON.parse(value)
    } catch {
      return message ?? INVALID_JSON_MESSAGE
    }
    return false
  }
}

export const notGreaterThan = (max, message) => {
  return (value) => {
    return value <= max || (message ?? `Field must be less than ${max}`)
  }
}

export const notLessThan = (min, message) => {
  return (value) => {
    return value >= min || (message ?? `Field must be greater than ${min}`)
  }
}

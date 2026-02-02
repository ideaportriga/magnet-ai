import { isString } from 'lodash'

const REQUIRED_DEFAULT_MESSAGE = 'Field can not be empty'
const MINLEGTH_DEFAULT_MESSAGE = (min) => `Field must consist of more than ${min} characters`
const INVALID_JSON_MESSAGE = ' Incorect json format'
const INVALID_SYSTEM_NAME_MESSAGE = 'System name can only contain letters, numbers, underscores and hyphens, and must not start with a number'
const INVISIBLE_CHARS_MESSAGE = 'Field contains invisible or whitespace characters that are not allowed'

// Regex to detect invisible/whitespace characters (except regular space within text)
// eslint-disable-next-line no-control-regex
const INVISIBLE_CHARS_REGEX = /[\u0000-\u001F\u007F-\u009F\u00A0\u1680\u180E\u2000-\u200F\u2028\u2029\u202F\u205F\u2060\u3000\uFEFF]/

// Regex for valid system_name: starts with letter or underscore, followed by letters, numbers, underscores, hyphens
const VALID_SYSTEM_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_-]*$/

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

/**
 * Validates that a value does not contain invisible or problematic whitespace characters.
 * Allows regular spaces within text but not leading/trailing spaces or special Unicode whitespace.
 */
export const noInvisibleChars = (message) => {
  return (value) => {
    if (!isString(value)) return true
    
    // Check for leading/trailing whitespace
    if (value !== value.trim()) {
      return message ?? 'Field must not have leading or trailing spaces'
    }
    
    // Check for invisible Unicode characters
    if (INVISIBLE_CHARS_REGEX.test(value)) {
      return message ?? INVISIBLE_CHARS_MESSAGE
    }
    
    return true
  }
}

/**
 * Validates system_name format:
 * - Must start with a letter or underscore
 * - Can only contain letters, numbers, underscores and hyphens
 * - No spaces or special characters
 * - No invisible characters
 */
export const validSystemName = (message) => {
  return (value) => {
    if (!isString(value) || !value) return true // Let required() handle empty values
    
    const trimmed = value.trim()
    
    // Check for leading/trailing whitespace (means original had spaces)
    if (value !== trimmed) {
      return 'System name must not have leading or trailing spaces'
    }
    
    // Check for invisible Unicode characters
    if (INVISIBLE_CHARS_REGEX.test(value)) {
      return 'System name contains invisible characters that are not allowed'
    }
    
    // Check for valid format
    if (!VALID_SYSTEM_NAME_REGEX.test(value)) {
      return message ?? INVALID_SYSTEM_NAME_MESSAGE
    }
    
    return true
  }
}

import { DateTime } from 'luxon'
import { get, isObject } from 'lodash'

async function fetchData(props) {
  const { endpoint = '', method = 'GET', service = '', headers, body, queryParams, credentials, signal } = props
  const options = {
    method,
    ...(!!credentials && { credentials }),
    ...(!!headers && { headers }),
    ...(!!body && { body }),
    ...(!!signal && { signal }),
  }

  async function handleErrors(response) {
    if (!response.ok) {
      const errorText = await response.text()
      throw Error(errorText)
    }
    return response
  }

  const response = await fetch(
    `${endpoint}${service ? `/${service}` : ''}${queryParams ? `?${new URLSearchParams(queryParams).toString()}` : ''}`,
    options
  )
    .then(handleErrors)
    .catch((error) => ({ error }))

  return response
}

const toKebabCase = (str) =>
  str &&
  str
    .match(/[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+/g)
    .map((x) => x.toLowerCase())
    .join('-')

function getUrlParameter(location, name, decodeConcatSymbol = true) {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]')
  const regex = new RegExp('[\\?&]' + name + '=([^&#]*)')
  const results = regex.exec(location)
  if (results === null) {
    return ''
  } else {
    return decodeConcatSymbol ? decodeURIComponent(results[1].replace(/\+/g, ' ')) : decodeURIComponent(results[1])
  }
}

function formatDate(val, format = 'LL/dd/yyyy') {
  return val?.isLuxonDateTime && val.isValid ? val.toFormat(format) : ''
}
export function compareLuxonDates(a, b) {
  return a.toMillis() - b.toMillis()
}

// Parse date fields to LUXON in array of objects
function parseDates(items = [], fields = [], format) {
  return items.map((item) => {
    Object.keys(item).forEach((key) => {
      if (fields.includes(key)) {
        if (format === 'SQL') item[key] = DateTime.fromSQL(item[key]) ?? ''
      }
    })
    return item
  })
}

function hasProps(obj = {}, props = []) {
  return props.every((prop) => prop in obj)
}

function readFileBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64String = window.btoa(reader.result)
      resolve(base64String)
    }

    reader.onerror = reject
    reader.readAsBinaryString(file)
  })
}

const alphabeticCollator = new Intl.Collator('sv')

function sortAlphabetically(array, fieldPath) {
  return array.slice().sort((a, b) => {
    const [valueA, valueB] = [a, b].map((el) => (fieldPath ? get(el, fieldPath) : el))
    return alphabeticCollator.compare(valueA, valueB)
  })
}

function formatOptions(options, labelProp = 'label', valueProp = 'value') {
  // console.log('formatOptions:', options)
  if (Array.isArray(options)) {
    const result = options
      .map((item) => {
        let res = {}
        if (isObject(item)) {
          if (valueProp in item) {
            res = item
            if (!(labelProp in item)) res.label = res.value
          } else {
            console.warn('formatOptions: option is skipped as it does not contain value prop', item)
            res = undefined
          }
        } else if ([undefined, null, ''].includes(item) || (typeof item === 'string' && item.trim() === '')) {
          console.warn('formatOptions: option is skipped as it has wrong value', item)
          res = undefined
        } else {
          res.label = item
          res.value = item
        }
        return res
      })
      .filter((item) => !!item)

    // console.log('formatOptions: after', result)
    return result
  } else {
    console.warn('formatOptions: options should be array', options)
    return []
  }
}

function daysToDate(val) {
  return DateTime.now().startOf('day').plus({ days: val })
}

function formatNumber(val, format = 'en', options = { maximumFractionDigits: 20 }) {
  val = String(val)
  const unforrmattedVal = val?.replace(',', '')
  if (isNaN(unforrmattedVal)) {
    console.warn(`NaN(${val}) is passed to formatNumber`)
    return '0'
  }
  return new Intl.NumberFormat(format, options).format(unforrmattedVal)
}

function pluralize(word, qty, isWithQty) {
  let pluralizeWord = word

  if (Math.abs(qty) !== 1) {
    pluralizeWord = `${word}s`
  }

  if (isWithQty) {
    return `${qty} ${pluralizeWord}`
  }
  return `${pluralizeWord}`
}

const newShade = (hexColor, magnitude) => {
  hexColor = hexColor.replace(`#`, ``)
  if (hexColor.length === 6) {
    const decimalColor = parseInt(hexColor, 16)
    let r = (decimalColor >> 16) + magnitude
    r > 255 && (r = 255)
    r < 0 && (r = 0)
    let g = (decimalColor & 0x0000ff) + magnitude
    g > 255 && (g = 255)
    g < 0 && (g = 0)
    let b = ((decimalColor >> 8) & 0x00ff) + magnitude
    b > 255 && (b = 255)
    b < 0 && (b = 0)
    return `#${(g | (b << 8) | (r << 16)).toString(16)}`
  } else {
    return hexColor
  }
}

const deepEqual = (value1, value2) => {
  if (value1 !== value2 && (!value1 || !value2)) return false
  value1 = JSON.parse(JSON.stringify(value1))
  value2 = JSON.parse(JSON.stringify(value2))
  if (value1 === value2) {
    return true
  }

  if (
    (typeof value1 !== 'object' && typeof value1 !== 'function') ||
    value1 === null ||
    (typeof value2 !== 'object' && typeof value2 !== 'function') ||
    value2 === null
  ) {
    return false
  }

  if (typeof value1 === 'object' && typeof value2 === 'object') {
    const keys1 = Object.keys(value1)
    const keys2 = Object.keys(value2)

    if (keys1.length !== keys2.length) {
      return false
    }

    for (const key of keys1) {
      if (!keys2.includes(key) || !deepEqual(value1[key], value2[key])) {
        return false
      }
    }

    return true
  }

  // If values are functions, compare their source code
  if (typeof value1 === 'function' && typeof value2 === 'function') {
    return value1.toString() === value2.toString()
  }

  // For other types, perform a simple equality check
  return value1 === value2
}

const cleanNewObject = (object) => JSON.parse(JSON.stringify(object))

function toUpperCaseWithUnderscores(str) {
  return str.trim().replace(/\s+/g, '_').toUpperCase()
}

export {
  pluralize,
  formatNumber,
  formatDate,
  formatOptions,
  getUrlParameter,
  parseDates,
  hasProps,
  readFileBase64,
  sortAlphabetically,
  daysToDate,
  newShade,
  fetchData,
  toKebabCase,
  deepEqual,
  cleanNewObject,
  toUpperCaseWithUnderscores,
}

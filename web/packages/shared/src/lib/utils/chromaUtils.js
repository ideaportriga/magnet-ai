import { DateTime } from 'luxon'
import { deepEqual } from './base'

function transformChromaResponse(items, ignoreFormat = false) {
  // eslint-disable-next-line @typescript-eslint/no-this-alias
  const config = this //config is bound in store

  items = Array.isArray(items) ? items : [items]
  return items.map((item) => {
    if (!item) return
    // TODO: Do we really need to handle metadata here?
    // if(item.metadata) {
    //     item = { ...item, ...item.metadata}
    //     delete item.metadata
    // }
    const formated = {}
    let children = []
    Object.keys(item).forEach((key) => {
      if (!config[key]) {
        formated[key] = valueConverter(item[key], config[key]?.type, ignoreFormat)
      } else {
        formated[key] = valueConverter(item[key], config[key]?.type, ignoreFormat)
        if (config[key].children) {
          const childFields = config[key]?.children[item[key]]
          if (childFields) children.push(...childFields.map(({ field }) => field))
        }
      }
    })
    //format children (currently only for source type)
    children.forEach((child) => {
      if (item[child]) {
        delete formated[child]
        formated[child] = valueConverter(item[child], 'String', ignoreFormat)
      }
    })
    return formated
  })
}

function transformChromaRequest(item, original) {
  // eslint-disable-next-line @typescript-eslint/no-this-alias
  const config = this //config is bond in store
  //transform keys to one level
  item = {
    ...(item ?? {}),
    ...(item.metadata ?? {}),
  }
  original = {
    ...(original ?? {}),
    ...(original.metadata ?? {}),
  }
  const formated = {}
  Object.keys(item).forEach((key) => {
    if (deepEqual(item[key], original[key])) return
    if (!config[key]) {
      formated[key] = item[key]
    }
    if (config[key]?.ignorePatch) return
    formated[key] = valueReverter(item[key], config[key]?.type)
  })
  return formated
}

const valueConverter = (value, type, ignoreFormat = false) => {
  if (ignoreFormat) return value
  if (type === 'String') return value
  if (type === 'Date') return DateTime.fromISO(value)
  if (type === 'Boolean') return typeof value === 'number' ? Boolean(value) : value === 'true'
  return value
}
const valueReverter = (value, type, ignoreFormat = false) => {
  if (ignoreFormat) return value
  if (type === 'String') return value
  if (type === 'Date') return value?.toISO()
  if (type === 'Boolean') return value.toString()
  return value
}

export { transformChromaRequest, transformChromaResponse }

import { DateTime } from 'luxon'

function transformStrapiResponse(data) {
  // eslint-disable-next-line @typescript-eslint/no-this-alias
  const config = this
  if (!data?.length) return []
  return data?.map((item) => {
    let formated = {
      ...item,
      ...(item.attributes ?? {}),
    }
    delete formated.attributes
    Object.keys(formated).forEach((key) => {
      if (config[key]?.type === 'StrapiDataObject') {
        const format = transformStrapiResponse.bind(config[key]?.config)
        if (formated[key]?.data) formated[key] = format(formated[key].data)
      } else {
        formated[key] = valueConverter(formated[key], config[key]?.type) //add format
      }
    })
    formated['slug'] = formated.id
    return formated
  })
}
function transformStrapiRequest(item, original) {
  // eslint-disable-next-line @typescript-eslint/no-this-alias
  const config = this
  const formated = {}
  Object.keys(item).forEach((key) => {
    if (config[key]?.ignorePatch) return
    if (config[key]?.type === 'object') {
      //item[key] = transformStrapiRequest(item[key], original?.[key])
    } else {
      if (original && item[key] === original[key]) return
      formated[key] = valueReverter(item[key], config[key]?.type) //add format
    }
  })
  return formated
}

const valueConverter = (value, type, ignoreFormat = false) => {
  if (ignoreFormat) return value
  if (type === 'String') return value
  if (type === 'Date') return DateTime.fromISO(value)
  if (type === 'Boolean' && typeof value != 'boolean') {
    return typeof value === 'number' ? Boolean(value) : value === 'true'
  }
  return value
}
const valueReverter = (value, type, ignoreFormat = false) => {
  if (ignoreFormat) return value
  if (type === 'String') return String(value)
  if (type === 'Date') return value?.toISO()
  if (type === 'Boolean') return value.toString()
  return value
}

export { transformStrapiRequest, transformStrapiResponse }

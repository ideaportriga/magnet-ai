export const transformFilterToMongoQuery = (filterObject) => {
  const mongoQuery = {}

  if (filterObject.search) {
    const { value, fields } = filterObject.search
    if (value && fields.length) {
      mongoQuery.$or = fields.map((field) => ({
        [field]: { $txt: value },
      }))
    }
  }

  if (filterObject.filters) {
    const orConditions = []

    Object.entries(filterObject.filters).forEach(([field, filter]) => {
      const { operator, value } = filter
      switch (operator) {
        case 'eq':
          console.log('value', value)
          mongoQuery[field] = value
          console.log('mongoQuery', mongoQuery)
          break
        case 'ne':
          mongoQuery[field] = { $ne: value }
          break
        case 'lt':
          mongoQuery[field] = { $lt: value }
          break
        case 'lte':
          mongoQuery[field] = { $lte: value }
          break
        case 'gt':
          mongoQuery[field] = { $gt: value }
          break
        case 'gte':
          mongoQuery[field] = { $gte: value }
          break
        case 'in':
          mongoQuery[field] = { $in: value }
          break
        case 'nin':
          mongoQuery[field] = { $nin: value }
          break
        case 'contains':
          mongoQuery[field] = { $txt: value }
          break
        case 'or':
          if (Array.isArray(value) && value.length) {
            orConditions.push(...value.map((v) => ({ [field]: v })))
          }
          break
        default:
          break
      }
    })

    if (orConditions.length) {
      mongoQuery.$or = [...(mongoQuery.$or || []), ...orConditions]
    }
  }

  return mongoQuery
}

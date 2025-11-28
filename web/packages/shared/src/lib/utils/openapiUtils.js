function getLabel(raw_name) {
  const name = raw_name.replace(/-/g, '_')
  let words = name.match(/[A-Za-z][a-z]*/g)
  words = words.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
  return words.join(' ')
}

function toSnakeCase(variable_name) {
  variable_name = variable_name.replace(/ /g, '_')
  variable_name = variable_name.replace(/([a-z0-9])([A-Z])/g, '$1_$2')
  variable_name = variable_name.replace(/[-_]/g, '_')
  return variable_name.toLowerCase()
}

const getSchemaProperties = (schema, parent) => {
  const result = []
  if (schema.type === 'object') {
    for (const [name, prop] of Object.entries(schema.properties || {})) {
      const field = {
        parent_type: parent.type,
        parent_name: parent.name || '',
        category: parent.category,
        required: schema.required ? schema.required.includes(name) : false,
        name: parent.name ? `${parent.name}.${name}` : name,
        label: getLabel(name),
        options: prop.enum || null,
        ...prop,
      }
      if (field.type === 'object') {
        const properties = field.properties || {}
        const required = field.required || []
        result.push(
          ...getSchemaProperties(
            {
              type: 'object',
              properties,
              required,
            },
            field
          )
        )
      }
      if (field.type === 'array') {
        const items = field.items || {}
        field.type = `${field.type}[${items.type}]`
        if (items.type === 'object') {
          result.push(...getSchemaProperties(items, field))
        }
      }
      result.push(field)
    }
  }
  if (schema.type === 'array') {
    const items = schema.items || {}
    result.push(
      ...getSchemaProperties(items, {
        type: 'array',
        category: parent.category,
        name: parent.name ? `${parent.name}.array` : '',
      })
    )
  }
  return result
}

function getSpecificationItems(spec, method, path) {
  const fields = []
  const pathObject = spec?.paths?.[path]

  if (pathObject) {
    const operation = pathObject[method]
    if (operation) {
      if (operation.parameters) {
        operation.parameters.forEach((parameter) => {
          const field = {
            category: parameter.in,
            required: parameter.required,
            name: parameter.name,
            label: getLabel(parameter.name),
            description: parameter.description,
            options: parameter.schema ? parameter.schema.enum : null,
            ...parameter.schema,
          }
          if (field.type === 'object') {
            const properties = field.properties || {}
            const required = field.required || []
            fields.push(
              ...getSchemaProperties(
                {
                  type: 'object',
                  properties,
                  required,
                },
                field
              )
            )
          }
          if (field.type === 'array') {
            const items = field.items || {}
            field.type = `${field.type}[${items.type}]`
            if (items.type === 'object') {
              fields.push(...getSchemaProperties(items, field))
            }
          }
          fields.push(field)
        })
      }

      if (operation.requestBody) {
        const schema = Object.values(operation.requestBody.content)[0].schema
        fields.push(
          ...getSchemaProperties(schema, {
            category: 'body',
            type: schema.type,
          })
        )
      }

      if (operation.responses && operation.responses['200']) {
        const schema = Object.values(operation.responses['200'].content)[0].schema
        fields.push(
          ...getSchemaProperties(schema, {
            category: 'response',
            type: schema.type,
          })
        )
      }
    }
  }
  return fields
}

export { getLabel, getSpecificationItems, toSnakeCase }

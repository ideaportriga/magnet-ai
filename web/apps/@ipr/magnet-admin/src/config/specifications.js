import { getSpecificationItems } from '@shared/utils/openapiUtils'
import { required } from '@shared/utils/validationRules'

export default [
  [
    {
      type: 'select',
      name: 'type',
      placeholder: 'Type',
      label: 'Type',
      rules: () => [required()],
      options: () => ['Query', 'Update', 'Insert', 'Custom'],
    },
  ],
  [
    {
      name: 'agent',
      placeholder: 'Agent',
      label: 'Agent',
      visibleIf: (context) => context['type'] === 'Custom',
    },
  ],
  [
    {
      type: 'select',
      name: 'open_api_path',
      placeholder: 'Path',
      label: 'Path',
      rules: (context) => (context['type'] !== 'Custom' ? [required()] : [() => true]),
      options: (context) => {
        const spec = context['open_api_spec'].content || {}
        const paths = spec.paths || {}
        return Object.keys(paths)
      },
    },
  ],
  [
    {
      type: 'select',
      name: 'open_api_method',
      placeholder: 'HTTP method',
      label: 'HTTP Method',
      rules: (context) => (context['type'] !== 'Custom' ? [required()] : [() => true]),
      options: (context) => {
        const spec = context['open_api_spec'].content || {}
        const path = context['open_api_path']
        const paths = spec.paths || {}
        return Object.keys(paths[path] || {})
      },
    },
  ],
  [
    {
      type: 'bool',
      name: 'query',
      label: 'Prerquery data',
      getter: (context) => {
        return !!Object.keys(context['open_api_data_query'] || {}).length
      },
      setter: (context, val) => {
        if (val) {
          context['open_api_data_query'] = {
            open_api_spec: {},
            open_api_path: '',
            open_api_method: '',
            mappings: {},
          }
        } else {
          context['open_api_data_query'] = {}
        }
      },
    },
  ],
  [
    {
      lvl: 1,
      name: 'query_open_open_api_spec',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      rules: (context) => (context['type'] !== 'Custom' && !!Object.keys(context['open_api_data_query'] || {}).length ? [required()] : [() => true]),
      getter: (context, { key }) => {
        const query = context['open_api_data_query']
        if (key) {
          return query['open_api_spec'][key]
        } else {
          return query['open_api_spec']
        }
      },
      setter: (context, val, { key }) => {
        const query = context['open_api_data_query']
        if (key) {
          query['open_api_spec'][key] = val
        }
      },
    },
  ],
  [
    {
      type: 'select',
      lvl: 1,
      name: 'query_open_api_path',
      placeholder: 'Query Path',
      label: 'Query Path',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      rules: (context) => (context['type'] !== 'Custom' && !!Object.keys(context['open_api_data_query'] || {}).length ? [required()] : [() => true]),
      options: (context) => {
        const query = context['open_api_data_query']
        const spec = query['open_api_spec'].content || {}
        const paths = spec.paths || {}
        return Object.keys(paths)
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        return query['open_api_path']
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['open_api_path'] = val
      },
    },
  ],
  [
    {
      type: 'select',
      lvl: 1,
      name: 'query_open_api_method',
      placeholder: 'Query HTTP method',
      label: 'Query HTTP method',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      rules: (context) => (context['type'] !== 'Custom' && !!Object.keys(context['open_api_data_query'] || {}).length ? [required()] : [() => true]),
      options: (context) => {
        const query = context['open_api_data_query']
        const spec = query['open_api_spec'].content || {}
        const path = query['open_api_path']
        const paths = spec.paths || {}
        return Object.keys(paths[path] || {})
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        return query['open_api_method']
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['open_api_method'] = val
      },
    },
  ],
  [
    {
      type: 'addChips',
      lvl: 1,
      name: 'query_mappings_in',
      placeholder: 'Query Data Mappings In',
      label: 'Query Data Mappings In',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['in_fn'] || {}
        return !Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = query['mappings'] || {}
        return mappings['in'] || {}
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['mappings'] = query['mappings'] || {}
        query['mappings']['in'] = val
      },
      options: (context) => {
        const query = context['open_api_data_query']
        const path = query.open_api_path
        const method = query.open_api_method
        const spec = query.open_api_spec?.content || {}
        const items = getSpecificationItems(spec, method, path).reduce((result, { name, category }) => {
          if (category !== 'response') {
            result.push(name)
          }
          return result
        }, [])
        return items
      },
    },
    {
      type: 'addCode',
      lvl: 1,
      name: 'query_mappings_in_fn',
      placeholder: 'Query Data Mapping Function In',
      label: 'Query Data Mapping Function In',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['in_fn'] || {}
        return !!Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = query['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['in_fn'] }
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['mappings'] = query['mappings'] || {}
        query['mappings']['in_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'query_in_type',
      label: 'Use data mapping function',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['in_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        if (val) {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['in'] = {}
          query['mappings']['in_fn'] = {
            content: '',
            name: '',
          }
        } else {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['in_fn'] = {}
          query['mappings']['in'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'addChips',
      lvl: 1,
      name: 'query_mappings_out',
      placeholder: 'Query Data Mappings Out',
      label: 'Query Data Mappings Out',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['out_fn'] || {}
        return !Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = query['mappings'] || {}
        return mappings['out'] || {}
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['mappings'] = query['mappings'] || {}
        query['mappings']['out'] = val
      },
      options: (context) => {
        const query = context['open_api_data_query']
        const path = query.open_api_path
        const method = query.open_api_method
        const spec = query.open_api_spec?.content || {}
        const items = getSpecificationItems(spec, method, path).reduce((result, { name, category }) => {
          if (category === 'response') {
            result.push(name)
          }
          return result
        }, [])
        return items
      },
    },
    {
      type: 'addCode',
      lvl: 1,
      name: 'query_mappings_in_fn',
      placeholder: 'Query Data Mapping Function Out',
      label: 'Query Data Mapping Function Out',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['out_fn'] || {}
        return !!Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = query['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['out_fn'] }
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['mappings'] = query['mappings'] || {}
        query['mappings']['out_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'query_out_type',
      label: 'Use data mapping function',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['out_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        if (val) {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['out'] = {}
          query['mappings']['out_fn'] = {
            content: '',
            name: '',
          }
        } else {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['out_fn'] = {}
          query['mappings']['out'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'placeholder',
      lvl: 1,
      name: 'query_mapping_fn_ph',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['mapping_fn'] || {}
        return !Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
    },
    {
      type: 'addCode',
      lvl: 1,
      name: 'query_mapping_fn',
      placeholder: 'Mapping function',
      label: 'Request and response mapping function',
      visibleIf: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['mapping_fn'] || {}
        return !!Object.keys(mappings).length && !!Object.keys(query || {}).length
      },
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = query['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['mapping_fn'] }
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        query['mappings'] = query['mappings'] || {}
        query['mappings']['mapping_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'use_query_mapping_fn',
      label: 'Use request and response mapping function',
      visibleIf: (context) => !!Object.keys(context['open_api_data_query'] || {}).length,
      getter: (context) => {
        const query = context['open_api_data_query']
        const mappings = (query['mappings'] || {})['mapping_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        const query = context['open_api_data_query']
        if (val) {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['mapping_fn'] = {
            content: '',
            name: '',
          }
        } else {
          query['mappings'] = query['mappings'] || {}
          query['mappings']['mapping_fn'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'addChips',
      name: 'mappings_in',
      placeholder: 'Data Mappings In',
      label: 'Data Mappings In',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['in_fn'] || {}
        return !Object.keys(mappings).length
      },
      getter: (context) => {
        const mappings = context['mappings'] || {}
        return mappings['in'] || {}
      },
      setter: (context, val) => {
        context['mappings'] = context['mappings'] || {}
        context['mappings']['in'] = val
      },
      options: (context) => {
        const path = context.open_api_path
        const method = context.open_api_method
        const spec = context.open_api_spec?.content || {}
        const items = getSpecificationItems(spec, method, path).reduce((result, { name, category }) => {
          if (category !== 'response') {
            result.push(name)
          }
          return result
        }, [])
        return items
      },
    },
    {
      type: 'addCode',
      name: 'mappings_in_fn',
      placeholder: 'Data Mapping Function In',
      label: 'Data Mapping Function In',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['in_fn'] || {}
        return !!Object.keys(mappings).length
      },
      getter: (context) => {
        const mappings = context['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['in_fn'] }
      },
      setter: (context, val) => {
        context['mappings'] = context['mappings'] || {}
        context['mappings']['in_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'in_type',
      label: 'Use data mapping function',
      getter: (context) => {
        const mappings = (context['mappings'] || {})['in_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        if (val) {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['in'] = {}
          context['mappings']['in_fn'] = {
            content: '',
            name: '',
          }
        } else {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['in_fn'] = {}
          context['mappings']['in'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'addChips',
      name: 'mappings_out',
      placeholder: 'Data Mappings Out',
      label: 'Data Mappings Out',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['out_fn'] || {}
        return !Object.keys(mappings).length
      },
      getter: (context) => {
        const mappings = context['mappings'] || {}
        return mappings['out'] || {}
      },
      setter: (context, val) => {
        context['mappings'] = context['mappings'] || {}
        context['mappings']['out'] = val
      },
      options: (context) => {
        const path = context.open_api_path
        const method = context.open_api_method
        const spec = context.open_api_spec?.content || {}
        const items = getSpecificationItems(spec, method, path).reduce((result, { name, category }) => {
          if (category === 'response') {
            result.push(name)
          }
          return result
        }, [])
        return items
      },
    },
    {
      type: 'addCode',
      name: 'mappings_out_fn',
      placeholder: 'Data Mapping Function Out',
      label: 'Data Mapping Function Out',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['out_fn'] || {}
        return !!Object.keys(mappings).length
      },
      getter: (context) => {
        const mappings = context['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['out_fn'] }
      },
      setter: (context, val) => {
        context['mappings'] = context['mappings'] || {}
        context['mappings']['out_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'out_type',
      label: 'Use data mapping function',
      getter: (context) => {
        const mappings = (context['mappings'] || {})['out_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        if (val) {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['out'] = {}
          context['mappings']['out_fn'] = {
            content: '',
            name: '',
          }
        } else {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['out_fn'] = {}
          context['mappings']['out'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'placeholder',
      name: 'mapping_fn_ph',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['mapping_fn'] || {}
        return !Object.keys(mappings).length
      },
    },
    {
      type: 'addCode',
      name: 'mapping_fn',
      placeholder: 'Mapping function',
      label: 'Request and response mapping function',
      visibleIf: (context) => {
        const mappings = (context['mappings'] || {})['mapping_fn'] || {}
        return !!Object.keys(mappings).length
      },
      getter: (context) => {
        const mappings = context['mappings'] || {}
        const module = context['module'] || {}
        return { module, ...mappings['mapping_fn'] }
      },
      setter: (context, val) => {
        context['mappings'] = context['mappings'] || {}
        context['mappings']['mapping_fn'] = {
          name: val.name,
        }
        context['module'] = { ...context['module'], ...val.module }
      },
      options: (context) => {
        const code = context['module']?.['content'] || ''
        const regex = /def\s+(\w+)\s*\([^()]*\):/g
        let items = []
        let match
        while ((match = regex.exec(code)) !== null) {
          items.push(match[1])
        }
        return items
      },
    },
    {
      type: 'bool',
      name: 'use_mapping_fn',
      label: 'Use request and response mapping function',
      getter: (context) => {
        const mappings = (context['mappings'] || {})['mapping_fn'] || {}
        return !!Object.keys(mappings).length
      },
      setter: (context, val) => {
        if (val) {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['mapping_fn'] = {
            content: '',
            name: '',
          }
        } else {
          context['mappings'] = context['mappings'] || {}
          context['mappings']['mapping_fn'] = {}
        }
      },
    },
  ],
  [
    {
      type: 'select',
      name: 'ui_type',
      placeholder: 'UI Type',
      label: 'UI Type',
      rules: (context) => (context['type'] !== 'Custom' ? [required()] : [() => true]),
      options: (context) => {
        const type = context.type || ''
        const types = [
          'inForm',
          'inSelectManyForm',
          'inSelectOneList',
          'inSelectManyList',
          'outForm',
          'outList',
          'outSelectOneList',
          'outSelectManyList',
        ]
        if (['Query'].includes(type)) {
          return types.filter((item) => item.startsWith('out'))
        } else if (['Update', 'Insert'].includes(type)) {
          return types.filter((item) => item.startsWith('in'))
        } else if (type) {
          return types
        } else {
          return []
        }
      },
    },
  ],
  [
    {
      name: 'ui_name',
      placeholder: 'UI Name',
      label: 'UI Name',
    },
  ],
  [
    {
      name: 'ui_description',
      placeholder: 'UI Description',
      label: 'UI Description',
    },
  ],
  [
    {
      type: 'pickChips',
      name: 'ui_items',
      placeholder: 'UI Items',
      label: 'UI Items',
      options: (context) => {
        const path = context.open_api_path
        const method = context.open_api_method
        const spec = context.open_api_spec?.content || {}
        const items = getSpecificationItems(spec, method, path).reduce((result, { name, category }) => {
          if (
            (context.type === 'Query' && category === 'response') ||
            ((context.type === 'Update' || context.type === 'Insert') && category !== 'response') ||
            context.type === 'Custom'
          ) {
            result.push(name)
          }
          return result
        }, [])
        return items
      },
    },
  ],
  [
    {
      name: 'ui_option_format',
      placeholder: 'Option Format',
      label: 'Option Format',
    },
  ],
]

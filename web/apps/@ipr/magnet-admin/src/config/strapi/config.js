import templatesControls from '@/config/strapi/controls/templates'
import promptsControls from '@/config/strapi/controls/prompts'
import { fetchData } from '@shared'
import patchObject from '@shared/utils/patchObject'
import store from '@/store'

export const controlsDefaultProps = {
  align: 'left',
  sortable: true,
  action: false,
  display: true,
  type: 'String',
  format: (val) => (val?.length ? val : '-'),
  fromMetadata: true,
  readonly: false,
  ignorePatch: false,
  rules: [],
}

const promptsTablePagination = {
  rowsPerPage: 10,
  sortBy: 'createdAt',
  descending: true,
}
const templatesTablePagination = {
  rowsPerPage: 10,
  sortBy: 'createdAt',
  descending: true,
}

const apiTemplates = {
  get: async (service, endpoint, queryParams, headers, payload, credentials = {}) => {
    return await fetchData({
      endpoint,
      service,
      // queryParams: `${queryParams}&sort[0]=createdAt:desc`,
      headers,
      credentials,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        // apiPrompts.get()
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting templates list`,
        }
      })
  },
  update: async (service, endpoint, headers, payload) => {
    const body = JSON.stringify(payload)
    return await fetchData({
      method: 'PATCH',
      endpoint,
      service,
      body,
      headers,
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then((data) => {
        return data?.data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in updating template`,
        }
      })
  },
  delete: async (service, endpoint, headers) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      service,
      headers,
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        // TODO ADD DELETE LINKED PROMPTS?
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in deleting template`,
        }
      })
  },
  create: async (service, endpoint, headers, payload) => {
    const body = JSON.stringify(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      service,
      headers,
      body,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.inserted_id
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error creating template`,
        }
      })
  },
}
const apiPrompts = {
  get: async () => {
    return store.getters?.strapi?.templates?.selectedRow?.prompts
  },
}

export default {
  templates: {
    config: patchObject(templatesControls, controlsDefaultProps),
    pagination: templatesTablePagination,
    api: apiTemplates,
    keyField: {
      field: 'id',
      urlKey: 'id',
      routerPath: 'prompt-template-groups',
    },
  },
  prompts: {
    config: patchObject(promptsControls, controlsDefaultProps),
    pagination: promptsTablePagination,
    api: apiPrompts,
    keyField: {
      field: 'index',
      urlKey: 'index',
      routerPath: 'prompt-templates',
    },
  },
  // DONT' use "format" as the entity key
}

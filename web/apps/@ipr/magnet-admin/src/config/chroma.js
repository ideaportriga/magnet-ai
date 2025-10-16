import collectionsControls from '@/config/collections/collections'
import documentsControls from '@/config/collections/documents'
import ragToolsControls from '@/config/rag-tools/rag-tools'
import retrievalToolsControls from '@/config/retrieval-tools/retrieval-tools'
import aiAppsControls from '@/config/ai_apps/ai_apps'
import aiAppTabsControls from '@/config/ai_app_tabs/ai_app_tabs'
import promptsControls from '@/config/prompts/prompts'
import evaluationTestSetsControls from '@/config/evaluation_sets/evaluation_sets'
import evaluationJobsControls from '@/config/evaluation_jobs/evaluation_jobs'
import mcpServersControls from '@/config/mcp/servers'
import { traceMainControls } from '@/config/observability/traces'
import modelControls from '@/config/model/model'
import providersControls from '@/config/provider/provider'
import { fetchData } from '@shared'
import patchObject from '@shared/utils/patchObject'
import assistantToolsControls from '@/config/assistant-tools/assistant-tools'
import apiToolsControls from '@/config/api-tools/api-tools'
import apiKeysControls from '@/config/api-keys/table'
import agentsControls from '@/config/agents/agents'
import jobsControls from '@/config/jobs/jobs'
import apiServersControls from '@/config/api_servers/api_servers'

// Universal function to build query parameters from pagination and filter objects
const buildQueryParams = (pagination = {}, filter = {}) => {
  const params = new URLSearchParams()
  
  // Handle pagination parameters
  if (pagination.page) {
    params.append('currentPage', pagination.page.toString())
  }
  
  if (pagination.rowsPerPage) {
    params.append('pageSize', pagination.rowsPerPage.toString())
  }
  
  if (pagination.sortBy) {
    params.append('orderBy', pagination.sortBy)
    params.append('sortOrder', pagination.descending ? 'desc' : 'asc')
  }
  
  // Handle filter parameters
  Object.keys(filter).forEach(key => {
    const value = filter[key]
    
    // Skip null, undefined, or empty values
    if (value === null || value === undefined) return
    
    // Handle arrays
    if (Array.isArray(value)) {
      if (value.length > 0) {
        value.forEach(item => {
          params.append(key, item.toString())
        })
      }
    }
    // Handle strings and other primitive values
    else if (value !== '') {
      params.append(key, value.toString())
    }
  })
  
  return params.toString()
}

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
}
const collectionTablePagination = {
  rowsPerPage: 10,
  sortBy: 'created',
  descending: true,
}
const documentsTablePagination = {
  rowsPerPage: 10,
  sortBy: 'metadata.createdTime',
  descending: true,
}
const ragconfigTablePagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const retrievalConfigTablePagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const promptsTablePagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const evaluationJobsPagination = {
  rowsPerPage: 10,
  sortBy: 'job_start',
  descending: true,
}
const mcpServersPagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const modelPagination = {
  rowsPerPage: 10,
  sortBy: 'is_default',
  descending: true,
}

const assistantToolsPagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const aiAppTablePagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}
const apiToolsPagination = {
  rowsPerPage: 10,
  sortBy: 'modified_at',
  descending: true,
}

const agentsPagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}


const observabilityTracesPagination = {
  rowsPerPage: 15,
  sortBy: 'start_time',
  descending: true,
}
const jobsPagination = {
  rowsPerPage: 10,
  sortBy: 'created_at',
  descending: true,
}
const apiServersPagination = {
  rowsPerPage: 10,
  sortBy: 'last_updated',
  descending: true,
}

const apiCollections = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_collections`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_collections/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'collections' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_collections/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_collections`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_collections/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiRagTools = {
  get: async (service, endpoint) => {
    console.log('fetch rag_tools')
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_rag_tools`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting RAG Tools list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_rag_tools/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'rag_tools' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `rag_tools/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    console.log(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: 'sql_rag_tools',
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating RAG Tool`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_rag_tools/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting RAG Tool`,
        }
      })
  },
}
const apiRetrievalTools = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_retrieval_tools`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting Retrieval Tool list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)

    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_retrieval_tools/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'retrieval' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_retrieval_tools/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    console.log(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_retrieval_tools`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating RAG Tool`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_retrieval_tools/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting RAG Tool`,
        }
      })
  },
}
const apiModelConfig = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_ai_models`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting Models list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)

    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_ai_models/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'model' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_ai_models/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    console.log(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_ai_models`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating RAG Tool`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_ai_models/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting RAG Tool`,
        }
      })
  },
}
const modelProviders = {
  get: async (service, endpoint) => {
    console.log('fetch model providers')
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_providers`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting Model provider list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)

    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_providers/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'provider' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating model provider`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_providers/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing model provider ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    console.log(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_providers`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating model provider`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_providers/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting model provider`,
        }
      })
  },
}
const apiPromptTemplates = {
  get: async (service, endpoint) => {
    console.log('fetch rag_tools')
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_prompts`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting Prompt template list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_prompts/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'promptTemplates' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `prompt_templates/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_prompts`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating RAG Tool`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_prompts/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting RAG Tool`,
        }
      })
  },
}
const apiDocs = {
  get: async (service, endpoint, { name }) => {
    console.log('apiCollections')
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `${service}/${name}/documents`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting documents list`,
        }
      })
  },
  getPaginated: async (_, endpoint, payload) => {
    const { descending, page, rowsPerPage, sortBy } = payload.pagination
    console.log('apiDocs getPaginated', payload)
    const collection_id = payload?.collection_id ?? ''
    const { filter } = payload

    if (!collection_id) {
      throw {
        technicalError: 'Collection ID is required',
        text: `Collection ID is required`,
      }
    }

    const body = JSON.stringify({
      limit: rowsPerPage,
      sort: sortBy,
      order: descending ? -1 : 1,
      filters: filter,
      fields: [],
      offset: (page - 1) * rowsPerPage,
    })

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `collections/${collection_id}/documents/paginate/offset`,
      body,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        console.log('data', data)
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting prompt tracing`,
        }
      })
  },
  update: async () => {
    throw {
      technicalError: 'Update method doesnt exist',
      text: `Update method doesnt exist on document list`,
    }
  },
  refresh: async () => {
    throw {
      technicalError: 'Refresh method doesnt exist',
      text: `Refresh method doesnt exist on document list`,
    }
  },
  create: async () => {
    throw {
      technicalError: 'Create method doesnt exist',
      text: `Create method doesnt exist on document list`,
    }
  },
  delete: async () => {
    throw {
      technicalError: 'Delete method doesnt exist',
      text: `Delete method doesnt exist on document list`,
    }
  },
}
const apiAiApps = {
  get: async (service, endpoint) => {
    console.log('apiAiApps', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_ai_apps`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_ai_apps/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'ai_apps' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_ai_apps/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_ai_apps`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_ai_apps/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiAiAppTabs = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `${service}`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `${service}/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'ai_app_tabs' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `${service}/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `${service}`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `${service}/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiEvaluationSets = {
  get: async (service, endpoint) => {
    console.log('apiAiApps', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_evaluation_sets`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    console.log('update', id, data)
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_evaluation_sets/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'evaluation_sets' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_evaluation_sets/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },

  create: async (service, endpoint, payload) => {
    const formData = new FormData()

    if (payload.file) {
      formData.append('file', payload.file)
    }

    delete payload.file

    const jsonPayload = JSON.stringify(payload)
    formData.append('json', jsonPayload)

    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_evaluation_sets/file`,
      body: formData,
      headers: {},
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_evaluation_sets/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiEvaluationJobs = {
  get: async (service, endpoint) => {
    console.log('apiAiApps', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `evaluations/list`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `evaluations/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'evaluation_jobs' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `evaluations/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `evaluation`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `evaluations/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiEvaluation = {
  get: async (service, endpoint) => {
    console.log('apiAiApps', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `evaluations/list`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `evaluations/jobs/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'evaluation_jobs' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `evaluations/jobs/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `evaluation/jobs`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `evaluation/jobs/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiAssistantTools = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `assistant_tools`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting Assistant tool list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `assistant_tools/${id}`,
      body: data,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'assistant_tools' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `assistant_tools/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    console.log(payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `assistant_tools`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating RAG Tool`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `assistant_tools/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting RAG Tool`,
        }
      })
  },
}
const apiObservabilityTraces = {
  getPaginated: async (_, endpoint, payload) => {
    const { pagination = {}, filter = {} } = payload
    
    // Build query parameters using universal function
    const queryString = buildQueryParams(pagination, filter)
    const url = queryString ? `traces?${queryString}` : 'traces'

    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: url,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return {
          items: data.items || [],
          limit: data.limit || 0,
          offset: data.offset || 0,
          total: data.total || 0,
        }
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting prompt tracing`,
        }
      })
  },
  get: async (_, endpoint, payload = {}) => {
    const { filter = {} } = payload
    
    // Build query parameters using universal function
    const queryString = buildQueryParams({ currentPage: '1', pageSize: '10' }, filter)
    const url = queryString ? `traces?${queryString}` : 'traces'

    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: url,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items || []
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting prompt tracing`,
        }
      })
  },
  getDetail: async (_, endpoint, payload) => {

    console.log('payload !', payload)
    const params = new URLSearchParams({
      ids: payload?.id,
    })

    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: `traces?${params.toString()}`,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        throw response
      })
      .then((data) => {
        return data?.items?.[0] || {}
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting prompt tracing`,
          status: res.status,
        }
      })
  },
  refresh: async (_, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `traces/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing prompt tracing ${id}`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `traces/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting trace`,
        }
      })
  },
}
const apiApiTools = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      service: `sql_api_tools`,
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(async (response) => {
        if (response.ok) {
          const res = await response.json()
          console.log('apiApiTools', res)
          return res.items.map((item) => ({
            ...item,
          }))
        }
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_api_tools/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'api_tools' })
        return true
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_api_tools`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_api_tools/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    }).then((response) => {
      if (response.ok) return id
      if (response.error) throw response
    })
  },
}
const apiApiToolProviders = {
  get: async (service, endpoint) => {
    console.log('apiApiToolProviders', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `api_tool_providers`,
    })
      .then(async (response) => {
        if (response.ok) {
          const res = await response.json()
          return res.system_names.map((system_name) => ({
            systemName: system_name,
          }))
        }
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting API Tool Provider list`,
        }
      })
  },
}
const apiAgents = {
  get: async (service, endpoint) => {
    console.log('apiAiApps', service, endpoint)
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_agents`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting collections list`,
        }
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_agents/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'agents' })
        return true
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error updating collection`,
        }
      })
  },
  refresh: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_agents/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing collection ${id}`,
        }
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_agents`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((collection) => {
        return collection
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error creating collection`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_agents/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting collection`,
        }
      })
  },
}
const apiJobs = {
  getPaginated: async (_, endpoint, payload) => {
    const { pagination = {}, filter = {} } = payload
    
    console.log('apiJobs getPaginated', pagination, filter)
    // Build query parameters using universal function
    const queryString = buildQueryParams(pagination, filter)
    const url = queryString ? `sql_jobs?${queryString}` : 'sql_jobs'

    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: url,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        console.log('data', data)
        return data
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting job data`,
        }
      })
  },
  get: async (_, endpoint, payload = {}) => {
    const { filter = {} } = payload
    
    // Build query parameters using universal function (no pagination for simple get)
    const queryString = buildQueryParams({}, filter)
    const url = queryString ? `sql_jobs?${queryString}` : 'sql_jobs'

    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: url,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items
      })
      .catch((res) => {
        throw {
          technicalError: res?.error,
          text: `Error in getting job data`,
        }
      })
  },
  getDetail: async (_, endpoint, payload) => {
    return await fetchData({
      method: 'GET',
      endpoint,
      credentials: 'include',
      service: `sql_jobs/${payload?.id}`,

      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        throw response
      })
      .then((data) => {
        return data
      })
      .catch((res) => {
        const error = {
          technicalError: res?.error,
          text: `Error in getting prompt tracing`,
          status: res.status, // Keep the HTTP status for checking 404
          originalResponse: res,
        }
        throw error
      })
  },
  refresh: async (_, endpoint, { id }) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_jobs/${id}/sync`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then(() => true)
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error in refreshing prompt tracing ${id}`,
        }
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_jobs/${id}`,
      body: '',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting trace`,
        }
      })
  },
}
const apiMcpServers = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_mcp_servers`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items || []
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_mcp_servers`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_mcp_servers/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'mcp_servers' })
        return true
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_mcp_servers/${id}`,
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'mcp_servers' })
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting mcp server`,
        }
      })
  },
}
const apiApiKeys = {
  get: async (_, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `api_keys`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
  },
  create: async (service, endpoint, payload) => {
    console.log('payload', payload)
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `api_keys`,
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `api_keys/${id}`,
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting api key`,
        }
      })
  },
}
const apiApiServers = {
  get: async (service, endpoint) => {
    return await fetchData({
      endpoint,
      credentials: 'include',
      service: `sql_api_servers`,
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data?.items || []
      })
  },
  create: async (service, endpoint, payload) => {
    return await fetchData({
      method: 'POST',
      endpoint,
      credentials: 'include',
      service: `sql_api_servers`,
      body: payload,
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return response.json()
        if (response.error) throw response
      })
      .then((data) => {
        return data
      })
  },
  update: async (service, endpoint, { id, data }, { dispatch }) => {
    return await fetchData({
      method: 'PATCH',
      endpoint,
      credentials: 'include',
      service: `sql_api_servers/${id}`,
      body: JSON.stringify(data),
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((response) => {
        if (response.ok) return true
        if (response.error) throw response
      })
      .then(() => {
        dispatch('get', { entity: 'api_servers' })
        return true
      })
  },
  delete: async (service, endpoint, { id }) => {
    return await fetchData({
      method: 'DELETE',
      endpoint,
      credentials: 'include',
      service: `sql_api_servers/${id}`,
    })
      .then((response) => {
        if (response.ok) return response
        if (response.error) throw response
      })
      .then(() => {
        return id
      })
      .catch((response) => {
        throw {
          technicalError: response?.error,
          text: `Error deleting api server`,
        }
      })
  },
}

//entities
export default {
  collections: {
    config: patchObject(collectionsControls, controlsDefaultProps),
    pagination: collectionTablePagination,
    api: apiCollections,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  documents: {
    config: patchObject(documentsControls, controlsDefaultProps),
    pagination: documentsTablePagination,
    api: apiDocs,
    keyField: {
      field: 'id',
      urlKey: 'chunk',
    },
  },
  rag_tools: {
    config: patchObject(ragToolsControls, { controlsDefaultProps }),
    pagination: ragconfigTablePagination,
    api: apiRagTools,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  retrieval: {
    config: patchObject(retrievalToolsControls, { controlsDefaultProps }),
    pagination: retrievalConfigTablePagination,
    api: apiRetrievalTools,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  promptTemplates: {
    config: patchObject(promptsControls, { controlsDefaultProps }),
    pagination: promptsTablePagination,
    api: apiPromptTemplates,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  ai_apps: {
    config: patchObject(aiAppsControls, { controlsDefaultProps }),
    pagination: aiAppTablePagination,
    api: apiAiApps,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  ai_app_tabs: {
    config: patchObject(aiAppTabsControls, { controlsDefaultProps }),
    pagination: promptsTablePagination,
    api: apiAiAppTabs,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  evaluation_sets: {
    config: patchObject(evaluationTestSetsControls, { controlsDefaultProps }),
    pagination: promptsTablePagination,
    api: apiEvaluationSets,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  evaluation_jobs: {
    config: patchObject(evaluationJobsControls, { controlsDefaultProps }),
    pagination: evaluationJobsPagination,
    api: apiEvaluationJobs,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  evaluation: {
    config: patchObject(evaluationJobsControls, { controlsDefaultProps }),
    pagination: evaluationJobsPagination,
    api: apiEvaluation,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  observability_traces: {
    config: patchObject(traceMainControls, { controlsDefaultProps }),
    pagination: observabilityTracesPagination,
    api: apiObservabilityTraces,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  model: {
    config: patchObject(modelControls, { controlsDefaultProps }),
    pagination: modelPagination,
    api: apiModelConfig,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  provider: {
    config: patchObject(providersControls, { controlsDefaultProps }),
    pagination: evaluationJobsPagination,
    api: modelProviders,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  assistant_tools: {
    config: patchObject(assistantToolsControls, { ...controlsDefaultProps }),
    pagination: assistantToolsPagination,
    api: apiAssistantTools,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  api_tools: {
    config: patchObject(apiToolsControls, { ...controlsDefaultProps }),
    pagination: apiToolsPagination,
    api: apiApiTools,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  api_tool_providers: {
    config: { ...controlsDefaultProps },
    api: apiApiToolProviders,
    keyField: {
      field: 'id',
    },
  },
  agents: {
    config: patchObject(agentsControls, { ...controlsDefaultProps }),
    pagination: agentsPagination,
    api: apiAgents,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  jobs: {
    config: patchObject(jobsControls, { ...controlsDefaultProps }),
    pagination: jobsPagination,
    api: apiJobs,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },

  mcp_servers: {
    config: patchObject(mcpServersControls, { ...controlsDefaultProps }),
    pagination: mcpServersPagination,
    api: apiMcpServers,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  api_keys: {
    config: patchObject(apiKeysControls, { ...controlsDefaultProps }),
    pagination: {
      sortBy: 'created_at',
      descending: true,
      page: 1,
      rowsPerPage: 10,
    },
    api: apiApiKeys,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  api_servers: {
    config: patchObject(apiServersControls, { ...controlsDefaultProps }),
    pagination: apiServersPagination,
    api: apiApiServers,
    keyField: {
      field: 'id',
      urlKey: 'id',
    },
  },
  // DONT' use "format" as the entity key
}

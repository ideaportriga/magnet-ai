import { fetchData } from '@shared'
import _ from 'lodash'

// state
const state = () => ({})

// getters
const getters = {}

// mutations
const mutations = {}

// ----- helpers -----

function schedulerFetch(getters, { method = 'GET', path = '', body = null }) {
  const endpoint = getters.config?.scheduler?.endpoint
  const service = getters.config?.scheduler?.service
  const credentials = getters.config?.scheduler?.credentials

  const opts: any = { method, endpoint, service: service + path, credentials }
  if (body) {
    opts.body = JSON.stringify(body)
    opts.headers = { 'Content-Type': 'application/json' }
  }
  return fetchData(opts)
}

async function jsonOrThrow(response) {
  if (response?.error) throw new Error(response.error)
  return await response.json()
}

/** Build ?queue=xxx query-string fragment */
function queueQP(queue?: string | null): string {
  return queue ? `queue=${encodeURIComponent(queue)}` : ''
}

/** Append extra query-string fragment to a path */
function appendQP(path: string, qp: string): string {
  if (!qp) return path
  return path.includes('?') ? `${path}&${qp}` : `${path}?${qp}`
}

// actions
const actions = {
  // ── Overview ────────────────────────────────────────────────
  async getDashboardOverview({ getters }, { queue = null } = {}) {
    const r = await schedulerFetch(getters, { path: appendQP('/overview', queueQP(queue)) })
    return jsonOrThrow(r)
  },

  // ── Jobs (paginated, filterable) ────────────────────────────
  async getDashboardJobs({ getters }, { queue = null, state = 'all', page = 1, size = 50 } = {}) {
    const r = await schedulerFetch(getters, {
      path: appendQP(`/jobs?state=${state}&page=${page}&size=${size}`, queueQP(queue)),
    })
    return jsonOrThrow(r)
  },

  // ── Repeatables ─────────────────────────────────────────────
  async getDashboardRepeatables({ getters }, { queue = null } = {}) {
    const r = await schedulerFetch(getters, { path: appendQP('/repeatables', queueQP(queue)) })
    return jsonOrThrow(r)
  },

  // ── Metrics ─────────────────────────────────────────────────
  async getDashboardMetrics({ getters }, { queue = null } = {}) {
    const r = await schedulerFetch(getters, { path: appendQP('/metrics', queueQP(queue)) })
    return jsonOrThrow(r)
  },

  // ── DLQ (failed jobs) ──────────────────────────────────────
  async getDashboardDLQ({ getters }, { queue = null, page = 1, size = 50 } = {}) {
    const r = await schedulerFetch(getters, {
      path: appendQP(`/dlq?page=${page}&size=${size}`, queueQP(queue)),
    })
    return jsonOrThrow(r)
  },

  // ── Queue status (legacy/full) ─────────────────────────────
  async getQueueStatus({ getters }, { queue = null } = {}) {
    const r = await schedulerFetch(getters, { path: appendQP('/queue-status', queueQP(queue)) })
    return jsonOrThrow(r)
  },

  // ── Job actions ─────────────────────────────────────────────
  async retryJob({ getters }, { jobId, queue = 'default' }) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/jobs/${jobId}/retry?queue=${encodeURIComponent(queue)}`,
    })
    return jsonOrThrow(r)
  },

  async removeJob({ getters }, { jobId, queue = 'default' }) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/jobs/${jobId}/remove?queue=${encodeURIComponent(queue)}`,
    })
    return jsonOrThrow(r)
  },

  async cancelQueueJob({ getters }, { jobId, queue = 'default' }) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/jobs/${jobId}/cancel?queue=${encodeURIComponent(queue)}`,
    })
    return jsonOrThrow(r)
  },

  // ── Queue control ───────────────────────────────────────────
  async pauseQueue({ getters }, queue = 'default') {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/queue/pause?queue=${encodeURIComponent(queue)}`,
    })
    return jsonOrThrow(r)
  },

  async resumeQueue({ getters }, queue = 'default') {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/queue/resume?queue=${encodeURIComponent(queue)}`,
    })
    return jsonOrThrow(r)
  },

  async cleanQueue({ getters }, { queue = 'default', state = 'completed', older_than_hours = 24 } = {}) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/queue/clean?queue=${encodeURIComponent(queue)}&state=${state}&older_than_hours=${older_than_hours}`,
    })
    return jsonOrThrow(r)
  },

  // ── Create / cancel job ─────────────────────────────────────
  async createAndRunJobScheduler({ getters, commit }, payload) {
    commit('set', { loading: true })
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: '/create-job',
      body: payload,
    })
    commit('set', { answersLoading: false })
    if (r?.error) {
      commit('set', {
        errorMessage: { technicalError: r.error, text: 'Error calling create and run job scheduler service' },
      })
    } else {
      return await r.json()
    }
  },

  async cancelJobScheduler({ getters, commit }, jobId) {
    commit('set', { loading: true })
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: '/cancel-job',
      body: { job_id: jobId },
    })
    commit('set', { loading: false })
    if (r?.error) {
      commit('set', {
        errorMessage: { technicalError: r.error, text: 'Error canceling job' },
      })
    } else {
      return await r.json()
    }
  },
}

export default {
  namespaced: true,
  state: state(),
  getters,
  mutations,
  actions,
}

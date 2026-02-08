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

// actions
const actions = {
  // ── Legacy queue-status (full payload) ──────────────────────────
  async getQueueStatus({ getters }) {
    const r = await schedulerFetch(getters, { path: '/queue-status' })
    return jsonOrThrow(r)
  },

  // ── Dashboard: overview ─────────────────────────────────────────
  async getDashboardOverview({ getters }) {
    const r = await schedulerFetch(getters, { path: '/dashboard/overview' })
    return jsonOrThrow(r)
  },

  // ── Dashboard: jobs (paginated, filterable) ─────────────────────
  async getDashboardJobs({ getters }, { state = 'all', page = 1, size = 50 } = {}) {
    const r = await schedulerFetch(getters, {
      path: `/dashboard/jobs?state=${state}&page=${page}&size=${size}`,
    })
    return jsonOrThrow(r)
  },

  // ── Dashboard: repeatables ──────────────────────────────────────
  async getDashboardRepeatables({ getters }) {
    const r = await schedulerFetch(getters, { path: '/dashboard/repeatables' })
    return jsonOrThrow(r)
  },

  // ── Dashboard: workers ──────────────────────────────────────────
  async getDashboardWorkers({ getters }) {
    const r = await schedulerFetch(getters, { path: '/dashboard/workers' })
    return jsonOrThrow(r)
  },

  // ── Dashboard: metrics ──────────────────────────────────────────
  async getDashboardMetrics({ getters }) {
    const r = await schedulerFetch(getters, { path: '/dashboard/metrics' })
    return jsonOrThrow(r)
  },

  // ── Dashboard: DLQ (failed jobs) ───────────────────────────────
  async getDashboardDLQ({ getters }, { page = 1, size = 50 } = {}) {
    const r = await schedulerFetch(getters, {
      path: `/dashboard/dlq?page=${page}&size=${size}`,
    })
    return jsonOrThrow(r)
  },

  // ── Job actions ─────────────────────────────────────────────────
  async retryJob({ getters }, jobId) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/dashboard/jobs/${jobId}/retry`,
    })
    return jsonOrThrow(r)
  },

  async removeJob({ getters }, jobId) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/dashboard/jobs/${jobId}/remove`,
    })
    return jsonOrThrow(r)
  },

  async cancelQueueJob({ getters }, jobId) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/dashboard/jobs/${jobId}/cancel`,
    })
    return jsonOrThrow(r)
  },

  // ── Queue control ───────────────────────────────────────────────
  async pauseQueue({ getters }) {
    const r = await schedulerFetch(getters, { method: 'POST', path: '/dashboard/queue/pause' })
    return jsonOrThrow(r)
  },

  async resumeQueue({ getters }) {
    const r = await schedulerFetch(getters, { method: 'POST', path: '/dashboard/queue/resume' })
    return jsonOrThrow(r)
  },

  async cleanQueue({ getters }, { state = 'completed', older_than_hours = 24 } = {}) {
    const r = await schedulerFetch(getters, {
      method: 'POST',
      path: `/dashboard/queue/clean?state=${state}&older_than_hours=${older_than_hours}`,
    })
    return jsonOrThrow(r)
  },

  // ── Create / cancel job ─────────────────────────────────────────
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
